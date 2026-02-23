from django.db import models
from django.utils import timezone

class Event(models.Model):
    title = models.CharField(max_length=200, default="Pune Color Festival 8.0")
    description = models.TextField()
    date = models.DateTimeField(default=timezone.now)
    start_time = models.TimeField(blank=True, null=True, help_text="Event start time e.g. 10:00")
    end_time = models.TimeField(blank=True, null=True, help_text="Event end time e.g. 16:00")
    venue_name = models.CharField(max_length=200)
    venue_address = models.TextField()
    map_embed_url = models.URLField(max_length=1000, blank=True, null=True, help_text="Paste the Google Maps Embed URL (the src attribute from the iframe)")
    image = models.ImageField(upload_to='events/', blank=True, null=True)
    is_published = models.BooleanField(default=False)

    def __str__(self):
        return self.title

class TicketType(models.Model):
    event = models.ForeignKey(Event, related_name='ticket_types', on_delete=models.CASCADE)
    name = models.CharField(max_length=100) # VIP, Early Bird, etc.
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity_available = models.IntegerField()
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} - {self.event.title}"

class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
    ]
    ticket_type = models.ForeignKey(TicketType, on_delete=models.CASCADE)
    customer_name = models.CharField(max_length=100)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=15)
    quantity = models.IntegerField(default=1)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_id = models.CharField(max_length=100, blank=True, null=True) # Razorpay payment ID
    order_id = models.CharField(max_length=100, blank=True, null=True) # Razorpay order ID
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer_name} - {self.ticket_type.name}"

