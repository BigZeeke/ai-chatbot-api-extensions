from django.db import models


class Conversation(models.Model):
    """Represents a chat conversation."""
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Conversation {self.id} ({self.created_at:%Y-%m-%d %H:%M})"


class Message(models.Model):
    """A single message within a conversation."""
    ROLE_CHOICES = [
        ("system", "System"),
        ("user", "User"),
        ("assistant", "Assistant"),
    ]

    conversation = models.ForeignKey(
        Conversation, related_name="messages", on_delete=models.CASCADE
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.role}: {self.content[:50]}"
