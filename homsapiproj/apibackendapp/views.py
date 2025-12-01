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
        # Expecting {'is_available': boolean}
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
        
        room = data.get('Rid') # This comes from source='Rid' in serializer but validated_data uses model field names usually? 
        # Wait, serializer has RoomId=RoomSerializer(source='Rid')... 
        # But for writing, we need to check how the serializer is defined.
        # The serializer has fields='__all__'. 
        # Let's check validated_data.
        
        # Actually, let's look at the serializer again.
        # If I send 'Rid' (primary key) in request, DRF handles it.
        # But wait, BookingSerializer has:
        # RoomId=RoomSerializer(source='Rid',read_only=True)
        # This means 'RoomId' is read-only. How do we pass the room ID?
        # We need a writeable field for Room.
        # The model has 'Rid'. The serializer should probably have 'Rid' as a writeable field or just use default ModelSerializer behavior for 'Rid' if it wasn't shadowed.
        # In the previous step, I fixed serializers.py but I didn't explicitly add a writeable field for Rid if I shadowed it.
        # Let's check serializers.py content again.
        # BookingSerializer:
        # Room_details = RoomSerializer(source='Rid', read_only=True)
        # fields = '__all__'
        # This is fine. 'Rid' (the FK field) will be available as a writeable field by default because 'Room_details' has a different name.
        
        room = data.get('Rid')
        check_in = data.get('CheckInDate')
        check_out = data.get('CheckOutDate')
        
        if not room:
             raise ValidationError("Room is required")

        # 1. Validate dates
        if check_in >= check_out:
            raise ValidationError("Check-out date must be after check-in date")
        
        # 2. Check room availability (is_available flag)
        if not room.is_available:
             raise ValidationError("Room is not available")

        # 3. Check for overlapping bookings
        # Overlap if: (StartA <= EndB) and (EndA >= StartB)
        # Here: (CheckIn < ExistingCheckOut) and (CheckOut > ExistingCheckIn)
        overlapping_bookings = Booking.objects.filter(
            Rid=room,
            status__in=['Confirmed', 'Pending'], # Assuming these statuses block the room
            CheckInDate__lt=check_out,
            CheckOutDate__gt=check_in
        )
        
        if overlapping_bookings.exists():
            raise ValidationError("Room is already booked for these dates")

        # 4. Calculate Total Price
        nights = (check_out - check_in).days
        total_amount = room.RoomPrice * nights
        
        # 5. Assign Guest Profile
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
        # Update booking status to Confirmed
        booking = serializer.validated_data.get('Booking')
        if booking:
            booking.status = 'Confirmed'
            booking.save()
        serializer.save(status='Success') # Assuming payment is successful immediately

class RegisterView(APIView):
    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Create GuestProfile
            GuestProfile.objects.create(
                User=user,
                phoneno=request.data.get("phoneno", "N/A"),
                Address=request.data.get("address", "N/A")
            )
            
            return Response({"message": "User registered successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
