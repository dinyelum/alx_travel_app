# ALX Travel App with Celery & Email Notifications

This project extends the ALX Travel App with Celery background tasks and email notifications for bookings.

## New Features

- **Celery Background Tasks**: Asynchronous email sending
- **Booking Confirmation Emails**: Automatic emails to guests
- **Host Notifications**: Email alerts to property hosts
- **RabbitMQ Integration**: Message broker for task queue

## Setup Instructions

### 1. Install Dependencies

```bash
pip install celery django-celery-results