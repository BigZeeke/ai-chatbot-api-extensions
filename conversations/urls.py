from django.urls import path
from . import views

urlpatterns = [
    path("conversations/", views.create_conversation, name="create-conversation"),
    path(
        "conversations/<int:conversation_id>/",
        views.get_conversation,
        name="get-conversation",
    ),
    path(
        "conversations/<int:conversation_id>/messages/",
        views.send_message,
        name="send-message",
    ),
]
