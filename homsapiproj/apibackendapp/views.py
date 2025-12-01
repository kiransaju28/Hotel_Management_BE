from django.shortcuts import render
from rest_framework import viewsets, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from django.db.models import Q
from .models import Room, GuestProfile, Booking, Payment
from .serializers import (
    RoomSerializer, GuestProfileSerializer, BookingSerializer, 
    PaymentSerializer, SignupSerializer
)
from .permissions import IsStaffOrReadOnly, IsBookingOwnerOrStaff, IsPaymentOwnerOrStaff
from datetime import datetime

# Create your views here.

class RoomViewSet(viewsets.ModelViewSet):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    permission_classes = [IsStaffOrReadOnly]

    @action(detail=True, methods=['patch'])
    def availability(self, request, pk=None):
        room = self.get_object()
        is_available = request.data.get('is_available')
        if is_available is None:
            return Response({"error": "is_available field is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        room.is_available = is_available
        room.save()
        return Response(RoomSerializer(room).data)

class GuestProfileViewSet(viewsets.ModelViewSet):
    queryset = GuestProfile.objects.all()
    serializer_class = GuestProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return GuestProfile.objects.all()
        return GuestProfile.objects.filter(User=user)

class BookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingSerializer
    permission_classes = [IsBookingOwnerOrStaff]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Booking.objects.all()
        if user.is_authenticated:
            return Booking.objects.filter(Gid__User=user)
        return Booking.objects.none()

    @action(detail=False, methods=['get'])
    def my(self, request):
        bookings = self.get_queryset()
        serializer = self.get_serializer(bookings, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['put'])
    def cancel(self, request, pk=None):
        booking = self.get_object()
        if booking.status == 'Cancelled':
             return Response({"message": "Booking is already cancelled"}, status=status.HTTP_400_BAD_REQUEST)
        
        booking.status = 'Cancelled'
        booking.save()
        return Response({"message": "Booking cancelled successfully"})

    def perform_create(self, serializer):
        user = self.request.user
        data = serializer.validated_data
        
        # Validation is now handled in Serializer.validate()
        
        # We still need to calculate TotalAmount and assign Gid
        # Serializer.validate() has access to 'Rid' (Room) and dates.
        
        room = data.get('Rid')
        check_in = data.get('CheckInDate')
        check_out = data.get('CheckOutDate')
        
        # Calculate Total Price
        nights = (check_out - check_in).days
        total_amount = room.RoomPrice * nights
        
        # Assign Guest Profile
        try:
            guest_profile = GuestProfile.objects.get(User=user)
        except GuestProfile.DoesNotExist:
             # Auto-create if missing (fallback)
             guest_profile = GuestProfile.objects.create(User=user, phoneno="N/A", Address="N/A")

        serializer.save(Gid=guest_profile, TotalAmount=total_amount, status='Pending')


class PaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [IsPaymentOwnerOrStaff]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Payment.objects.all()
        if user.is_authenticated:
            return Payment.objects.filter(Booking__Gid__User=user)
        return Payment.objects.none()

    @action(detail=False, methods=['get'])
    def my(self, request):
        payments = self.get_queryset()
        serializer = self.get_serializer(payments, many=True)
        return Response(serializer.data)

    def perform_create(self, serializer):
        # Validation is handled in Serializer.validate()
        
        # Update booking status to Confirmed
        booking = serializer.validated_data.get('Booking')
        if booking:
            booking.status = 'Confirmed'
            booking.save()
        serializer.save(status='Success')

class RegisterView(APIView):
    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            # Serializer now handles User creation and GuestProfile creation
            user = serializer.save()
            return Response({"message": "User registered successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
