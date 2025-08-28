import uuid
import os
import requests
from django.core.mail import send_mail
from django.conf import settings
from django.http import JsonResponse
from rest_framework import viewsets
from rest_framework.generics import ListAPIView
from rest_framework.decorators import api_view
from celery import shared_task
from .serializers import ListingSerializer, BookingSerializer, PaymentSerializer, UserSerializer, \
    LocationSerializer
from .models import User, Listing, Booking, Payment, PaymentStatus, Location

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer

class ListingViewSet(viewsets.ModelViewSet):
    queryset = Listing.objects.all()
    serializer_class = ListingSerializer

class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer

    def perform_create(self, serializer):
        guest = self.request.user
        listing = serializer.validated_data.get('listing')
        if guest.is_anonymous:
            guest = serializer.validated_data.get('guest')
        booking = serializer.save(guest=guest, listing=listing)
        try:
            create_chapa_payment(booking)
        except requests.RequestException as e:
            print(f"[Chapa Payment Error]({e})")
        return booking

class PaymentListView(ListAPIView):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer

def create_chapa_payment(booking):
    secret_key = os.environ.get("CHAPA_SECRET_KEY")
    chapa_url = os.environ.get("CHAPA_BASE_URL")
    if not secret_key or not chapa_url:
        return {
            "status": "error",
            "data": "Missing CHAPA_SECRET_KEY or CHAPA_BASE_URL environment variables."
        }

    tx_ref = str(uuid.uuid4())
    app_url = os.environ.get("APP_URL")
    port = os.environ.get("APP_PORT")
    return_url = f"{app_url}:{port}/api/payment/verify/{tx_ref}/"

    chapa_payload = {
        "amount": booking.total_price,
        "email": booking.guest.email,
        "first_name": booking.guest.first_name,
        "last_name": booking.guest.last_name,
        "phone_number": getattr(booking.guest, "phone_number", None) or "",
        "tx_ref": tx_ref,
        "return_url": return_url,
        "customization": {
            "title": f"payment- {booking.listing.title[:5]}",
            "description": f"Staying from {booking.start_date} to {booking.end_date}"
        }
    }

    headers = {
        "Authorization": f"Bearer {secret_key}",
        "Content-Type": "application/json",
    }

    response = requests.post(f"{chapa_url}/transaction/initialize", json=chapa_payload, headers=headers)
    chapa_data = response.json()

    if chapa_data.get("status") == "success":
        booking.payment_url = chapa_data["data"]["checkout_url"]
        booking.save()
        Payment.objects.create(
            booking=booking,
            transaction_id=tx_ref,
            amount=booking.total_price,
        )
    return chapa_data



@shared_task
def send_payment_confirmation_email(user_email, booking_id):
    subject = "Booking Payment Confirmation"
    message = f"Your payment for booking {booking_id} was successful. Thank you for booking with us!"
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user_email])


@api_view(["GET"])
def verify_payment(request, tx_ref):
    secret_key = os.environ.get("CHAPA_SECRET_KEY")
    chapa_url = os.environ.get("CHAPA_BASE_URL")
    headers = {
        "Authorization": f"Bearer {secret_key}",
    }
    try:
        response = requests.get(f"{chapa_url}/transaction/verify/{tx_ref}", headers=headers)
        chapa_data = response.json()
        try:
            payment = Payment.objects.get(transaction_id=tx_ref)
        except Payment.DoesNotExist:
            return JsonResponse({"status": "error", "data": "Payment not found"})

        if chapa_data.get("status") == "success" and chapa_data.get("data").get("status") == "success":
            payment.payment_status = PaymentStatus.SUCCESS
            payment.save()
            # send email using celery
            send_payment_confirmation_email.delay(payment.booking.guest.email, payment.booking.id)
            return JsonResponse({"status": "success", "data": chapa_data})
        else:
            payment.payment_status = PaymentStatus.FAILED
            payment.save()
            return JsonResponse({"status": "error", "data": chapa_data})
    except requests.RequestException as e:
        return JsonResponse({"status": "error", "data": str(e)})