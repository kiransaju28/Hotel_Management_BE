from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Room(models.Model):
    Rid=models.AutoField(primary_key=True)
    RoomNumber=models.CharField(max_length=100)
    RoomType=models.CharField(max_length=100)
    RoomPrice=models.DecimalField(max_digits=10,decimal_places=2)
    Capacity=models.IntegerField()
    is_available=models.BooleanField(default=True)
    
class GuestProfile(models.Model):
    Gid = models.AutoField(primary_key=True)
    User = models.OneToOneField(User,on_delete=models.CASCADE)
    phoneno=models.CharField(max_length=15)
    Address=models.TextField()

class Booking(models.Model):
    BookingId = models.AutoField(primary_key=True)
    Rid = models.ForeignKey(Room,on_delete=models.CASCADE)
    Gid = models.ForeignKey(GuestProfile,on_delete=models.CASCADE)
    CheckInDate = models.DateField()
    CheckOutDate = models.DateField()
    TotalAmount = models.DecimalField(max_digits=10,decimal_places=2)
    status = models.CharField(max_length=100)

class Payment(models.Model):
    PaymentId = models.AutoField(primary_key=True)
    Booking = models.ForeignKey(Booking,on_delete=models.CASCADE)
    Amount = models.DecimalField(max_digits=10,decimal_places=2)
    PaymentDate = models.DateField()
    PaymentMethod = models.CharField(max_length=100)
    status = models.CharField(max_length=100)
    
    