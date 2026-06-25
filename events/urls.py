from django.urls import path
from . import views

urlpatterns = [
    path("", views.EventListView.as_view(), name="event_list"),
    path("events/<int:pk>/", views.EventDetailView.as_view(), name="event_detail"),
    path("events/new/", views.create_event, name="create_event"),
    path("events/<int:pk>/edit/", views.edit_event, name="edit_event"),
    path("events/<int:pk>/delete/", views.delete_event, name="delete_event"),
    path("events/<int:pk>/register/", views.register, name="event_register"),
    path("events/<int:pk>/unregister/", views.unregister, name="event_unregister"),
    path("my-events/", views.my_events, name="my_events"),
    path("login/", views.poc_login, name="poc_login"),
    path("logout/", views.poc_logout, name="poc_logout"),
    path("register/", views.signup, name="register"),
    path("verify/<str:token>/", views.verify_email, name="verify_email"),
]
