from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .models import Booking
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def send_booking_confirmation_email(self, booking_id):
    """
    Send booking confirmation email as a Celery background task.
    
    Args:
        booking_id (int): The ID of the booking to send confirmation for
    """
    try:
        # Get the booking object
        booking = Booking.objects.get(id=booking_id)
        guest_email = booking.guest.email
        listing_title = booking.listing.title
        
        # Email subject and content
        subject = f'Booking Confirmation - {listing_title}'
        
        # HTML email content
        html_message = render_to_string('listings/email/booking_confirmation.html', {
            'booking': booking,
            'listing': booking.listing,
            'guest': booking.guest,
        })
        
        # Plain text version
        plain_message = strip_tags(html_message)
        
        # Send email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[guest_email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Booking confirmation email sent successfully to {guest_email} for booking #{booking_id}")
        
        return f"Email sent successfully to {guest_email}"
        
    except Booking.DoesNotExist:
        logger.error(f"Booking with id {booking_id} does not exist")
        raise self.retry(countdown=60 * 5)  # Retry after 5 minutes
        
    except Exception as e:
        logger.error(f"Failed to send booking confirmation email: {str(e)}")
        # Retry the task after 5 minutes, with max 3 retries
        raise self.retry(exc=e, countdown=60 * 5)

@shared_task
def send_booking_notification_to_host(booking_id):
    """
    Send notification email to the host when a new booking is made.
    """
    try:
        booking = Booking.objects.get(id=booking_id)
        host_email = booking.listing.host.email
        listing_title = booking.listing.title
        
        subject = f'New Booking Notification - {listing_title}'
        
        html_message = render_to_string('listings/email/booking_notification_host.html', {
            'booking': booking,
            'listing': booking.listing,
            'guest': booking.guest,
        })
        
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[host_email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Booking notification sent to host {host_email} for booking #{booking_id}")
        
        return f"Notification sent to host {host_email}"
        
    except Exception as e:
        logger.error(f"Failed to send booking notification to host: {str(e)}")
        return f"Failed to send notification: {str(e)}"