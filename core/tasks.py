from celery import shared_task
from django.core.mail import EmailMessage
from django.conf import settings
from io import BytesIO
import qrcode
from .models import Booking

@shared_task
def send_ticket_email(booking_id):
    try:
        booking = Booking.objects.get(id=booking_id)
    except Booking.DoesNotExist:
        return f"Booking {booking_id} not found."

    if booking.status != 'paid':
        return f"Booking {booking_id} is not paid."

    # Generate QR Code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    # Encode booking details into the QR code
    qr_data = f"Booking ID: {booking.id}\nName: {booking.customer_name}\nEvent: {booking.ticket_type.event.title}\nTicket: {booking.ticket_type.name} x {booking.quantity}"
    qr.add_data(qr_data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save the QR code image to a BytesIO stream
    img_stream = BytesIO()
    img.save(img_stream, format='PNG')
    img_stream.seek(0)

    # Prepare Email
    subject = f"Your Tickets for {booking.ticket_type.event.title} - Pune Color Festival"
    message = f"""
    Dear {booking.customer_name},

    Thank you for purchasing tickets to {booking.ticket_type.event.title}!

    Booking Details:
    - Ticket: {booking.ticket_type.name}
    - Quantity: {booking.quantity}
    - Amount Paid: ₹{booking.total_amount}
    - Order/Payment ID: {booking.payment_id}

    Please find your ticket QR code attached. Show this QR code at the entry gates for verification.

    We look forward to seeing you at the festival!

    Regards,
    Pune Color Festival Team
    """

    email = EmailMessage(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@punecolorfestival.com',
        [booking.customer_email],
    )

    # Attach the QR code
    email.attach(f'ticket_qr_{booking.id}.png', img_stream.read(), 'image/png')
    
    # Send the email
    email.send(fail_silently=False)

    return f"Ticket email sent successfully for Booking {booking_id}."
