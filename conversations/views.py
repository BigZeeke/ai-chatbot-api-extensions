from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.conf import settings
from django.shortcuts import get_object_or_404

from .models import Conversation, Message
from .serializers import (
    ConversationSerializer,
    SendMessageSerializer,
)
from .llm_service import get_llm_response


@api_view(["POST"])
def create_conversation(request):
    """
    POST /api/conversations/
    Create a new conversation. Optionally accepts a system_prompt field.
    """
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


@api_view(["GET"])
def get_conversation(request, conversation_id):
    """
    GET /api/conversations/<id>/
    Retrieve a conversation with all its messages.
    """
    conversation = get_object_or_404(Conversation, id=conversation_id)
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

    # Build the message list from conversation history
    history = conversation.messages.all()
    messages_for_llm = [
        {"role": msg.role, "content": msg.content}
        for msg in history
    ]

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
