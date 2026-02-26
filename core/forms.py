from django import forms
from .models import Event, TicketType

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'description', 'date', 'start_time', 'end_time', 'venue_name', 'venue_address', 'map_embed_url', 'image', 'is_published']
        widgets = {
            'date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
            'description': forms.Textarea(attrs={'rows': 4}),
        }

class TicketTypeForm(forms.ModelForm):
    class Meta:
        model = TicketType
        fields = ['name', 'price', 'quantity_available', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2}),
        }
