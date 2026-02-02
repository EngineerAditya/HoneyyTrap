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
├── main.py                  # FastAPI application entry point
├── models.py                # Pydantic models for request/response
├── requirements.txt         # Python dependencies
├── .env.example             # Example environment variables
├── README.md                # This file
└── intelligence/            # Intelligence extraction module
    ├── __init__.py          # Module exports
    ├── README.md            # Module documentation
    ├── patterns.py          # Regex patterns for extraction
    ├── extractor.py         # Main IntelligenceExtractor class
    ├── link_analyzer.py     # URL phishing analysis (WHOIS/DDG)
    └── session_store.py     # Session-based intelligence aggregation
```

---

## Testing Intelligence Extraction

The API automatically extracts scam indicators from every incoming message. To test this functionality:

### Test 1: Scam Message with Multiple Indicators

```bash
curl -X POST http://localhost:8000/honeypot \
  -H "Content-Type: application/json" \
  -H "x-api-key: my-super-secret-key-123" \
  -d '{
    "sessionId": "intel-test-001",
    "message": {
      "sender": "scammer",
      "text": "URGENT! Pay Rs 500 to scammer@okicici or visit http://fake-bank.xyz. Call +919876543210 now!",
      "timestamp": "2026-02-02T10:00:00Z"
    },
    "conversationHistory": []
  }'
```

**Check server terminal for extraction logs:**
```
[SESSION: intel-test-001] Received message from scammer
[SESSION: intel-test-001] Extracted: UPI IDs: scammer@okicici; Phone numbers: +919876543210; Suspicious links: http://fake-bank.xyz; Keywords: urgent, pay, bank
[SESSION: intel-test-001] Session scam detected: True
```

### Test 2: Verify Extraction Directly (Python)

```bash
cd api
python -c "
from intelligence import IntelligenceExtractor
import json

extractor = IntelligenceExtractor()
result = extractor.extract('Pay to scammer@okicici or visit http://fake-bank.xyz. Call +919876543210')
print(json.dumps(result, indent=2, default=str))
"
```

**Expected Output:**
```json
{
  "bankAccounts": [],
  "upiIds": ["scammer@okicici"],
  "phishingLinks": ["http://fake-bank.xyz"],
  "phoneNumbers": ["+919876543210"],
  "suspiciousKeywords": ["pay", "bank"],
  "emails": [],
  "allLinks": ["http://fake-bank.xyz"],
  "linkReports": [
    {
      "url": "http://fake-bank.xyz",
      "risk": "SUSPICIOUS",
      "reasons": ["Suspicious TLD: .xyz"],
      "domain": "fake-bank.xyz",
      "domain_age_days": null
    }
  ]
}
```

### Test 3: Verify Session Aggregation

```bash
cd api
python -c "
from intelligence import IntelligenceExtractor, session_store
import json

extractor = IntelligenceExtractor()

# Clear and start new session
session_store.clear_session('test-session')

# Add first message intel
intel1 = extractor.extract('Pay to scammer@okicici immediately!')
session_store.add_intelligence('test-session', intel1)

# Add second message intel
intel2 = extractor.extract('Call +919876543210 for help')
session = session_store.add_intelligence('test-session', intel2)

# Check aggregated result
print('Aggregated Intelligence:')
print(json.dumps(session.to_dict(), indent=2))
print('\\nScam Detected:', session.scam_detected)
print('Message Count:', session.message_count)
"
```

### Test 4: Verify GUVI Payload Format

```bash
cd api
python -c "
from intelligence import session_store
import json

# Assuming session exists from previous test
payload = session_store.get_final_payload('test-session', 'Scammer used urgency tactics')
print(json.dumps(payload, indent=2))
"
```

**Expected GUVI-compatible payload:**
```json
{
  "sessionId": "test-session",
  "scamDetected": true,
  "totalMessagesExchanged": 2,
  "extractedIntelligence": {
    "bankAccounts": [],
    "upiIds": ["scammer@okicici"],
    "phishingLinks": [],
    "phoneNumbers": ["+919876543210"],
    "suspiciousKeywords": ["pay", "immediately"]
  },
  "agentNotes": "Scammer used urgency tactics"
}
```

---

## What Gets Extracted

| Type | Pattern | Example |
|------|---------|---------|
| UPI IDs | `name@bankhandle` | `scammer@okicici` |
| Phone Numbers | Indian mobile (+91...) | `+919876543210` |
| Bank Accounts | 9-18 digits with context | `123456789012` |
| URLs | http/https links | `http://fake-bank.xyz` |
| Emails | Standard email format | `victim@gmail.com` |
| Keywords | Urgency, threats, etc. | `urgent`, `blocked`, `verify` |

---

## Link Risk Analysis

URLs are automatically analyzed with enhanced phishing detection:

### Risk Levels
| Level | Description |
|-------|-------------|
| `CRITICAL` | Institutional rule violation (bank without .bank.in, govt without .gov.in) |
| `HIGH_RISK` | Subdomain masking, typosquatting, shady TLD, new domain |
| `SUSPICIOUS` | Moderate concerns |
| `SAFE` | No issues found |

### Detection Rules

| Check | Criteria | Risk Level |
|-------|----------|------------|
| **Institutional (Bank)** | Bank context but not `.bank.in` | CRITICAL |
| **Institutional (Govt)** | Fines/taxes but not `.gov.in` | CRITICAL |
| **Subdomain Masking** | `sbi.bank.in.fake.com` | CRITICAL |
| **Typosquatting** | `sbi-bank.in`, `hdlc.com` | HIGH_RISK |
| **Shady TLD** | `.xyz`, `.vip`, `.top`, `.buzz` | HIGH_RISK |
| **Domain Age** | Created < 30 days ago | HIGH_RISK |
| **IP Address URL** | `http://192.168.1.1/...` | HIGH_RISK |
| **Web Reputation** | Scam reports found | HIGH_RISK |

### Test Enhanced Link Analysis

```bash
cd api
python -c "
from intelligence import IntelligenceExtractor
import json

extractor = IntelligenceExtractor()

# Banking scam: Wrong TLD
result = extractor.extract('Your HDFC account is blocked! Click http://hdfc.com/verify')
print('Risk:', result['linkReports'][0]['risk'])
print('Reason:', result['linkReports'][0]['reasons'][0])
"
```

**Output:**
```
Risk: CRITICAL
Reason: Bank context but URL is not .bank.in (domain: hdfc.com)
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

- [x] ~~Step 1: API endpoint structure~~
- [x] ~~Step 2: Intelligence extraction (UPI, phone, links, keywords)~~
- [x] ~~Step 3: Link phishing analysis (WHOIS, DDG)~~
- [ ] Step 4: AI agent for response generation
- [ ] Step 5: GUVI callback integration
- [ ] Step 6: Deploy to cloud
