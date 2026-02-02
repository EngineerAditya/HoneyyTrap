# Intelligence Extraction Module

Comprehensive scam detection and intelligence extraction for the Honeypot API.

## Features

### 1. Entity Extraction (`patterns.py`)
| Type | Pattern | Example |
|------|---------|---------|
| UPI IDs | `name@bankhandle` | `scammer@okicici` |
| Phone Numbers | Indian mobile (+91) | `+919876543210` |
| Bank Accounts | 9-18 digits with context | `123456789012` |
| URLs | http/https links | `http://fake.xyz` |
| Emails | Standard format | `victim@gmail.com` |
| Keywords | Urgency, threats | `urgent`, `blocked` |

### 2. Enhanced Link Analysis (`link_analyzer.py`)

| Risk Level | Description |
|------------|-------------|
| `CRITICAL` | Institutional rule violation (.bank.in, .gov.in) |
| `HIGH_RISK` | Subdomain masking, typosquatting, shady TLD |
| `SUSPICIOUS` | Moderate concerns |
| `SAFE` | No issues found |

### 3. Scam Classification (`classifier.py`)

**Scam Types:**
- `bank_fraud` - Account blocked, KYC update
- `upi_fraud` - Pay to this UPI
- `phishing` - Click this link
- `lottery_scam` - You won a prize
- `job_scam` - Work from home offer
- `tech_support` - Device infected
- `impersonation` - I'm from RBI/Police
- `loan_scam` - Pre-approved loan

**Dynamic Confidence (0-100):**
```
Message 1: "Account blocked"     → 40%
Message 2: + phishing link       → 85%
Message 3: + asks for OTP        → 100%
```

### 4. Session Aggregation (`session_store.py`)

- Aggregates intelligence across multi-turn conversations
- Tracks conversation history
- Auto-generates agent notes
- Provides rich LLM context

---

## Quick Test

```bash
cd api
python -c "
from intelligence import IntelligenceExtractor, session_store
import json

extractor = IntelligenceExtractor()
session_store.clear_session('test')

# Add message
intel = extractor.extract('Your HDFC blocked! Click http://hdfc.com/verify')
session = session_store.add_intelligence('test', intel, {'sender': 'scammer', 'text': 'test', 'timestamp': '2026-02-02T10:00:00Z'})

print('Confidence:', session.confidence)
print('LLM Context:', json.dumps(session_store.get_llm_context('test'), indent=2))
"
```

---

## LLM Context Output

```python
session_store.get_llm_context('session-id') →
{
    "scamDetected": true,
    "confidence": 85,
    "scamType": "phishing",
    "urgency": "high",
    "tactics": {
        "impersonating": "HDFC Bank",
        "threats": ["legal action", "terminate"],
        "asksFor": ["OTP", "Verification"]
    },
    "intel": {
        "upiIds": ["scammer@okicici"],
        "phoneNumbers": [],
        "bankAccounts": [],
        "riskyLinks": ["http://hdfc.com/verify (CRITICAL: not .bank.in)"]
    },
    "session": {
        "messageCount": 3,
        "durationSeconds": 120
    }
}
```

---

## GUVI Final Payload

```python
session_store.get_final_payload('session-id') →
{
    "sessionId": "test-001",
    "scamDetected": true,
    "totalMessagesExchanged": 3,
    "extractedIntelligence": {
        "bankAccounts": [],
        "upiIds": ["scammer@okicici"],
        "phishingLinks": ["http://hdfc.com/verify"],
        "phoneNumbers": [],
        "suspiciousKeywords": ["blocked", "verify", "otp"]
    },
    "agentNotes": "Scam type: phishing. Confidence: 100%. Impersonating: HDFC Bank."
}
```

---

## Files

| File | Purpose |
|------|---------|
| `patterns.py` | Regex patterns for entity extraction |
| `link_analyzer.py` | Enhanced URL phishing detection |
| `classifier.py` | Scam type + confidence scoring |
| `extractor.py` | Main orchestrator class |
| `session_store.py` | Session aggregation + LLM context |
| `__init__.py` | Module exports |
