from rest_framework import permissions

class IsStaffOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow staff to edit objects.
    """
    def has_permission(self, request, view):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the staff
        return request.user and request.user.is_staff

class IsBookingOwnerOrStaff(permissions.BasePermission):
    """
    Custom permission to allow owners of an object to edit it.
    Staff can view all.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Staff members can view all
        if request.user.is_staff:
            return True

        # Guests can only view/edit their own bookings
        # obj is a Booking instance
        return obj.Gid.User == request.user

class IsPaymentOwnerOrStaff(permissions.BasePermission):
    """
    Custom permission to allow owners of an object to edit it.
    Staff can view all.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Staff members can view all
        if request.user.is_staff:
            return True

        # Guests can only view/edit their own payments
        # obj is a Payment instance
        return obj.Booking.Gid.User == request.user
