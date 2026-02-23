from django import forms
from .models import Event, TicketType

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'description', 'date', 'venue_name', 'venue_address', 'map_embed_url', 'image', 'is_published']
        widgets = {
            'date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows': 4}),
        }

class TicketTypeForm(forms.ModelForm):
    class Meta:
        model = TicketType
        fields = ['name', 'price', 'quantity_available', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2}),
        }
