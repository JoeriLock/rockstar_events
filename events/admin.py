from django.contrib import admin
from .models import Event, EventRegistration, Tag

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ["title", "starts_at", "location", "organizer", "attendee_count", "max_attendees"]
    list_filter = ["starts_at"]
    search_fields = ["title", "location"]


@admin.register(EventRegistration)
class EventRegistrationAdmin(admin.ModelAdmin):
    list_display = ["event", "user", "registered_at"]
    list_filter = ["event"]
