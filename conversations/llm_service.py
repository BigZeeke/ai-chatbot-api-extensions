import requests
from django.conf import settings
from requests.exceptions import Timeout, ConnectionError, HTTPError


def get_llm_response(messages):
    """
    Send messages to the configured LLM API and return the response text.

    Args:
        messages: List of message dicts with 'role' and 'content' keys.

    Returns:
        str: The LLM's response text.

    Raises:
        Exception: If the API call fails.
    """
    headers = {"Content-Type": "application/json"}

    if settings.LLM_API_KEY:
        headers["Authorization"] = f"Bearer {settings.LLM_API_KEY}"

    payload = {
        "model": settings.LLM_MODEL,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 1024,
    }

    try:
        response = requests.post(
            f"{settings.LLM_API_URL}/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=60,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]

    except Timeout:
        raise Exception("LLM API request timed out. Please try again.")
    except ConnectionError:
        raise Exception(
            "Could not connect to LLM API. Check that the service is running."
        )
    except HTTPError as e:
        status = e.response.status_code
        if status == 401:
            raise Exception("Invalid LLM API key.")
        elif status == 429:
            raise Exception("LLM API rate limit exceeded. Please wait and try again.")
        else:
            raise Exception(f"LLM API error: HTTP {status}")
    except (KeyError, IndexError):
        raise Exception("Unexpected response format from LLM API.")


def build_messages_for_llm(conversation, max_messages=10):
    """
    Build the outbound message list for the LLM.

    Returns the system prompt plus the most recent `max_messages`
    non-system messages, in chronological order. The full history
    stays in the database; only this outbound list is truncated.
    """
    system_message = conversation.messages.filter(role="system").first()

    recent_messages = list(
        conversation.messages.exclude(role="system").order_by("-created_at", "-id")[
            :max_messages
        ]
    )
    recent_messages.reverse()

    messages_for_llm = []
    if system_message:
        messages_for_llm.append(
            {"role": system_message.role, "content": system_message.content}
        )
    for message in recent_messages:
        messages_for_llm.append({"role": message.role, "content": message.content})
    return messages_for_llm
