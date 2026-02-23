from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from .models import Event, TicketType, Booking
from .forms import EventForm, TicketTypeForm
from .tasks import send_ticket_email
import base64
import io
import qrcode

def index(request):
    events = Event.objects.filter(is_published=True)
    
    context = {
        'events': events,
        'year': 2026,
    }
    return render(request, 'core/index.html', context)

def event_tickets(request, event_id):
    from django.shortcuts import get_object_or_404
    event = get_object_or_404(Event, id=event_id)
    ticket_types = TicketType.objects.filter(event=event)
    return render(request, 'core/partials/ticket_selection.html', {'event': event, 'ticket_types': ticket_types})

def update_total(request):
    total = 0
    for key, value in request.GET.items():
        if key.startswith('qty_'):
            try:
                ticket_id = int(key.split('_')[1])
                quantity = int(value)
                ticket = TicketType.objects.get(id=ticket_id)
                total += ticket.price * quantity
            except (ValueError, TicketType.DoesNotExist):
                continue
    
    return render(request, 'core/partials/total_display.html', {'total': total})

import razorpay
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseBadRequest

def checkout(request, event_id):
    if request.method != 'POST':
        return redirect('index')
        
    event = get_object_or_404(Event, id=event_id)
    customer_name = request.POST.get('customer_name')
    customer_email = request.POST.get('customer_email')
    customer_phone = request.POST.get('customer_phone')
    
    total_amount = 0
    selected_tickets = []
    
    for key, value in request.POST.items():
        if key.startswith('qty_'):
            try:
                ticket_id = int(key.split('_')[1])
                quantity = int(value)
                if quantity > 0:
                    ticket = TicketType.objects.get(id=ticket_id, event=event)
                    total_amount += ticket.price * quantity
                    selected_tickets.append((ticket, quantity))
            except (ValueError, TicketType.DoesNotExist):
                continue
                
    if total_amount == 0:
        return redirect('index') # Optionally show an error message

    # Initialize Razorpay Client or Bypass
    is_bypass = getattr(settings, 'LOCAL_PAYMENT_BYPASS', False)
    
    if is_bypass:
        order_id = f"local_test_{event.id}_{customer_phone}"
        payment_data = {'amount': int(total_amount * 100)}
    else:
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        payment_data = {
            'amount': int(total_amount * 100), # Amount in paise
            'currency': 'INR',
            'receipt': f'order_receipt_{event.id}'
        }
        razorpay_order = client.order.create(data=payment_data)
        order_id = razorpay_order['id']
    
    # Save Bookings
    for ticket, quantity in selected_tickets:
        Booking.objects.create(
            ticket_type=ticket,
            customer_name=customer_name,
            customer_email=customer_email,
            customer_phone=customer_phone,
            quantity=quantity,
            total_amount=ticket.price * quantity,
            order_id=order_id,
            status='pending'
        )
        
    context = {
        'event': event,
        'order_id': order_id,
        'amount': payment_data['amount'],
        'amount_rupees': payment_data['amount'] // 100,
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
        'customer_name': customer_name,
        'customer_email': customer_email,
        'customer_phone': customer_phone,
        'local_payment_bypass': is_bypass,
    }
    
    return render(request, 'core/checkout.html', context)

@csrf_exempt
def payment_verify(request):
    if request.method == "POST":
        data = request.POST
        payment_id = data.get('razorpay_payment_id', '')
        razorpay_order_id = data.get('razorpay_order_id', '')
        signature = data.get('razorpay_signature', '')
        is_bypass = getattr(settings, 'LOCAL_PAYMENT_BYPASS', False) and data.get('bypass') == 'true'

        if not is_bypass:
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            
            try:
                client.utility.verify_payment_signature({
                    'razorpay_order_id': razorpay_order_id,
                    'razorpay_payment_id': payment_id,
                    'razorpay_signature': signature
                })
            except razorpay.errors.SignatureVerificationError:
                # Payment signature verification failed
                bookings = Booking.objects.filter(order_id=razorpay_order_id)
                for booking in bookings:
                    booking.status = 'failed'
                    booking.save()
                return render(request, 'core/payment_failed.html', {'error': 'Invalid Payment Signature'})
                
        # If signature verification is successful or bypassed:
        if is_bypass:
            payment_id = f"bypassed_{razorpay_order_id}"

        bookings = Booking.objects.filter(order_id=razorpay_order_id)
        for booking in bookings:
            booking.status = 'paid'
            booking.payment_id = payment_id
            booking.save()
            
            # Trigger background task to send email and generate QR
            send_ticket_email.delay(booking.id)
            
        return render(request, 'core/payment_success.html', {'bookings': bookings})
            
    return redirect('index')

def download_ticket(request, order_id):
    bookings = Booking.objects.filter(order_id=order_id, status='paid')
    if not bookings.exists():
        return redirect('index')

    items = []
    for booking in bookings:
        qr = qrcode.QRCode(version=1, box_size=8, border=3)
        qr.add_data(f"ID:{booking.id}|{booking.customer_name}|{booking.ticket_type.name} x{booking.quantity}|Colour Carnival 1.0")
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        qr_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        items.append({
            'name': booking.customer_name,
            'ticket': booking.ticket_type.name,
            'qty': booking.quantity,
            'amount': booking.total_amount,
            'payment_id': booking.payment_id,
            'booking_id': booking.id,
            'qr': qr_b64,
        })

    return render(request, 'core/ticket.html', {'items': items})

# --- Organizer Views ---

@staff_member_required
def organizer_dashboard(request):
    events = Event.objects.all().order_by('-date')
    return render(request, 'organizer/dashboard.html', {'events': events})

@staff_member_required
def organizer_event_create(request):
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save()
            return redirect('organizer_dashboard')
    else:
        form = EventForm()
    return render(request, 'organizer/event_form.html', {'form': form, 'title': 'Create Event'})

@staff_member_required
def organizer_event_add_ticket(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if request.method == 'POST':
        form = TicketTypeForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.event = event
            ticket.save()
            return redirect('organizer_dashboard')
    else:
        form = TicketTypeForm()
    return render(request, 'organizer/ticket_form.html', {'form': form, 'event': event, 'title': f'Add Ticket to {event.title}'})

@staff_member_required
def organizer_ticket_edit(request, ticket_id):
    ticket = get_object_or_404(TicketType, id=ticket_id)
    if request.method == 'POST':
        form = TicketTypeForm(request.POST, instance=ticket)
        if form.is_valid():
            form.save()
            return redirect('organizer_dashboard')
    else:
        form = TicketTypeForm(instance=ticket)
    return render(request, 'organizer/ticket_form.html', {'form': form, 'event': ticket.event, 'title': f'Edit Ticket: {ticket.name}'})

@staff_member_required
def organizer_ticket_delete(request, ticket_id):
    ticket = get_object_or_404(TicketType, id=ticket_id)
    if request.method == 'POST':
        ticket.delete()
        return redirect('organizer_dashboard')
    return render(request, 'organizer/ticket_confirm_delete.html', {'ticket': ticket})

@staff_member_required
def organizer_event_edit(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            form.save()
            return redirect('organizer_dashboard')
    else:
        form = EventForm(instance=event)
    return render(request, 'organizer/event_form.html', {'form': form, 'title': f'Edit Event: {event.title}'})

@staff_member_required
def organizer_event_delete(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if request.method == 'POST':
        event.delete()
        return redirect('organizer_dashboard')
    return render(request, 'organizer/event_confirm_delete.html', {'event': event})

