from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.conf import settings
from django.db.models import Count
from django.shortcuts import get_object_or_404

from .models import Conversation, Message
from .serializers import (
    ConversationListSerializer,
    ConversationSerializer,
    SendMessageSerializer,
)
from .llm_service import build_messages_for_llm, get_llm_response


@api_view(["GET", "POST"])
def create_conversation(request):
    """
    GET /api/conversations/
    List all conversations, newest first, with a message count.

    POST /api/conversations/
    Create a new conversation. Optionally accepts a system_prompt field.
    """
    if request.method == "GET":
        conversations_with_counts = Conversation.objects.annotate(
            message_count=Count("messages")
        ).order_by("-created_at")
        serializer = ConversationListSerializer(
            conversations_with_counts, many=True
        )
        return Response(serializer.data)

    conversation = Conversation.objects.create()

    # Create the system message for this conversation
    system_prompt = request.data.get(
        "system_prompt", settings.LLM_SYSTEM_PROMPT)
    Message.objects.create(
        conversation=conversation,
        role="system",
        content=system_prompt,
    )

    serializer = ConversationSerializer(conversation)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(["GET", "DELETE"])
def get_conversation(request, conversation_id):
    """
    GET /api/conversations/<id>/
    Retrieve a conversation with all its messages.

    DELETE /api/conversations/<id>/
    Delete a conversation and all of its messages.
    """
    conversation = get_object_or_404(Conversation, id=conversation_id)

    if request.method == "DELETE":
        conversation.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = ConversationSerializer(conversation)
    return Response(serializer.data)


@api_view(["POST"])
def send_message(request, conversation_id):
    """
    POST /api/conversations/<id>/messages/
    Send a user message and get an AI response.
    """
    conversation = get_object_or_404(Conversation, id=conversation_id)

    # Validate the incoming message
    serializer = SendMessageSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user_content = serializer.validated_data["content"]

    # Save the user's message
    Message.objects.create(
        conversation=conversation,
        role="user",
        content=user_content,
    )

    # Build the outbound message list: system prompt + most recent messages
    messages_for_llm = build_messages_for_llm(conversation, max_messages=10)

    # Call the LLM
    try:
        ai_response = get_llm_response(messages_for_llm)
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    # Save the assistant's response
    assistant_message = Message.objects.create(
        conversation=conversation,
        role="assistant",
        content=ai_response,
    )

    # Return both the user message and the assistant's response
    return Response(
        {
            "user_message": {
                "role": "user",
                "content": user_content,
            },
            "assistant_message": {
                "role": "assistant",
                "content": ai_response,
            },
        },
        status=status.HTTP_201_CREATED,
    )
