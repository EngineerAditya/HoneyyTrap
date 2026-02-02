"""
Link Analyzer - Enhanced URL Safety Checker

This module analyzes URLs to determine if they are potentially malicious/phishing.
Uses WHOIS data, web reputation checks, and India-specific institutional rules.

Enhanced Features:
- Institutional validation (.bank.in, .gov.in rules)
- Subdomain masking detection
- Typosquatting detection
- Enhanced TLD risk scoring
"""

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from difflib import SequenceMatcher
from enum import Enum
from typing import Optional, List
from urllib.parse import urlparse

# These imports will be available after installing dependencies
try:
    import whois
    WHOIS_AVAILABLE = True
except ImportError:
    WHOIS_AVAILABLE = False

try:
    from duckduckgo_search import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    DDGS_AVAILABLE = False

try:
    import tldextract
    TLDEXTRACT_AVAILABLE = True
except ImportError:
    TLDEXTRACT_AVAILABLE = False


class RiskLevel(str, Enum):
    """Risk levels for analyzed URLs."""
    SAFE = "SAFE"
    SUSPICIOUS = "SUSPICIOUS"
    HIGH_RISK = "HIGH_RISK"
    CRITICAL = "CRITICAL"  # Institutional rule violation
    UNKNOWN = "UNKNOWN"  # When we can't determine


@dataclass
class LinkRiskReport:
    """Report containing risk assessment for a URL."""
    url: str
    risk: RiskLevel
    reasons: List[str]
    domain: str
    etld_plus_one: str = ""  # Effective TLD+1 (real domain)
    domain_age_days: Optional[int] = None
    creation_date: Optional[str] = None
    checks_performed: List[str] = field(default_factory=list)


