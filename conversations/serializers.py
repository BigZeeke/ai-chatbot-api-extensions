from rest_framework import serializers
from .models import Conversation, Message


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ["id", "role", "content", "created_at"]
        read_only_fields = ["id", "role", "created_at"]


class ConversationSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = ["id", "created_at", "messages"]
        read_only_fields = ["id", "created_at"]


class SendMessageSerializer(serializers.Serializer):
    """Serializer for validating incoming user messages."""

    content = serializers.CharField(max_length=10000)


class ConversationListSerializer(serializers.ModelSerializer):
    """Serializer for the conversation list: no messages, only a count."""

    message_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Conversation
        fields = ["id", "created_at", "message_count"]
        read_only_fields = ["id", "created_at"]
