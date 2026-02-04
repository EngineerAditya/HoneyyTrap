"""
Intelligence Extractor - Main Orchestrator

This module orchestrates the extraction of scam indicators from messages.
It uses patterns.py for regex extraction and link_analyzer.py for URL validation.
"""

from typing import Dict, List, Any

from .patterns import (
    extract_urls,
    extract_upi_ids,
    extract_phone_numbers,
    extract_bank_accounts,
    extract_emails,
    extract_suspicious_keywords
)
from .link_analyzer import LinkAnalyzer, RiskLevel


class IntelligenceExtractor:
    """
    Main orchestrator for intelligence extraction.
    
    Extracts:
    - Bank accounts
    - UPI IDs
    - Phone numbers
    - URLs (with phishing analysis)
    - Suspicious keywords
    - Emails (for LLM context)
    """
    
    def __init__(self, enable_link_analysis: bool = True):
        """
        Initialize the extractor.
        
        Args:
            enable_link_analysis: Whether to perform deep link analysis
        """
        self.link_analyzer = LinkAnalyzer() if enable_link_analysis else None
    
    def extract(self, text: str) -> Dict[str, Any]:
        """
        Extract all intelligence from a text message.
        
        Args:
            text: The message text to analyze
            
        Returns:
            Dictionary with extracted intelligence
        """
        # Extract all entities using regex
        urls = extract_urls(text)
        upi_ids = extract_upi_ids(text)
        phone_numbers = extract_phone_numbers(text)
        bank_accounts = extract_bank_accounts(text, phone_numbers)  # Pass phones to avoid false positives
        emails = extract_emails(text)
        keywords = extract_suspicious_keywords(text)
        
        # Analyze URLs for phishing (pass message context for institutional rules)
        phishing_links = []
        link_reports = []
        
        if self.link_analyzer and urls:
            for url in urls:
                report = self.link_analyzer.analyze(url, message_context=text)
                link_reports.append({
                    "url": report.url,
                    "risk": report.risk.value,
                    "reasons": report.reasons,
                    "domain": report.domain,
                    "etld_plus_one": report.etld_plus_one,
                    "domain_age_days": report.domain_age_days,
                    "creation_date": report.creation_date,
                    "checks_performed": report.checks_performed
                })
                
                # Add to phishing links if risky (including CRITICAL)
                if report.risk in (RiskLevel.CRITICAL, RiskLevel.HIGH_RISK, RiskLevel.SUSPICIOUS):
                    phishing_links.append(url)
        
        return {
            "bankAccounts": bank_accounts,
            "upiIds": upi_ids,
            "phishingLinks": phishing_links,
            "phoneNumbers": phone_numbers,
            "suspiciousKeywords": keywords,
            "emails": emails,
            "allLinks": urls,
            "linkReports": link_reports  # Detailed reports for logging/LLM
        }
    
    def extract_from_history(self, messages: List[Dict]) -> Dict[str, Any]:
        """
        Extract intelligence from conversation history.
        
        Args:
            messages: List of message dictionaries with 'text' field
            
        Returns:
            Aggregated intelligence dictionary
        """
        aggregated = {
            "bankAccounts": [],
            "upiIds": [],
            "phishingLinks": [],
            "phoneNumbers": [],
            "suspiciousKeywords": [],
            "emails": [],
            "allLinks": [],
            "linkReports": []
        }
        
        for msg in messages:
            text = msg.get("text", "")
            intel = self.extract(text)
            
            # Aggregate without duplicates
            for key in aggregated:
                if key == "linkReports":
                    aggregated[key].extend(intel.get(key, []))
                else:
                    existing = set(aggregated[key])
                    existing.update(intel.get(key, []))
                    aggregated[key] = list(existing)
        
        return aggregated
    
    def get_summary(self, intel: Dict[str, Any]) -> str:
        """
        Generate a human-readable summary of extracted intelligence.
        
        Args:
            intel: The intelligence dictionary
            
        Returns:
            Summary string
        """
        parts = []
        
        if intel.get("upiIds"):
            parts.append(f"UPI IDs: {', '.join(intel['upiIds'])}")
        if intel.get("phoneNumbers"):
            parts.append(f"Phone numbers: {', '.join(intel['phoneNumbers'])}")
        if intel.get("bankAccounts"):
            parts.append(f"Bank accounts: {', '.join(intel['bankAccounts'])}")
        if intel.get("phishingLinks"):
            parts.append(f"Suspicious links: {', '.join(intel['phishingLinks'])}")
        if intel.get("suspiciousKeywords"):
            parts.append(f"Keywords: {', '.join(intel['suspiciousKeywords'])}")
        
        return "; ".join(parts) if parts else "No scam indicators found"
