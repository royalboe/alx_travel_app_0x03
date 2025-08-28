from rest_framework import serializers
from .models import Listing, Booking

class ListingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Listing
        fields = ['id', 'title', 'price_per_night', 'description', 'image_url', 'location', 'host', 'created_at', 'updated_at']
        read_only_fields = ['id', 'location', 'host', 'created_at', 'updated_at']

class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ['id', 'start_date', 'end_date', 'total_price', 'status', 'guest', 'listing', 'created_at', 'updated_at']
        read_only_fields = ['id', 'guest', 'listing','created_at', 'updated_at']