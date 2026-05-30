# AI Chatbot API Extensions

Three extensions to the Django REST Framework AI chatbot you built in today's lesson ([week16/day4](https://github.com/CP-Evenings-and-Weekends/curriculum/blob/main/Module_06_AI_LLMs/week16/day4/README.md)).

Use your in-class project as the starter — the lesson walked you through the entire build (models, serializers, llm_service, three views, urls).  This repo's job is to spell out exactly what to add on top.

## Setup reminder

If your in-class code is in good shape, just keep building on it.  If it isn't, the cleanest thing to do is re-walk the lesson with your eyes open — the build is short enough that a clean rebuild is faster than untangling a broken one.

You should have, before starting:

- A running PostgreSQL DB named `ai_chatbot`
- Two existing endpoints working: `POST /api/conversations/` and `POST /api/conversations/<id>/messages/`
- Either Ollama on `localhost:11434` or an `OPENAI_API_KEY` in your `.env`

Test the existing endpoints with curl (as shown in the lesson) and make sure both round-trips succeed before moving on.

## Assignment 1 — `DELETE /api/conversations/<id>/`

Delete a conversation and all its messages.  Because `Message.conversation` uses `on_delete=models.CASCADE`, the database does the cascade for you — your view just calls `.delete()` on the conversation.

### Requirements
- New `delete_conversation` view (or extend the existing `get_conversation` to also handle `DELETE`)
- Returns `204 No Content` on success
- Returns `404` if the conversation doesn't exist (use `get_object_or_404`)

### Verify
```bash
curl -X DELETE -i http://localhost:8000/api/conversations/1/
# expect: HTTP/1.1 204 No Content

curl -X DELETE -i http://localhost:8000/api/conversations/9999/
# expect: HTTP/1.1 404 Not Found
```

## Assignment 2 — `GET /api/conversations/`

List all conversations with their `id`, `created_at`, and message count.

### Requirements
- New `list_conversations` view
- Order by `created_at` descending (newest first — matches the `Conversation` model's default `Meta.ordering`)
- Each item in the response should include the message count without N+1-querying the DB.  Use Django's `annotate(message_count=Count("messages"))` so a single query gets everything.

### Expected response shape

```json
[
  {"id": 3, "created_at": "2026-09-19T15:10:00Z", "message_count": 12},
  {"id": 2, "created_at": "2026-09-19T15:05:00Z", "message_count": 4},
  {"id": 1, "created_at": "2026-09-19T15:00:00Z", "message_count": 8}
]
```

### Verify
```bash
curl http://localhost:8000/api/conversations/
```

## Assignment 3 — Token-limit truncation

The lesson showed `build_messages_for_llm(conversation, max_messages=20)` in the "Token Limits and Truncation Strategies" section.  Wire it in.

### Requirements
- Replace the inline `[{...} for msg in history]` list construction in `send_message` with a call to `build_messages_for_llm(conversation, max_messages=20)`
- If a conversation exceeds 20 non-system messages, only the system prompt + most recent 10 non-system messages get sent to the LLM
- The full history still gets **persisted** in the DB — only the **outbound** request gets truncated

### Verify
The easiest test: spin up a conversation, send 25 messages, then check that the LLM still responds without a token-limit error.  Add a `print(len(messages_for_llm))` in `send_message` temporarily to confirm the outbound list caps at 11 (1 system + 10 recent).

## Things to think about
- For Assignment 2, why does `annotate(message_count=Count("messages"))` matter more than looping `for c in Conversation.objects.all(): c.messages.count()`?  How many queries does each version run for 100 conversations?
- The truncation in Assignment 3 silently drops older context.  How would a user notice?  How would you indicate it in the UI?
- What happens if the system prompt itself is enormous?  Does your truncation strategy still help?

## Stretch
- **Soft delete**: instead of actually deleting, add a `deleted_at` timestamp on Conversation and exclude soft-deleted conversations from the list endpoint.  Useful for "undo delete" UX.
- **Token counting, not message counting**: use `tiktoken` (the lib you used in [llm-token-explorer](https://github.com/CP-Evenings-and-Weekends/llm-token-explorer)) to truncate by actual token budget, not message count.
- **Summarization**: when history exceeds N messages, make a separate LLM call to summarize the oldest N/2 messages and replace them with a single synthesized "Earlier in this conversation, the user…" message.
- **Pagination** on the list endpoint with DRF's `PageNumberPagination`.

> Stuck? Have a code error? Use the ["4 Before Me"](https://docs.google.com/document/d/1nseOs5oabYBKNHfwJZNAR7GlU0zkZxNagsw63AD7XV0/edit) debugging checklist to help you solve it!
