# Honeypot API

FastAPI-based input endpoint for the scam detection honeypot system.

## Quick Start

### 1. Create & Activate Conda Environment

```bash
# Create conda environment (one-time setup)
conda create -n honeyytrap python=3.11 -y

# Activate the environment
conda activate honeyytrap

# Install dependencies
cd api
pip install -r requirements.txt
```

> **Note:** Always activate the environment before running the API:
> ```bash
> conda activate honeyytrap
> ```

### 2. Set Up Environment Variables

```bash
# Copy the example env file
cp .env.example .env

# Edit .env and set your own API key
nano .env
```

Set your API key in the `.env` file:
```
HONEYPOT_API_KEY=my-super-secret-key-123
```

### 3. Run the Server

```bash
python main.py
```

Or using uvicorn directly:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at: `http://localhost:8000`

---

## Testing the API

### Method 1: Health Check (Simplest)

Open in browser or use curl:
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status": "healthy", "message": "Honeypot API is running"}
```

---

### Method 2: Test with curl (Recommended)

**First Message (No History):**
```bash
curl -X POST http://localhost:8000/honeypot \
  -H "Content-Type: application/json" \
  -H "x-api-key: my-super-secret-key-123" \
  -d '{
    "sessionId": "test-session-001",
    "message": {
      "sender": "scammer",
      "text": "Your bank account will be blocked today. Verify immediately.",
      "timestamp": "2026-01-31T10:15:30Z"
    },
    "conversationHistory": [],
    "metadata": {
      "channel": "SMS",
      "language": "English",
      "locale": "IN"
    }
  }'
```

Expected response:
```json
{
  "status": "success",
  "reply": "I received your message. Can you tell me more about this?"
}
```

**Follow-up Message (With History):**
```bash
curl -X POST http://localhost:8000/honeypot \
  -H "Content-Type: application/json" \
  -H "x-api-key: my-super-secret-key-123" \
  -d '{
    "sessionId": "test-session-001",
    "message": {
      "sender": "scammer",
      "text": "Share your UPI ID to avoid account suspension.",
      "timestamp": "2026-01-31T10:17:10Z"
    },
    "conversationHistory": [
      {
        "sender": "scammer",
        "text": "Your bank account will be blocked today. Verify immediately.",
        "timestamp": "2026-01-31T10:15:30Z"
      },
      {
        "sender": "user",
        "text": "Why will my account be blocked?",
        "timestamp": "2026-01-31T10:16:10Z"
      }
    ],
    "metadata": {
      "channel": "SMS",
      "language": "English",
      "locale": "IN"
    }
  }'
```

---

### Method 3: Test with Invalid API Key (Auth Check)

```bash
curl -X POST http://localhost:8000/honeypot \
  -H "Content-Type: application/json" \
  -H "x-api-key: wrong-key" \
  -d '{"sessionId": "test", "message": {"sender": "scammer", "text": "test", "timestamp": "2026-01-31T10:00:00Z"}}'
```

Expected response (401 Unauthorized):
```json
{"detail": "Invalid API key"}
```

---

### Method 4: Interactive API Docs

FastAPI auto-generates documentation. Open in browser:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

You can test the API directly from the Swagger UI!

---

## File Structure

```
api/
├── main.py           # FastAPI application entry point
├── models.py         # Pydantic models for request/response
├── requirements.txt  # Python dependencies
├── .env.example      # Example environment variables
└── README.md         # This file
```

---

## API Endpoints

| Method | Endpoint    | Description                          | Auth Required |
|--------|-------------|--------------------------------------|---------------|
| GET    | `/health`   | Health check                         | No            |
| POST   | `/honeypot` | Process scam message                 | Yes           |

---

## Request/Response Format

### Request Headers
```
Content-Type: application/json
x-api-key: YOUR_API_KEY
```

### Request Body
```json
{
  "sessionId": "unique-session-id",
  "message": {
    "sender": "scammer",
    "text": "Message content",
    "timestamp": "2026-01-31T10:00:00Z"
  },
  "conversationHistory": [],
  "metadata": {
    "channel": "SMS",
    "language": "English",
    "locale": "IN"
  }
}
```

### Response Body
```json
{
  "status": "success",
  "reply": "Agent's response"
}
```

---

## Next Steps (TODO)

- [ ] Step 2: Add scam detection logic
- [ ] Step 3: Add AI agent for response generation
- [ ] Step 4: Intelligence extraction
- [ ] Step 5: GUVI callback integration
- [ ] Step 6: Deploy to cloud
