# Agentic Honeypot Simulation Guide

This guide explains how to bring the HoneyyTrap system online and run the simulation script. You can provide this entire file to an LLM to instruct it on how to participate in the test.

## 1. System Setup (Get Online)

### Prerequisites
- Python 3.10+
- Dependencies installed (`pip install -r requirements.txt`)
- Gemini API Key configured in `api/.env`

### Step A: Start the API Server
Open a terminal and run the backend server. **Make sure you are in the `HoneyyTrap` root directory.**

```bash
# Correct Command (loads api as a package)
python3 -m uvicorn api.main:app --reload
```
*Note: Keep this terminal open. You will see server logs and the final **Callback Payload** here.*

## 2. Running the Simulation

### Step B: Start the Interactive Simulator
Open a **new terminal** and run the simulation script. This script acts as the interface for the "Scammer".
```bash
python3 scripts/simulate_conversation.py
```

## 3. Instructions for LLM Tester (The Scammer)

**Context**: You represent the "Scammer" in this simulation. 
**Goal**: Test if the Agentic Honeypot can detect you, extract information, and keep you engaged.

**Procedure**:
1.  **Scenario Selection**: Choose a scam scenario (e.g., "Bank KYC Update", "Lottery Win", "Tech Support").
2.  **Initial Message**: Type an opening message in the simulation terminal.
    *   *Example*: "Dear customer, your SBI account is blocked. Update PAN immediately."
3.  **Engagement**: 
    *   The Agent (AI) will reply.
    *   Read the Agent's reply.
    *   Generate a natural response as a scammer would (be persistent, ask for money/details, get frustrated if they stall).
    *   Paste your response into the terminal.
4.  **Leak Info**: Eventually, provide a fake UPI ID (e.g., `scam@okicici`) or a fake Link (`http://bit.ly/fake`) to test extraction.
5.  **Conclusion**: Continue until the conversation ends or you successfully paste 10 messages.

## 4. Verifying Success

Look at the **Server Terminal (Step A)**. The test is successful if you see:
1.  **Scam Detected: True** in the logs.
2.  **Extracted Intelligence** showing the fake UPI/Link you provided.
3.  **[CALLBACK TRIGGERED]** payload printed at the end.
