# Frontend Notes

This React + Vite frontend sends assistant requests only to the backend endpoint:

- `POST /api/chat`

Do not place Gemini keys in frontend code or `.env` files used by Vite.

Configure Gemini in the backend `.env` file:

```env
GEMINI_API_KEY=your_key_here
# Optional
GEMINI_MODEL=models/gemini-2.5-flash
```

The backend `chat_service.py` reads these environment variables and handles the LLM call.
