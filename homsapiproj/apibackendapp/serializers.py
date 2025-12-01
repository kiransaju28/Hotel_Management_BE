from rest_framework import serializers
from .models import Room, GuestProfile, Booking, Payment
from django.contrib.auth.models import User, Group
from django.contrib.auth.hashers import make_password

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

class PaymentSerializer(serializers.ModelSerializer):
    Booking_details = BookingSerializer(source='Booking', read_only=True)
    
    class Meta:
        model = Payment
        fields = '__all__'

# -------------------------------
# Signup Serializer
# -------------------------------

class SignupSerializer(serializers.ModelSerializer):
    group_name = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ["username", "password", "group_name"]

    def create(self, validated_data):
        group_name = validated_data.pop("group_name", None)
        validated_data["password"] = make_password(validated_data.get("password"))
        user = super(SignupSerializer, self).create(validated_data)

        if group_name:
            group, created = Group.objects.get_or_create(name=group_name)
            user.groups.add(group)

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