class LinkAnalyzer:
    """
    Analyzes URLs for phishing/malware indicators.
    
    Enhanced Checks:
    1. Institutional Rules: .bank.in for banks, .gov.in for government
    2. Subdomain Masking: Detect sbi.bank.in.fake-site.com tricks
    3. Typosquatting: Detect sbi-bank.in, hdlc.com (similar to hdfc)
    4. Shady TLDs: .xyz, .vip, .top, etc.
    5. Domain Age: WHOIS lookup for creation date
    6. Web Reputation: DuckDuckGo search for scam reports
    """
    
    # === INSTITUTIONAL RULES (India-specific) ===
    BANK_KEYWORDS = {
        'hdfc', 'sbi', 'icici', 'axis', 'kotak', 'pnb', 'bob', 'canara',
        'union', 'idbi', 'yes', 'indusind', 'federal', 'rbl', 'bandhan',
        'bank', 'banking', 'netbanking', 'account'
    }
    REQUIRED_BANK_TLD = '.bank.in'
    
    GOVT_KEYWORDS = {
        'fine', 'fines', 'tax', 'taxes', 'challan', 'echallan', 'legal',
        'notice', 'court', 'police', 'rbi', 'sebi', 'customs', 'income',
        'government', 'ministry', 'aadhaar', 'pan', 'gst'
    }
    REQUIRED_GOVT_TLD = '.gov.in'
    
    # === SHADY TLDs ===
    HIGH_RISK_TLDS = {
        'xyz', 'vip', 'top', 'buzz', 'live', 'icu', 'tk', 'ml', 'cf', 'ga', 'gq',
        'click', 'link', 'work', 'site', 'website', 'online', 'club', 'zip', 'mov'
    }
    
    CONDITIONAL_RISK_TLDS = {'support', 'help', 'info'}
    
    URGENCY_KEYWORDS = {
        'blocked', 'suspended', 'immediate', 'immediately', 'urgent', 'urgently',
        'expire', 'expired', 'verify', 'verification', 'action', 'required',
        'warning', 'alert', 'attention'
    }
    
    # === KNOWN BRANDS (for typosquatting) ===
    KNOWN_BRANDS = {
        'sbi', 'hdfc', 'icici', 'axis', 'kotak', 'pnb', 'canara', 'bob',
        'paytm', 'phonepe', 'gpay', 'amazon', 'flipkart', 'google',
        'facebook', 'whatsapp', 'instagram', 'microsoft', 'apple'
    }
    
    # === TRUSTED DOMAINS (whitelist) ===
    TRUSTED_DOMAINS = {
        # Tech giants
        'google.com', 'facebook.com', 'amazon.com', 'microsoft.com',
        'apple.com', 'github.com', 'youtube.com', 'twitter.com',
        'linkedin.com', 'instagram.com', 'whatsapp.com',
        # Indian banks (.bank.in)
        'sbi.bank.in', 'hdfc.bank.in', 'icici.bank.in', 'axis.bank.in',
        'kotak.bank.in', 'pnb.bank.in',
        # Indian banks (legacy domains - still valid)
        'onlinesbi.sbi', 'hdfcbank.com', 'icicibank.com', 'axisbank.com',
        'kotak.com', 'pnb.com',
        # Payment services
        'paytm.com', 'phonepe.com', 'npci.org.in',
        # Government
        'gov.in', 'nic.in', 'incometax.gov.in', 'parivahan.gov.in',
        'echallan.parivahan.gov.in'
    }
    
    # === SCAM KEYWORDS for web search ===
    SCAM_KEYWORDS = {
        'scam', 'fraud', 'fake', 'phishing', 'malware', 'spam',
        'dangerous', 'warning', 'avoid', 'beware', 'alert',
        'cybercrime', 'hacked', 'stolen'
    }
    
    def __init__(self, enable_whois: bool = True, enable_web_search: bool = True):
        """
        Initialize the LinkAnalyzer.
        
        Args:
            enable_whois: Whether to perform WHOIS lookups
            enable_web_search: Whether to search the web for reputation
        """
        self.enable_whois = enable_whois and WHOIS_AVAILABLE
        self.enable_web_search = enable_web_search and DDGS_AVAILABLE
    
    def analyze(self, url: str, message_context: str = "") -> LinkRiskReport:
        """
        Analyze a URL and return a risk report.
        
        Args:
            url: The URL to analyze
            message_context: The full message text for context-aware analysis
            
        Returns:
            LinkRiskReport with risk assessment
        """
        reasons = []
        checks_performed = []
        risk = RiskLevel.SAFE
        domain_age = None
        creation_date_str = None
        
        # Parse the URL
        try:
            parsed = urlparse(url)
            full_domain = parsed.netloc.lower()
            # Remove www. prefix
            if full_domain.startswith('www.'):
                full_domain = full_domain[4:]
        except Exception:
            return LinkRiskReport(
                url=url,
                risk=RiskLevel.UNKNOWN,
                reasons=["Could not parse URL"],
                domain="",
                checks_performed=["URL parsing"]
            )
        
        # Extract eTLD+1 (the REAL domain)
        etld_plus_one = self._extract_etld_plus_one(full_domain)
        checks_performed.append("eTLD+1 extraction")
        
        # Check 1: Is it a trusted domain?
        if etld_plus_one in self.TRUSTED_DOMAINS or full_domain in self.TRUSTED_DOMAINS:
            return LinkRiskReport(
                url=url,
                risk=RiskLevel.SAFE,
                reasons=["Known trusted domain"],
                domain=full_domain,
                etld_plus_one=etld_plus_one,
                checks_performed=["Trusted domain whitelist"]
            )
        
        # Check 2: Institutional Rules (CRITICAL)
        checks_performed.append("Institutional rules")
        inst_risk, inst_reason = self._check_institutional_rules(etld_plus_one, message_context)
        if inst_reason:
            reasons.append(inst_reason)
            risk = self._max_risk(risk, inst_risk)
        
        # Check 3: Subdomain Masking (CRITICAL)
        checks_performed.append("Subdomain masking")
        mask_risk, mask_reason = self._check_subdomain_masking(full_domain, etld_plus_one)
        if mask_reason:
            reasons.append(mask_reason)
            risk = self._max_risk(risk, mask_risk)
        
        # Check 4: Typosquatting
        checks_performed.append("Typosquatting detection")
        typo_risk, typo_reason = self._check_typosquatting(full_domain)
        if typo_reason:
            reasons.append(typo_reason)
            risk = self._max_risk(risk, typo_risk)
        
        # Check 5: IP address instead of domain
        checks_performed.append("IP address check")
        if self._is_ip_address(full_domain):
            reasons.append("URL uses IP address instead of domain name")
            risk = self._max_risk(risk, RiskLevel.HIGH_RISK)
        
        # Check 6: Shady TLD
        checks_performed.append("TLD risk analysis")
        tld = full_domain.split('.')[-1] if '.' in full_domain else ''
        if tld in self.HIGH_RISK_TLDS:
            reasons.append(f"High-risk TLD: .{tld}")
            risk = self._max_risk(risk, RiskLevel.HIGH_RISK)
        elif tld in self.CONDITIONAL_RISK_TLDS:
            # Only flag if message has urgency keywords
            if any(kw in message_context.lower() for kw in self.URGENCY_KEYWORDS):
                reasons.append(f"Suspicious TLD .{tld} with urgency context")
                risk = self._max_risk(risk, RiskLevel.SUSPICIOUS)
        
        # Check 7: Very long subdomain
        if full_domain.count('.') > 3:
            reasons.append("Unusually deep subdomain structure")
            risk = self._max_risk(risk, RiskLevel.SUSPICIOUS)
        
        # Check 8: WHOIS - Domain age
        if self.enable_whois:
            checks_performed.append("WHOIS domain age")
            age_result = self._check_domain_age(etld_plus_one)
            if age_result:
                domain_age, creation_date_str, age_risk, age_reason = age_result
                if age_reason:
                    reasons.append(age_reason)
                    risk = self._max_risk(risk, age_risk)
        
        # Check 9: Web reputation (skip if already critical)
        if self.enable_web_search and risk not in (RiskLevel.CRITICAL, RiskLevel.HIGH_RISK):
            checks_performed.append("Web reputation search")
            rep_risk, rep_reason = self._check_web_reputation(etld_plus_one)
            if rep_reason:
                reasons.append(rep_reason)
                risk = self._max_risk(risk, rep_risk)
        
        # If no issues found
        if not reasons:
            reasons.append("No obvious indicators found")
        
        return LinkRiskReport(
            url=url,
            risk=risk,
            reasons=reasons,
            domain=full_domain,
            etld_plus_one=etld_plus_one,
            domain_age_days=domain_age,
            creation_date=creation_date_str,
            checks_performed=checks_performed
        )
    
    def _max_risk(self, current: RiskLevel, new: RiskLevel) -> RiskLevel:
        """Return the higher risk level."""
        order = [RiskLevel.SAFE, RiskLevel.UNKNOWN, RiskLevel.SUSPICIOUS, 
                 RiskLevel.HIGH_RISK, RiskLevel.CRITICAL]
        return max(current, new, key=lambda x: order.index(x))
    
    def _extract_etld_plus_one(self, domain: str) -> str:
        """Extract the effective TLD+1 (real domain) using tldextract."""
        if TLDEXTRACT_AVAILABLE:
            ext = tldextract.extract(domain)
            if ext.suffix:
                return f"{ext.domain}.{ext.suffix}"
            return ext.domain
        else:
            # Fallback to simple extraction
            return self._get_root_domain_fallback(domain)
    
    def _get_root_domain_fallback(self, domain: str) -> str:
        """Fallback root domain extraction without tldextract."""
        parts = domain.split('.')
        if len(parts) >= 2:
            # Handle .co.in, .com.au, .bank.in, .gov.in etc.
            if len(parts) >= 3 and parts[-2] in ('co', 'com', 'org', 'net', 'gov', 'ac', 'bank'):
                return '.'.join(parts[-3:])
            return '.'.join(parts[-2:])
        return domain
    
    def _check_institutional_rules(self, etld_plus_one: str, message: str) -> tuple:
        """
        Check institutional validation rules.
        
        Banking context: Must use .bank.in
        Government context: Must use .gov.in
        """
        message_lower = message.lower()
        
        # Banking Rule
        if any(bank in message_lower for bank in self.BANK_KEYWORDS):
            if not etld_plus_one.endswith('.bank.in'):
                # Check if it's a known legacy bank domain
                legacy_banks = {'hdfcbank.com', 'icicibank.com', 'axisbank.com', 
                               'kotak.com', 'onlinesbi.sbi'}
                if etld_plus_one not in legacy_banks:
                    return (RiskLevel.CRITICAL, 
                            f"Bank context but URL is not .bank.in (domain: {etld_plus_one})")
        
        # Government Rule
        if any(kw in message_lower for kw in self.GOVT_KEYWORDS):
            if not etld_plus_one.endswith('.gov.in'):
                return (RiskLevel.CRITICAL,
                        f"Government/legal context but URL is not .gov.in (domain: {etld_plus_one})")
        
        return (RiskLevel.SAFE, None)
    
    def _check_subdomain_masking(self, full_domain: str, etld_plus_one: str) -> tuple:
        """
        Detect subdomain masking attacks.
        
        Example: sbi.bank.in.verify-kyc.com
        Real domain is verify-kyc.com, but subdomain looks like sbi.bank.in
        """
        # Get the subdomain part
        if etld_plus_one and full_domain != etld_plus_one:
            subdomain = full_domain.replace(etld_plus_one, '').rstrip('.')
            
            # Check for trusted-looking patterns in subdomain
            trusted_patterns = ['.bank.in', '.gov.in', 'sbi', 'hdfc', 'icici', 
                               'axis', 'paytm', 'phonepe']
            
            for pattern in trusted_patterns:
                if pattern in subdomain:
                    return (RiskLevel.CRITICAL,
                            f"Subdomain masking: '{pattern}' in subdomain but real domain is '{etld_plus_one}'")
        
        return (RiskLevel.SAFE, None)
    
    def _check_typosquatting(self, domain: str) -> tuple:
        """
        Detect typosquatting attempts.
        
        - Hyphenated brands: sbi-bank.in
        - Similar spellings: hdlc.com (similar to hdfc)
        """
        domain_lower = domain.lower()
        domain_parts = domain_lower.replace('-', '.').split('.')
        
        # Check for hyphenated brand names
        for brand in self.KNOWN_BRANDS:
            hyphenated = f"{brand}-"
            if hyphenated in domain_lower:
                return (RiskLevel.HIGH_RISK,
                        f"Hyphenated brand name: '{brand}-' in domain")
        
        # Check for similar spellings (typosquatting)
        for part in domain_parts:
            if len(part) < 3:
                continue
            for brand in self.KNOWN_BRANDS:
                if part == brand:
                    continue  # Exact match is fine
                
                # Check similarity
                ratio = SequenceMatcher(None, part, brand).ratio()
                if 0.7 < ratio < 1.0:
                    return (RiskLevel.HIGH_RISK,
                            f"Possible typosquatting: '{part}' similar to '{brand}' ({int(ratio*100)}% match)")
        
        return (RiskLevel.SAFE, None)
    
    def _is_ip_address(self, domain: str) -> bool:
        """Check if domain is an IP address."""
        # IPv4 check
        ipv4_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if re.match(ipv4_pattern, domain):
            return True
        # IPv6 check (simplified)
        if ':' in domain:
            return True
        return False
    
    def _check_domain_age(self, domain: str) -> Optional[tuple]:
        """
        Check domain age via WHOIS.
        
        Returns:
            Tuple of (age_days, creation_date_str, risk_level, reason) or None
        """
        try:
            w = whois.whois(domain)
            creation_date = w.creation_date
            
            # Handle list (some WHOIS servers return multiple dates)
            if isinstance(creation_date, list):
                creation_date = creation_date[0]
            
            if creation_date:
                # Make timezone-aware if needed
                if creation_date.tzinfo is None:
                    creation_date = creation_date.replace(tzinfo=timezone.utc)
                
                now = datetime.now(timezone.utc)
                age_days = (now - creation_date).days
                creation_date_str = creation_date.strftime("%Y-%m-%d")
                
                if age_days < 30:
                    return (age_days, creation_date_str, RiskLevel.HIGH_RISK, 
                            f"Domain created only {age_days} days ago (registered: {creation_date_str})")
                elif age_days < 90:
                    return (age_days, creation_date_str, RiskLevel.SUSPICIOUS,
                            f"Domain is relatively new ({age_days} days old, registered: {creation_date_str})")
                else:
                    return (age_days, creation_date_str, RiskLevel.SAFE, None)
        except Exception as e:
            print(f"[LinkAnalyzer] WHOIS lookup failed for {domain}: {e}")
        
        return None
    
    def _check_web_reputation(self, domain: str) -> tuple:
        """
        Search the web for scam reports about this domain.
        
        Returns:
            Tuple of (risk_level, reason) or (SAFE, None) if clean
        """
        try:
            ddgs = DDGS()
            query = f'"{domain}" scam OR fraud OR phishing'
            results = list(ddgs.text(query, max_results=5))
            
            # Check if any results mention scam keywords
            scam_mentions = 0
            for result in results:
                text = (result.get('title', '') + ' ' + result.get('body', '')).lower()
                if any(kw in text for kw in self.SCAM_KEYWORDS):
                    scam_mentions += 1
            
            if scam_mentions >= 2:
                return (RiskLevel.HIGH_RISK, 
                        f"Multiple scam reports found online ({scam_mentions} sources)")
            elif scam_mentions == 1:
                return (RiskLevel.SUSPICIOUS,
                        "Some negative reports found online")
        except Exception as e:
            print(f"[LinkAnalyzer] Web search failed for {domain}: {e}")
        
        return (RiskLevel.SAFE, None)
