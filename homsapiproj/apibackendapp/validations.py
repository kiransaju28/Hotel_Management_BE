import re
from datetime import date
from rest_framework.exceptions import ValidationError
from .models import Booking

def validate_dates(check_in, check_out):
    if check_in >= check_out:
        raise ValidationError("Check-out date must be after check-in date.")
    
    if check_in < date.today():
        raise ValidationError("Cannot book dates in the past.")

def validate_room_availability(room, check_in, check_out):
    if not room.is_available:
        raise ValidationError("Room is not marked as available.")
    
    # Check for overlapping bookings
    overlapping_bookings = Booking.objects.filter(
        Rid=room,
        status__in=['Confirmed', 'Pending'],
        CheckInDate__lt=check_out,
        CheckOutDate__gt=check_in
    )
    
    if overlapping_bookings.exists():
        raise ValidationError("Room is already booked for these dates.")

def validate_payment_amount(booking, amount):
    if amount != booking.TotalAmount:
        raise ValidationError(f"Payment amount ({amount}) does not match booking total ({booking.TotalAmount}).")

def validate_email(email):
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    if not re.match(email_regex, email):
        raise ValidationError("Invalid email format.")

def validate_phone(phone):
    phone_regex = r'^\+?1?\d{9,15}$'
    if not re.match(phone_regex, phone):
        raise ValidationError("Invalid phone number format. Must be 9-15 digits.")

def validate_password(password):
    if len(password) < 8:
        raise ValidationError("Password must be at least 8 characters long.")
    # Add more complexity checks if needed (e.g., uppercase, numbers)
