from django.db import models
from django.contrib.auth.models import AbstractUser
from uuid import uuid4

class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    phone_number = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return self.username


class Location(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    country = models.CharField(max_length=200)
    state = models.CharField(max_length=200)
    city = models.CharField(max_length=200)

    def __str__(self):
        return f"{self.country}, {self.state}, {self.city}"

class Listing(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    title = models.CharField(max_length=200)
    price_per_night = models.IntegerField()
    description = models.TextField(blank=True)
    image_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Foreign keys
    host = models.ForeignKey(User, on_delete=models.CASCADE)
    location = models.ForeignKey(Location, on_delete=models.PROTECT)

    def __str__(self):
        return f"{self.title} - {self.location}"

class BookingStatus(models.TextChoices):
    ACTIVE = 'active'
    CANCELLED = 'cancelled'
    PENDING = 'pending'

class Booking(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    start_date = models.DateField()
    end_date = models.DateField()
    total_price = models.IntegerField()
    status = models.CharField(max_length=50, choices=BookingStatus.choices, default=BookingStatus.PENDING)
    payment_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Foreign keys
    guest = models.ForeignKey(User, on_delete=models.CASCADE)
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.listing} - {self.guest}, {self.status}, {self.total_price}"

class Review(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    rating = models.IntegerField()
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Foreign key
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE)
    guest = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.listing} - {self.guest} - {self.rating}"

class PaymentStatus(models.TextChoices):
    PENDING = 'pending'
    SUCCESS = 'success'
    FAILED = 'failed'

class Payment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    payment_status = models.CharField(max_length=200, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    amount = models.IntegerField()
    transaction_id = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Foreign key
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.booking} - {self.payment_status} - {self.amount}"