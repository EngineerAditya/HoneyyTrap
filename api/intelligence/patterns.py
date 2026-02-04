"""
Intelligence Extraction Module - Regex Patterns

This module contains all compiled regex patterns for extracting scam indicators
from text messages. Patterns are designed for Indian context (UPI, +91 phones, etc).
"""

import re
from typing import List

# ============== URL PATTERNS ==============
# Matches http:// and https:// URLs
# Improved to not capture trailing punctuation
URL_PATTERN = re.compile(
    r'https?://[^\s<>"\')\]]+',
    re.IGNORECASE
)

# ============== UPI ID PATTERNS ==============
# Matches VPA format: name@bankhandle
# Common handles: okaxis, okicici, okhdfcbank, ybl, paytm, upi, etc.
UPI_PATTERN = re.compile(
    r'\b[a-zA-Z0-9._-]{2,256}@[a-zA-Z]{2,64}\b',
    re.IGNORECASE
)

# ============== PHONE NUMBER PATTERNS ==============
# Indian mobile numbers: +91, 0, or direct 10 digits starting with 6-9
PHONE_PATTERN = re.compile(
    r'(?:\+91[-\s]?|0)?[6-9]\d{9}\b'
)

# ============== BANK ACCOUNT PATTERNS ==============
# Generic bank account numbers: 9-18 digits
# Note: This may have false positives, so we look for context clues
BANK_ACCOUNT_PATTERN = re.compile(
    r'\b\d{9,18}\b'
)

# ============== EMAIL PATTERNS ==============
# Standard email format
EMAIL_PATTERN = re.compile(
    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    re.IGNORECASE
)

# ============== SUSPICIOUS KEYWORDS ==============
# Words/phrases that indicate urgency, threats, or scam tactics
SUSPICIOUS_KEYWORDS: List[str] = [
    # Urgency
    "urgent", "immediately", "now", "today", "asap", "hurry",
    # Threats
    "blocked", "suspended", "closed", "deactivated", "frozen",
    "terminate", "legal action", "police", "arrest",
    # Requests
    "verify", "confirm", "update", "click", "link",
    "share", "send", "transfer", "pay",
    # Authority impersonation
    "bank", "rbi", "government", "income tax", "customs",
    "sbi", "hdfc", "icici", "axis",
    # Money
    "refund", "cashback", "lottery", "prize", "winner",
    "credit", "loan", "emi",
    # OTP/Security
    "otp", "pin", "password", "cvv", "card number",
]

# Compile keywords into a pattern for efficient matching
SUSPICIOUS_KEYWORDS_PATTERN = re.compile(
    r'\b(' + '|'.join(re.escape(kw) for kw in SUSPICIOUS_KEYWORDS) + r')\b',
    re.IGNORECASE
)


def extract_urls(text: str) -> List[str]:
    """Extract all URLs from text."""
    urls = URL_PATTERN.findall(text)
    # Strip trailing punctuation that might have been captured
    cleaned = []
    for url in urls:
        # Remove trailing punctuation like . , ; : ! ? 
        while url and url[-1] in '.,:;!?':
            url = url[:-1]
        if url:
            cleaned.append(url)
    return cleaned


def extract_upi_ids(text: str) -> List[str]:
    """Extract all UPI IDs from text."""
    matches = UPI_PATTERN.findall(text)
    # Filter out common email domains to avoid false positives
    email_domains = {'gmail', 'yahoo', 'hotmail', 'outlook', 'mail', 'email'}
    return [m for m in matches if m.split('@')[1].lower() not in email_domains]


def extract_phone_numbers(text: str) -> List[str]:
    """Extract all phone numbers from text."""
    matches = PHONE_PATTERN.findall(text)
    # Normalize format: remove spaces/dashes, ensure +91 prefix
    normalized = []
    for match in matches:
        clean = re.sub(r'[-\s]', '', match)
        if not clean.startswith('+91') and not clean.startswith('0'):
            clean = '+91' + clean
        elif clean.startswith('0'):
            clean = '+91' + clean[1:]
        normalized.append(clean)
    return normalized


def extract_bank_accounts(text: str, phone_numbers: List[str] = None) -> List[str]:
    """Extract potential bank account numbers from text."""
    # Only return if there's context suggesting it's a bank account
    context_keywords = ['account', 'a/c', 'acc', 'transfer', 'neft', 'imps', 'rtgs']
    text_lower = text.lower()
    
    if any(kw in text_lower for kw in context_keywords):
        matches = BANK_ACCOUNT_PATTERN.findall(text)
        
        # Filter out phone numbers if provided
        if phone_numbers:
            # Normalize phone numbers for comparison (remove +91, 0 prefix)
            phone_digits = set()
            for phone in phone_numbers:
                digits = re.sub(r'[^\d]', '', phone)
                if digits.startswith('91'):
                    digits = digits[2:]
                phone_digits.add(digits)
            
            matches = [m for m in matches if m not in phone_digits and m[1:] not in phone_digits]
        
        return matches
    return []


def extract_emails(text: str) -> List[str]:
    """Extract all email addresses from text."""
    return EMAIL_PATTERN.findall(text)


def extract_suspicious_keywords(text: str) -> List[str]:
    """Extract all suspicious keywords from text."""
    matches = SUSPICIOUS_KEYWORDS_PATTERN.findall(text)
    # Return unique, lowercase keywords
    return list(set(kw.lower() for kw in matches))
