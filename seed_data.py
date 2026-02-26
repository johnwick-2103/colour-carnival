import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pune_color_festival.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import Event, TicketType

def seed():
    # Protect existing data from being wiped
    if Event.objects.exists():
        print("Database already contains events. Skipping seed to prevent data loss.")
        return
    
    # Create Organizer User
    if not User.objects.filter(username='organizer').exists():
        User.objects.create_superuser('organizer', 'organizer@example.com', 'password123')
        print("Created superuser: organizer / password123")
    
    # The ONE real event
    event = Event.objects.create(
        title="Colour Carnival 1.0",
        description="The Ultimate Holi Party of the Year! Come join us for an epic celebration of colours, music, and energy.",
        date="2026-03-08 10:00:00",
        venue_name="Pandhurang Lawns",
        venue_address="Guruvar Peth, Opposite to Reliance Mall, Ambajogai - 431517",
        start_time="10:00",
        end_time="16:00",
        map_embed_url="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3769.55!2d76.37!3d18.78!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x0%3A0x0!2zMTjCsDQ2JzQ4LjAiTiA3NsKwMjInMTIuMCJF!5e0!3m2!1sen!2sin!4v1700000000000",
        is_published=True
    )
    
    # Tickets
    TicketType.objects.create(event=event, name='Early Bird Children (0-10 years)', price=199.00, quantity_available=200, description='Entry for 1 Child.')
    TicketType.objects.create(event=event, name='Early Bird Single Girl', price=399.00, quantity_available=200, description='Entry for 1 Girl.')
    TicketType.objects.create(event=event, name='Early Bird Couple', price=599.00, quantity_available=150, description='Entry for 1 Couple (1 Male + 1 Female).')
    TicketType.objects.create(event=event, name='Group of 4 (For family, couples,and group)', price=1499.00, quantity_available=100, description='Entry for 4 people.')
    TicketType.objects.create(event=event, name='Group of 8 (For family, couples,and group)', price=2999.00, quantity_available=50, description='Entry for 8 people.')

    print("Database seeded successfully with Colour Carnival 1.0.")

if __name__ == '__main__':
    seed()
