"""
Intelligence Extraction Module

This module provides comprehensive intelligence extraction for scam detection:
- Regex-based entity extraction (UPI, phone, links, etc.)
- Enhanced URL phishing analysis
- Scam classification and confidence scoring
- Session-based intelligence aggregation
"""

from .patterns import (
    extract_urls,
    extract_upi_ids,
    extract_phone_numbers,
    extract_bank_accounts,
    extract_emails,
    extract_suspicious_keywords,
)

from .link_analyzer import (
    LinkAnalyzer,
    LinkRiskReport,
    RiskLevel,
)

from .classifier import (
    ScamClassifier,
    ScamAnalysis,
    ScamType,
    UrgencyLevel,
)

from .extractor import IntelligenceExtractor

from .session_store import (
    SessionStore,
    SessionIntelligence,
    session_store,  # Global instance
)


__all__ = [
    # Patterns
    "extract_urls",
    "extract_upi_ids",
    "extract_phone_numbers",
    "extract_bank_accounts",
    "extract_emails",
    "extract_suspicious_keywords",
    # Link Analysis
    "LinkAnalyzer",
    "LinkRiskReport",
    "RiskLevel",
    # Classification
    "ScamClassifier",
    "ScamAnalysis",
    "ScamType",
    "UrgencyLevel",
    # Extraction
    "IntelligenceExtractor",
    # Session
    "SessionStore",
    "SessionIntelligence",
    "session_store",
]
