"""
Scam Classifier - Scam Type Detection and Confidence Scoring

This module provides:
1. Dynamic confidence scoring (0-100)
2. Scam type classification
3. Urgency level detection
4. Threat and impersonation detection
"""

from enum import Enum
from typing import Dict, List, Optional, Set
from dataclasses import dataclass


class ScamType(str, Enum):
    """Types of scams detected."""
    BANK_FRAUD = "bank_fraud"           # Account blocked, KYC update
    UPI_FRAUD = "upi_fraud"             # Pay to this UPI
    PHISHING = "phishing"               # Click this link
    LOTTERY_SCAM = "lottery_scam"       # You won a prize
    JOB_SCAM = "job_scam"               # Work from home offer
    TECH_SUPPORT = "tech_support"       # Device infected
    IMPERSONATION = "impersonation"     # I'm from RBI/Police
    LOAN_SCAM = "loan_scam"             # Pre-approved loan
    UNKNOWN = "unknown"


class UrgencyLevel(str, Enum):
    """Urgency level in scam message."""
    HIGH = "high"       # Immediate action required
    MEDIUM = "medium"   # Time pressure but not immediate
    LOW = "low"         # No time pressure


@dataclass
class ScamAnalysis:
    """Complete scam analysis result."""
    scam_type: ScamType
    confidence: int  # 0-100
    urgency: UrgencyLevel
    impersonating: Optional[str]  # "SBI", "RBI", "Police", etc.
    threats: List[str]  # ["account blocked", "legal action"]
    asks_for: List[str]  # ["OTP", "UPI ID", "bank details"]
    
    def to_dict(self) -> dict:
        return {
            "scamType": self.scam_type.value,
            "confidence": self.confidence,
            "urgency": self.urgency.value,
            "impersonating": self.impersonating,
            "threats": self.threats,
            "asksFor": self.asks_for
        }


