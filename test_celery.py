import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pune_color_festival.settings')
django.setup()

from core.models import Booking, TicketType
from core.tasks import send_ticket_email

t = TicketType.objects.first()
if t:
    b = Booking.objects.create(
        ticket_type=t, 
        customer_name='Test Celery', 
        customer_email='testcelery@example.com', 
        customer_phone='1234567890', 
        quantity=2, 
        total_amount=t.price*2, 
        status='paid', 
        payment_id='pay_123'
    )
    result = send_ticket_email.delay(b.id).get()
    print("TASK RESULT:", result)
else:
    print("No ticket types found.")
