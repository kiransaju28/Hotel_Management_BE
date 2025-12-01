from rest_framework import serializers
from .models import Room, GuestProfile, Booking, Payment
from django.contrib.auth.models import User, Group
from django.contrib.auth.hashers import make_password
from .validations import (
    validate_dates, validate_room_availability, 
    validate_payment_amount, validate_email, 
    validate_phone, validate_password
)

class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = '__all__'

class GuestProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = GuestProfile
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email')

class BookingSerializer(serializers.ModelSerializer):
    # Read-only nested serializers for display
    Room_details = RoomSerializer(source='Rid', read_only=True)
    Guest_details = GuestProfileSerializer(source='Gid', read_only=True)
    
    class Meta:
        model = Booking
        fields = '__all__'
        extra_kwargs = {
            'Gid': {'required': False}, # Handled in view
            'TotalAmount': {'required': False}, # Handled in view/serializer
            'status': {'required': False}
        }

    def validate(self, data):
        # We need 'Rid' (Room) and dates to validate availability
        # If instance exists (update), use instance values if not in data
        
        # Note: 'Rid' might be in data as a PK if passed directly, or we might need to fetch it.
        # Since we use ModelSerializer, 'Rid' field expects a Room instance.
        
        room = data.get('Rid')
        check_in = data.get('CheckInDate')
        check_out = data.get('CheckOutDate')
        
        # If partial update, we might not have all fields
        if self.instance:
            room = room or self.instance.Rid
            check_in = check_in or self.instance.CheckInDate
            check_out = check_out or self.instance.CheckOutDate

        if room and check_in and check_out:
            validate_dates(check_in, check_out)
            validate_room_availability(room, check_in, check_out)
        
        return data

class PaymentSerializer(serializers.ModelSerializer):
    Booking_details = BookingSerializer(source='Booking', read_only=True)
    
    class Meta:
        model = Payment
        fields = '__all__'
        extra_kwargs = {
            'status': {'required': False}
        }

    def validate(self, data):
        booking = data.get('Booking')
        amount = data.get('Amount')
        
        if self.instance:
            booking = booking or self.instance.Booking
            amount = amount or self.instance.Amount
            
        if booking and amount:
            validate_payment_amount(booking, amount)
            
        return data

# -------------------------------
# Signup Serializer
# -------------------------------

class SignupSerializer(serializers.ModelSerializer):
    group_name = serializers.CharField(write_only=True, required=False)
    email = serializers.EmailField(required=True)
    phoneno = serializers.CharField(write_only=True, required=False) # Passed to GuestProfile
    address = serializers.CharField(write_only=True, required=False) # Passed to GuestProfile

    class Meta:
        model = User
        fields = ["username", "password", "email", "group_name", "phoneno", "address"]

    def validate_email(self, value):
        validate_email(value)
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already registered.")
        return value

    def validate_password(self, value):
        validate_password(value)
        return value
        
    def validate_phoneno(self, value):
        if value:
            validate_phone(value)
        return value

    def create(self, validated_data):
        group_name = validated_data.pop("group_name", None)
        phoneno = validated_data.pop("phoneno", "N/A")
        address = validated_data.pop("address", "N/A")
        
        validated_data["password"] = make_password(validated_data.get("password"))
        user = super(SignupSerializer, self).create(validated_data)

        if group_name:
            group, created = Group.objects.get_or_create(name=group_name)
            user.groups.add(group)
            
        # Create GuestProfile here or in View? 
        # View was doing it, but Serializer create is cleaner if we have the data.
        # Let's do it here since we have the data now.
        GuestProfile.objects.create(
            User=user,
            phoneno=phoneno,
            Address=address
        )

        return user

# -------------------------------
# Login Serializer
# -------------------------------

class LoginSerializer(serializers.ModelSerializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'password']