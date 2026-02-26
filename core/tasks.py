from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from io import BytesIO
import base64
import qrcode
import qrcode.constants
from .models import Booking


@shared_task
def send_ticket_email(booking_id):
    try:
        booking = Booking.objects.get(id=booking_id)
    except Booking.DoesNotExist:
        return f"Booking {booking_id} not found."

    if booking.status != 'paid':
        return f"Booking {booking_id} is not paid."

    event = booking.ticket_type.event

    # Generate QR Code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(
        f"ID:{booking.id}|{booking.customer_name}|{booking.ticket_type.name} x{booking.quantity}|Colour Carnival 1.0"
    )
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img_stream = BytesIO()
    img.save(img_stream, format='PNG')
    img_stream.seek(0)

    # Build ticket download URL
    site_url = getattr(settings, 'SITE_URL', 'https://colour-carnival.onrender.com')
    ticket_url = f"{site_url}/ticket/{booking.order_id}/"

    subject = f"Your Ticket — Colour Carnival 1.0 🎉"

    # Plain text fallback
    text_body = f"""
Dear {booking.customer_name},

🎉 Payment Successful! Your ticket is confirmed.

Booking Details:
  Event     : {event.title}
  Ticket    : {booking.ticket_type.name}
  Quantity  : {booking.quantity}
  Amount    : ₹{booking.total_amount}
  Payment ID: {booking.payment_id}

📥 Download your ticket here:
{ticket_url}

Show the QR code at the entry gate. The QR image is also attached.

📅 Date   : 8th March, 2026 | 10:00 AM – 4:00 PM
📍 Venue  : Pandhurang Lawns, Guruvar Peth, Ambajogai

For queries: 9145452609 / 9359176168 | @colourcarnival_1.0

See you there! 🌈
— Colour Carnival Team
    """

    # HTML email body
    html_body = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
  body {{ font-family: 'Helvetica Neue', Arial, sans-serif; background: #f5f5f5; margin: 0; padding: 0; }}
  .wrapper {{ max-width: 580px; margin: 30px auto; background: #fff; border-radius: 14px; overflow: hidden; box-shadow: 0 4px 24px rgba(0,0,0,0.10); }}
  .header {{ background: linear-gradient(135deg, #E8182A, #f4a261); padding: 36px 30px; text-align: center; color: #fff; }}
  .header h1 {{ margin: 0 0 6px; font-size: 26px; font-weight: 900; letter-spacing: 1px; text-transform: uppercase; }}
  .header p {{ margin: 0; font-size: 14px; opacity: 0.9; }}
  .success-badge {{ background: #27ae60; color: #fff; font-size: 15px; font-weight: 700; text-align: center; padding: 12px; }}
  .body {{ padding: 30px; }}
  .greeting {{ font-size: 16px; color: #333; margin-bottom: 20px; }}
  .table {{ width: 100%; border-collapse: collapse; margin-bottom: 24px; }}
  .table td {{ padding: 10px 12px; font-size: 14px; border-bottom: 1px solid #f0f0f0; }}
  .table td:first-child {{ font-weight: 700; color: #555; width: 40%; }}
  .table td:last-child {{ color: #222; }}
  .amount {{ color: #E8182A; font-weight: 900; font-size: 16px; }}
  .btn {{ display: block; background: #E8182A; color: #fff !important; text-decoration: none; text-align: center; padding: 15px 30px; border-radius: 8px; font-size: 15px; font-weight: 700; margin: 24px 0; letter-spacing: 0.5px; }}
  .info-box {{ background: #fff8e1; border-left: 4px solid #FFD700; padding: 14px 18px; border-radius: 6px; margin-bottom: 20px; }}
  .info-box p {{ margin: 4px 0; font-size: 13px; color: #555; }}
  .info-box strong {{ color: #333; }}
  .footer {{ background: #1a1a1a; color: #aaa; text-align: center; padding: 20px; font-size: 12px; }}
  .footer a {{ color: #FFD700; text-decoration: none; }}
</style>
</head>
<body>
<div class="wrapper">
  <div class="header">
    <h1>Colour Carnival 1.0</h1>
    <p>The Ultimate Holi Party of the Year! 🎉</p>
  </div>
  <div class="success-badge">✅ Payment Successful — Ticket Confirmed!</div>
  <div class="body">
    <p class="greeting">Dear <strong>{booking.customer_name}</strong>, thank you for booking!</p>
    <table class="table">
      <tr><td>🎪 Event</td><td>{event.title}</td></tr>
      <tr><td>🎟 Ticket Type</td><td>{booking.ticket_type.name}</td></tr>
      <tr><td>🔢 Quantity</td><td>{booking.quantity} person(s)</td></tr>
      <tr><td>💳 Amount Paid</td><td class="amount">₹{booking.total_amount}</td></tr>
      <tr><td>🔑 Payment ID</td><td style="font-size:12px;">{booking.payment_id}</td></tr>
      <tr><td>📋 Booking ID</td><td>#{booking.id}</td></tr>
    </table>

    <a href="{ticket_url}" class="btn">📥 Download My Ticket &amp; QR Code</a>

    <div class="info-box">
      <p><strong>📅 Date:</strong> 8th March, 2026 &nbsp;|&nbsp; 10:00 AM – 4:00 PM</p>
      <p><strong>📍 Venue:</strong> Pandhurang Lawns, Guruvar Peth, Ambajogai – 431517</p>
      <p><strong>⚠️ Important:</strong> Show the QR code (in ticket or attached) at the entry gate.</p>
    </div>

    <p style="font-size:13px; color:#888;">Your QR code is also attached to this email as an image backup.</p>
  </div>
  <div class="footer">
    For queries: <a href="tel:9145452609">9145452609</a> / <a href="tel:9359176168">9359176168</a>
    &nbsp;|&nbsp; <a href="https://instagram.com/colourcarnival_1.0">@colourcarnival_1.0</a><br><br>
    © 2026 Colour Carnival. All rights reserved.
  </div>
</div>
</body>
</html>
    """

    # --- Resend Email Delivery ---
    resend_key = getattr(settings, 'RESEND_API_KEY', '')
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'Colour Carnival <noreply@punecolorfestival.com>')
    email_status = "Skipped (No Resend Key)"
    
    if resend_key:
        try:
            resend_url = "https://api.resend.com/emails"
            headers = {
                "Authorization": f"Bearer {resend_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "from": from_email,
                "to": [booking.customer_email],
                "subject": subject,
                "html": html_body,
                "text": text_body,
                "attachments": [
                    {
                        "filename": f"ticket_qr_{booking.id}.png",
                        "content": base64.b64encode(img_stream.read()).decode('utf-8')
                    }
                ]
            }
            resp = requests.post(resend_url, headers=headers, json=payload, timeout=10)
            if resp.status_code in [200, 201]:
                email_status = "Sent"
            else:
                email_status = f"Failed: {resp.text}"
        except Exception as e:
            email_status = f"Error: {str(e)}"

    # --- WhatsApp Ticket Delivery ---
    whatsapp_status = "Skipped (No API Keys)"
    phone_id = getattr(settings, 'WHATSAPP_PHONE_NUMBER_ID', '')
    token = getattr(settings, 'WHATSAPP_ACCESS_TOKEN', '')

    if phone_id and token:
        try:
            import re
            clean_phone = re.sub(r'\D', '', booking.customer_phone)
            if len(clean_phone) == 10:
                clean_phone = f"91{clean_phone}"

            url = f"https://graph.facebook.com/v18.0/{phone_id}/messages"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            payload = {
                "messaging_product": "whatsapp",
                "to": clean_phone,
                "type": "template",
                "template": {
                    "name": "hello_world",
                    "language": {
                        "code": "en_US"
                    }
                }
            }
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            
            if response.status_code in [200, 201]:
                whatsapp_status = f"Sent to {clean_phone}"
            else:
                whatsapp_status = f"Failed ({response.status_code}): {response.text}"
        except Exception as e:
            whatsapp_status = f"Error: {str(e)}"

    return f"Resend Email: {email_status} | WhatsApp: {whatsapp_status}"
