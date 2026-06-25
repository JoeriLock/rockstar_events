from django.contrib.auth.models import User
from django.db import models


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Event(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=255, blank=True)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField(null=True, blank=True)
    max_attendees = models.PositiveIntegerField(null=True, blank=True)
    image = models.ImageField(upload_to="events/", blank=True, null=True)
    tags = models.ManyToManyField(Tag, blank=True, related_name="events")
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="organized_events")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["starts_at"]

    def __str__(self):
        return self.title

    @property
    def attendee_count(self):
        return self.registrations.count()

    @property
    def is_full(self):
        return self.max_attendees is not None and self.attendee_count >= self.max_attendees


class EventRegistration(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="registrations")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="registrations")
    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("event", "user")]

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} → {self.event.title}"