class ScamClassifier:
    """
    Classifies scams and calculates dynamic confidence.
    """
    
    # === SCAM TYPE INDICATORS ===
    BANK_FRAUD_KEYWORDS = {
        'account', 'blocked', 'suspended', 'kyc', 'verify', 'netbanking',
        'debit card', 'credit card', 'atm', 'branch', 'ifsc'
    }
    
    UPI_FRAUD_KEYWORDS = {
        'upi', 'paytm', 'phonepe', 'gpay', 'google pay', 'bhim',
        'send money', 'transfer', 'payment', 'pay now', 'collect'
    }
    
    PHISHING_KEYWORDS = {
        'click', 'link', 'verify', 'login', 'password', 'update',
        'confirm', 'secure', 'validate'
    }
    
    LOTTERY_KEYWORDS = {
        'won', 'winner', 'prize', 'lottery', 'lucky', 'congratulations',
        'claim', 'reward', 'gift', 'free', 'cashback'
    }
    
    JOB_SCAM_KEYWORDS = {
        'job', 'work from home', 'earn', 'income', 'salary', 'offer',
        'hiring', 'vacancy', 'part time', 'full time', 'wfh'
    }
    
    TECH_SUPPORT_KEYWORDS = {
        'virus', 'infected', 'hacked', 'malware', 'security', 'computer',
        'device', 'phone', 'sim', 'locked', 'compromised'
    }
    
    LOAN_SCAM_KEYWORDS = {
        'loan', 'pre-approved', 'sanction', 'emi', 'interest', 'credit',
        'disbursement', 'processing fee'
    }
    
    # === IMPERSONATION TARGETS ===
    IMPERSONATION_ENTITIES = {
        # Banks
        'sbi': 'SBI (State Bank of India)',
        'hdfc': 'HDFC Bank',
        'icici': 'ICICI Bank',
        'axis': 'Axis Bank',
        'kotak': 'Kotak Mahindra Bank',
        'pnb': 'Punjab National Bank',
        # Government
        'rbi': 'RBI (Reserve Bank of India)',
        'income tax': 'Income Tax Department',
        'customs': 'Customs Department',
        'police': 'Police',
        'cyber cell': 'Cyber Crime Cell',
        'court': 'Court',
        # Services
        'paytm': 'Paytm',
        'phonepe': 'PhonePe',
        'amazon': 'Amazon',
        'flipkart': 'Flipkart',
    }
    
    # === THREATS ===
    THREAT_PATTERNS = [
        'account will be blocked',
        'account blocked',
        'account suspended',
        'legal action',
        'police case',
        'arrest',
        'fir',
        'court notice',
        'penalty',
        'fine',
        'freeze',
        'deactivate',
        'terminate',
        'close your account',
        'jail',
        'prosecution'
    ]
    
    # === ASKS FOR ===
    ASKS_FOR_PATTERNS = {
        'otp': 'OTP',
        'pin': 'PIN',
        'password': 'Password',
        'cvv': 'CVV',
        'card number': 'Card Number',
        'account number': 'Account Number',
        'upi id': 'UPI ID',
        'upi pin': 'UPI PIN',
        'bank details': 'Bank Details',
        'aadhaar': 'Aadhaar Number',
        'pan': 'PAN Card',
        'send money': 'Money Transfer',
        'pay': 'Payment',
        'transfer': 'Money Transfer',
        'click': 'Link Click',
        'verify': 'Verification',
    }
    
    # === URGENCY INDICATORS ===
    HIGH_URGENCY = {
        'immediately', 'now', 'urgent', 'asap', 'hurry', 'quick',
        'within 24 hours', 'today', 'right now', 'instant'
    }
    
    MEDIUM_URGENCY = {
        'soon', 'as soon as possible', 'at the earliest', 'before',
        'deadline', 'expire', 'last chance'
    }
    
    def classify(self, text: str, intel: dict) -> ScamAnalysis:
        """
        Analyze text and intelligence to classify scam.
        
        Args:
            text: Combined message text (current + history)
            intel: Extracted intelligence dictionary
            
        Returns:
            ScamAnalysis with type, confidence, urgency, etc.
        """
        text_lower = text.lower()
        
        # Detect scam type
        scam_type = self._detect_scam_type(text_lower, intel)
        
        # Calculate confidence
        confidence = self._calculate_confidence(text_lower, intel)
        
        # Detect urgency
        urgency = self._detect_urgency(text_lower)
        
        # Detect impersonation
        impersonating = self._detect_impersonation(text_lower)
        
        # Detect threats
        threats = self._detect_threats(text_lower)
        
        # Detect what scammer asks for
        asks_for = self._detect_asks_for(text_lower)
        
        return ScamAnalysis(
            scam_type=scam_type,
            confidence=confidence,
            urgency=urgency,
            impersonating=impersonating,
            threats=threats,
            asks_for=asks_for
        )
    
    def _detect_scam_type(self, text: str, intel: dict) -> ScamType:
        """Detect the type of scam based on keywords and intel."""
        scores = {
            ScamType.BANK_FRAUD: 0,
            ScamType.UPI_FRAUD: 0,
            ScamType.PHISHING: 0,
            ScamType.LOTTERY_SCAM: 0,
            ScamType.JOB_SCAM: 0,
            ScamType.TECH_SUPPORT: 0,
            ScamType.LOAN_SCAM: 0,
        }
        
        # Keyword matching
        for kw in self.BANK_FRAUD_KEYWORDS:
            if kw in text: scores[ScamType.BANK_FRAUD] += 1
        for kw in self.UPI_FRAUD_KEYWORDS:
            if kw in text: scores[ScamType.UPI_FRAUD] += 1
        for kw in self.PHISHING_KEYWORDS:
            if kw in text: scores[ScamType.PHISHING] += 1
        for kw in self.LOTTERY_KEYWORDS:
            if kw in text: scores[ScamType.LOTTERY_SCAM] += 1
        for kw in self.JOB_SCAM_KEYWORDS:
            if kw in text: scores[ScamType.JOB_SCAM] += 1
        for kw in self.TECH_SUPPORT_KEYWORDS:
            if kw in text: scores[ScamType.TECH_SUPPORT] += 1
        for kw in self.LOAN_SCAM_KEYWORDS:
            if kw in text: scores[ScamType.LOAN_SCAM] += 1
        
        # Intel-based boosting
        if intel.get("upiIds"): scores[ScamType.UPI_FRAUD] += 3
        if intel.get("phishingLinks"): scores[ScamType.PHISHING] += 3
        if intel.get("bankAccounts"): scores[ScamType.BANK_FRAUD] += 2
        
        # Get highest scoring type
        max_type = max(scores.items(), key=lambda x: x[1])
        if max_type[1] > 0:
            return max_type[0]
        return ScamType.UNKNOWN
    
    def _calculate_confidence(self, text: str, intel: dict) -> int:
        """
        Calculate dynamic confidence score (0-100).
        
        Scoring:
        - Phishing links (especially CRITICAL): +40
        - UPI IDs: +25
        - Phone numbers: +10
        - Bank accounts: +15
        - Suspicious keywords: +5 each (max 25)
        - Threats detected: +15
        - Impersonation: +10
        - Urgency: +5-10
        """
        score = 0
        
        # Intel-based scoring
        if intel.get("phishingLinks"):
            score += 30
            # Check for CRITICAL links
            for report in intel.get("linkReports", []):
                if report.get("risk") == "CRITICAL":
                    score += 15
                    break
        
        if intel.get("upiIds"):
            score += 25
        
        if intel.get("phoneNumbers"):
            score += 10
        
        if intel.get("bankAccounts"):
            score += 15
        
        # Keywords (capped at 25)
        keyword_score = len(intel.get("suspiciousKeywords", [])) * 5
        score += min(keyword_score, 25)
        
        # Threats
        threats = self._detect_threats(text)
        if threats:
            score += 15
        
        # Impersonation
        if self._detect_impersonation(text):
            score += 10
        
        # Urgency
        urgency = self._detect_urgency(text)
        if urgency == UrgencyLevel.HIGH:
            score += 10
        elif urgency == UrgencyLevel.MEDIUM:
            score += 5
        
        return min(max(score, 0), 100)
    
    def _detect_urgency(self, text: str) -> UrgencyLevel:
        """Detect urgency level in message."""
        if any(kw in text for kw in self.HIGH_URGENCY):
            return UrgencyLevel.HIGH
        if any(kw in text for kw in self.MEDIUM_URGENCY):
            return UrgencyLevel.MEDIUM
        return UrgencyLevel.LOW
    
    def _detect_impersonation(self, text: str) -> Optional[str]:
        """Detect if scammer is impersonating an entity."""
        for keyword, entity in self.IMPERSONATION_ENTITIES.items():
            if keyword in text:
                return entity
        return None
    
    def _detect_threats(self, text: str) -> List[str]:
        """Detect threats in message."""
        threats = []
        for pattern in self.THREAT_PATTERNS:
            if pattern in text:
                threats.append(pattern)
        return threats
    
    def _detect_asks_for(self, text: str) -> List[str]:
        """Detect what information scammer is asking for."""
        asks = []
        for pattern, label in self.ASKS_FOR_PATTERNS.items():
            if pattern in text:
                if label not in asks:
                    asks.append(label)
        return asks
