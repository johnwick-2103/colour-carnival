from django.urls import path
from . import views

urlpatterns = [
    # Public URLs
    path('', views.index, name='index'),
    path('event/<int:event_id>/tickets/', views.event_tickets, name='event_tickets'),
    path('update-total/', views.update_total, name='update_total'),
    path('checkout/<int:event_id>/', views.checkout, name='checkout'),
    path('checkout/', views.checkout_display, name='checkout_display'),
    path('payment/verify/', views.payment_verify, name='payment_verify'),
    path('ticket/<str:order_id>/', views.download_ticket, name='download_ticket'),
    path('terms/', views.terms, name='terms'),
    
    # Organizer URLs
    path('organizer/dashboard/', views.organizer_dashboard, name='organizer_dashboard'),
    path('organizer/event/new/', views.organizer_event_create, name='organizer_event_create'),
    path('organizer/event/<int:event_id>/edit/', views.organizer_event_edit, name='organizer_event_edit'),
    path('organizer/event/<int:event_id>/delete/', views.organizer_event_delete, name='organizer_event_delete'),
    path('organizer/event/<int:event_id>/ticket/new/', views.organizer_event_add_ticket, name='organizer_event_add_ticket'),
    path('organizer/ticket/<int:ticket_id>/edit/', views.organizer_ticket_edit, name='organizer_ticket_edit'),
    path('organizer/ticket/<int:ticket_id>/delete/', views.organizer_ticket_delete, name='organizer_ticket_delete'),
]
