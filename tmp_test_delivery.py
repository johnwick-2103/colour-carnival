import os
import django
import sys

# Setup Django Environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pune_color_festival.settings')
django.setup()

from core.tasks import send_ticket_email
from core.models import Booking

# Find a valid paid booking to safely test with
booking = Booking.objects.filter(status='paid').last()

if not booking:
    print("❌ No paid bookings found in the local database to use for testing.")
else:
    print(f"Testing Delivery for Booking ID: {booking.id} ({booking.customer_name})")
    
    # Optional: override the customer email to the owner's email for the test
    booking.customer_email = "aryandoshi21@gmail.com"
    booking.save()
    
    try:
        print("Executing task synchronously...")
        result = send_ticket_email(booking.id)
        print("\n✅ Task Completed. Result:")
        print(result)
    except Exception as e:
        print("\n❌ Task Failed with Exception:")
        import traceback
        traceback.print_exc()
