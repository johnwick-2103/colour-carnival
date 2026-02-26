from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from io import BytesIO
import base64
import requests
import re
import weasyprint
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
    qr_b64 = base64.b64encode(img_stream.read()).decode('utf-8')
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
    
    # settings.DEFAULT_FROM_EMAIL evaluates to '' if not set, so getattr fallback won't trigger.
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', '')
    if not from_email:
        # If no domain is configured, default to Resend's testing sandbox
        from_email = 'Colour Carnival <onboarding@resend.dev>'

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
                        "content": qr_b64
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
            clean_phone = re.sub(r'\D', '', booking.customer_phone)
            if len(clean_phone) == 10:
                clean_phone = f"91{clean_phone}"

            pdf_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
            <meta charset="UTF-8">
            <style>
              body {{ font-family: 'Helvetica Neue', Arial, sans-serif; background: #fff; margin: 0; padding: 20px; }}
              .wrapper {{ max-width: 600px; margin: 0 auto; border: 2px solid #333; border-radius: 12px; overflow: hidden; }}
              .header {{ background: #E8182A; padding: 20px; text-align: center; color: #fff; border-bottom: 4px solid #333; }}
              .header h1 {{ margin: 0; font-size: 28px; text-transform: uppercase; letter-spacing: 2px; }}
              .receipt-badge {{ background: #222; color: #fff; font-size: 16px; font-weight: 700; text-align: center; padding: 10px; text-transform: uppercase; letter-spacing: 1px; }}
              .body {{ padding: 30px; }}
              .table {{ width: 100%; border-collapse: collapse; margin-bottom: 30px; font-size: 16px; }}
              .table td {{ padding: 12px 10px; border-bottom: 1px solid #eee; }}
              .table td:first-child {{ font-weight: bold; color: #555; width: 40%; }}
              .amount {{ color: #E8182A; font-weight: bold; font-size: 18px; }}
              .qr-container {{ text-align: center; margin: 20px 0; padding: 20px; background: #f9f9f9; border-radius: 8px; border: 1px dashed #ccc; }}
              .qr-container img {{ width: 220px; height: 220px; }}
              .qr-hint {{ font-size: 14px; color: #666; margin-top: 10px; font-weight: bold; }}
              .footer {{ text-align: center; padding: 20px; font-size: 12px; color: #888; border-top: 1px solid #eee; margin-top: 20px; }}
            </style>
            </head>
            <body>
            <div class="wrapper">
              <div class="header">
                <h1>Colour Carnival 1.0</h1>
                <p style="margin: 5px 0 0; opacity: 0.9;">Official Event Ticket</p>
              </div>
              <div class="receipt-badge">Payment Receipt / Admittance Pass</div>
              <div class="body">
                <p><strong>Name:</strong> {booking.customer_name}</p>
                <table class="table">
                  <tr><td>🎪 Event</td><td>{event.title}</td></tr>
                  <tr><td>🎟 Ticket Type</td><td>{booking.ticket_type.name}</td></tr>
                  <tr><td>🔢 Quantity</td><td>{booking.quantity} Person(s)</td></tr>
                  <tr><td>💳 Total Paid</td><td class="amount">₹{booking.total_amount}</td></tr>
                  <tr><td>🔑 Payment ID</td><td>{booking.payment_id}</td></tr>
                  <tr><td>📋 Booking ID</td><td>#{booking.id}</td></tr>
                </table>
                
                <div class="qr-container">
                  <img src="data:image/png;base64,{qr_b64}" alt="Ticket QR Code" />
                  <div class="qr-hint">Scan this QR Code at the Entry Gate</div>
                </div>

                <div style="font-size: 14px; color: #444; text-align: center; margin-top: 30px;">
                  <p><strong>📅 Date:</strong> 8th March, 2026 | 10:00 AM – 4:00 PM</p>
                  <p><strong>📍 Venue:</strong> Pandhurang Lawns, Guruvar Peth, Ambajogai – 431517</p>
                </div>
              </div>
              <div class="footer">
                Colour Carnival &copy; 2026 | Support: 9145452609 / 9359176168
              </div>
            </div>
            </body>
            </html>
            """

            # Step 1: Generate PDF from the HTML Receipt Body
            pdf_bytes = weasyprint.HTML(string=pdf_html).write_pdf()

            # Step 2: Upload PDF to Meta API (Media Endpoint)
            media_url = f"https://graph.facebook.com/v18.0/{phone_id}/media"
            media_headers = {
                "Authorization": f"Bearer {token}"
            }
            # Simplifying file upload structure for the requests library
            files = {
                "file": (f"Colour-Carnival-Ticket-{booking.id}.pdf", pdf_bytes, "application/pdf")
            }
            data = {"messaging_product": "whatsapp"}
            media_response = requests.post(media_url, headers=media_headers, data=data, files=files, timeout=15)
            
            if media_response.status_code in [200, 201]:
                media_id = media_response.json().get('id')
                
                # Step 3: Send WhatsApp Message with Document Attachment
                message_url = f"https://graph.facebook.com/v18.0/{phone_id}/messages"
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
                
                # We send a standard document message instead of a template.
                # Note: Sending free-form messages requires the user to have initiated the chat within 24h,
                # OR we must use a pre-approved template that supports document headers.
                # Assuming this is a business-initiated standard template with a documented header:
                payload = {
                    "messaging_product": "whatsapp",
                    "to": clean_phone,
                    "type": "document",
                    "document": {
                        "id": media_id,
                        "caption": f"🎟 Colour Carnival Ticket - #{booking.id}\nThank you {booking.customer_name}! Show the attached QR code at the entry gate.",
                        "filename": f"Colour-Carnival-Ticket-#{booking.id}.pdf"
                    }
                }
                
                msg_response = requests.post(message_url, headers=headers, json=payload, timeout=10)
                
                if msg_response.status_code in [200, 201]:
                    whatsapp_status = f"Sent Document to {clean_phone}"
                else:
                    # Fallback to the pre-approved hello_world template if Meta rejects free-form documents
                    # (Meta blocks raw files if the customer hasn't messaged the business in 24 hours)
                    fallback_payload = {
                        "messaging_product": "whatsapp",
                        "to": clean_phone,
                        "type": "template",
                        "template": {
                            "name": "hello_world",
                            "language": { "code": "en_US" }
                        }
                    }
                    fallback_resp = requests.post(message_url, headers=headers, json=fallback_payload, timeout=10)
                    if fallback_resp.status_code in [200, 201]:
                        whatsapp_status = f"Sent 'hello_world' Template to {clean_phone} (Document blocked by Meta 24h rule)"
                    else:
                        whatsapp_status = f"Document Failed: {msg_response.text} | Template Failed: {fallback_resp.text}"
            else:
                whatsapp_status = f"Media Upload Failed: {media_response.text}"
                
        except Exception as e:
            whatsapp_status = f"Error: {str(e)}"

    return f"Resend Email: {email_status} | WhatsApp: {whatsapp_status}"
