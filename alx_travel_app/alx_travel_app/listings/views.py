from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from .models import Listing, Booking
from .serializers import ListingSerializer, BookingSerializer
from .tasks import send_booking_confirmation_email, send_booking_notification_to_host

class ListingViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing property listings.
    
    Provides CRUD operations for Listing model.
    """
    queryset = Listing.objects.all()
    serializer_class = ListingSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def perform_create(self, serializer):
        """Set the host to the current user when creating a listing."""
        serializer.save(host=self.request.user)

class BookingViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing bookings.
    
    Provides CRUD operations for Booking model.
    """
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        Users can see their own bookings.
        """
        user = self.request.user
        if user.is_authenticated:
            return Booking.objects.filter(guest=user)
        return Booking.objects.none()
    
    def perform_create(self, serializer):
        """Set the guest to the current user and trigger email notifications."""
        booking = serializer.save(guest=self.request.user)
        
        # Trigger email tasks asynchronously using Celery
        try:
            # Send confirmation to guest
            send_booking_confirmation_email.delay(booking.id)
            
            # Send notification to host
            send_booking_notification_to_host.delay(booking.id)
            
        except Exception as e:
            # Log the error but don't fail the booking creation
            # The emails will be retried by Celery
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to queue email tasks for booking {booking.id}: {str(e)}")
    
    def create(self, request, *args, **kwargs):
        """
        Override create to return immediate response while emails are processed in background.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        
        return Response(
            {
                'message': 'Booking created successfully. Confirmation email will be sent shortly.',
                'booking': serializer.data
            },
            status=status.HTTP_201_CREATED,
            headers=headers
        )