"""
Service for handling LLM interactions.
"""
import json
import requests
import time
import random
import re
import yaml
import os
from typing import Dict, Any, Optional
from enum import Enum
from config_loader import get_llm_config
from security_manager import security_manager, security_logger, sanitize_streamlit_output

class CircuitBreakerState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit is open, rejecting requests
    HALF_OPEN = "half_open"  # Testing if service is back

class CircuitBreaker:
    """
    Circuit breaker pattern implementation for API calls.
    
    Prevents cascade failures by temporarily blocking requests
    when the service is experiencing high failure rates.
    """
    
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            timeout: Seconds to wait before attempting to close circuit
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = CircuitBreakerState.CLOSED
    
    def can_execute(self) -> bool:
        """Check if request can be executed."""
        if self.state == CircuitBreakerState.CLOSED:
            return True
        elif self.state == CircuitBreakerState.OPEN:
            if time.time() - self.last_failure_time >= self.timeout:
                self.state = CircuitBreakerState.HALF_OPEN
                return True
            return False
        else:  # HALF_OPEN
            return True
    
    def record_success(self):
        """Record a successful operation."""
        self.failure_count = 0
        self.state = CircuitBreakerState.CLOSED
    
    def record_failure(self):
        """Record a failed operation."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN

def retry_with_exponential_backoff(max_retries: int = 3, base_delay: float = 1.0):
    """
    Decorator for retry logic with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds for exponential backoff
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    error_text = str(e)

                    if re.search(r"\b(401|403)\b", error_text):
                        security_logger.error(f"API call failed without retry due to authentication/authorization error: {e}")
                        raise
                    
                    if attempt < max_retries:
                        # Exponential backoff with jitter
                        delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                        security_logger.warning(f"API call failed (attempt {attempt + 1}), retrying in {delay:.1f}s: {e}")
                        time.sleep(delay)
                    else:
                        security_logger.error(f"API call failed after {max_retries + 1} attempts: {e}")
            
            raise last_exception
        return wrapper
    return decorator

class PIIScrubber:
    """
    PII scrubbing service for GDPR/CCPA compliance
    
    Removes or masks personally identifiable information before
    sending data to external LLM services.
    """
    
    def __init__(self):
        """Initialize PII scrubber with patterns and replacements from config file"""
        self._load_config()
        self._compile_patterns()
        
    def _load_config(self):
        """Load PII scrubbing configuration from config/pii_config.yaml"""
        config_path = os.path.join(os.path.dirname(__file__), 'config', 'pii_config.yaml')
        
        # Default configuration fallback
        default_config = {
            'pii_scrubbing': {
                'enabled': True,
                'scrub_types': {
                    'emails': True,
                    'phones': True,
                    'ssns': True,
                    'credit_cards': True,
                    'ip_addresses': False,
                    'mac_addresses': False,
                    'names': True,
                    'custom_patterns': []
                },
                'replacements': {
                    'email': '[EMAIL_REDACTED]',
                    'phone': '[PHONE_REDACTED]',
                    'ssn': '[SSN_REDACTED]',
                    'credit_card': '[CREDIT_CARD_REDACTED]',
                    'ip_address': '[IP_REDACTED]',
                    'mac_address': '[MAC_REDACTED]',
                    'name': '[NAME_REDACTED]',
                    'custom': '[PII_REDACTED]'
                }
            },
            'compliance': {
                'log_scrubbing_events': True,
                'gdpr_compliant': True,
                'ccpa_compliant': True
            }
        }
        
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    loaded_config = yaml.safe_load(f)
                    self.config = {**default_config, **loaded_config}
                    security_logger.info(f"Loaded PII scrubbing configuration from {config_path}")
            else:
                self.config = default_config
                security_logger.warning(f"PII config file not found at {config_path}, using defaults")
        except Exception as e:
            security_logger.error(f"Error loading PII config: {e}, using defaults")
            self.config = default_config
        
        # Extract scrubbing configuration for easy access
        self.scrub_config = self.config['pii_scrubbing']['scrub_types']
        self.replacements = self.config['pii_scrubbing']['replacements']
        self.enabled = self.config['pii_scrubbing']['enabled']
        self.log_events = self.config['compliance']['log_scrubbing_events']
        
    def _compile_patterns(self):
        """Compile regex patterns for PII detection"""
        # Email patterns
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        
        # Phone number patterns (US, international)
        self.phone_patterns = [
            re.compile(r'\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b'),
            re.compile(r'\b\+?[1-9]\d{1,14}\b'),  # International format
        ]
        
        # SSN patterns
        self.ssn_pattern = re.compile(r'\b\d{3}-?\d{2}-?\d{4}\b')
        
        # Credit card patterns (basic Luhn algorithm check)
        self.cc_pattern = re.compile(r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3[0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b')
        
        # IP address patterns
        self.ip_pattern = re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b')
        
        # MAC address patterns
        self.mac_pattern = re.compile(r'\b(?:[0-9A-Fa-f]{2}[:-]){5}(?:[0-9A-Fa-f]{2})\b')
        
        # Names that might be PII (common first/last name patterns)
        self.name_patterns = [
            re.compile(r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b'),  # First Last
        ]

        # Additional compliance-oriented patterns for common EU identifiers.
        self.eu_pii_patterns = [
            re.compile(r'\b[A-Z]{2}\d{2}(?:\s?[A-Z0-9]{4}){3,7}\b'),  # IBAN
            re.compile(r'\b[A-Z]{2}\d{9,12}\b'),  # VAT numbers
            re.compile(r'\b[A-Z]{1,2}\d{7,8}\b'),  # Passport numbers
            re.compile(r'\b[A-Z]{5}\d{6}[A-Z]{2}\d[A-Z]{2}\b'),  # UK-style driving licence
        ]
    
    def scrub_text(self, text: str) -> str:
        """
        Scrub PII from text while preserving analytical value
        
        Args:
            text: Input text that may contain PII
            
        Returns:
            Scrubbed text with PII removed/masked
        """
        if not text or not isinstance(text, str):
            return text
        
        # Check if PII scrubbing is globally enabled
        if not self.enabled:
            return text
        
        scrubbed = text
        scrubbed_items = []
        
        # Email scrubbing
        if self.scrub_config.get('emails', True):
            matches = self.email_pattern.findall(scrubbed)
            if matches:
                scrubbed_items.extend(['email'] * len(matches))
                scrubbed = self.email_pattern.sub(self.replacements['email'], scrubbed)
        
        # Phone number scrubbing
        if self.scrub_config.get('phones', True):
            for pattern in self.phone_patterns:
                matches = pattern.findall(scrubbed)
                if matches:
                    scrubbed_items.extend(['phone'] * len(matches))
                    scrubbed = pattern.sub(self.replacements['phone'], scrubbed)
        
        # SSN scrubbing
        if self.scrub_config.get('ssns', True):
            matches = self.ssn_pattern.findall(scrubbed)
            if matches:
                scrubbed_items.extend(['ssn'] * len(matches))
                scrubbed = self.ssn_pattern.sub(self.replacements['ssn'], scrubbed)
        
        # Credit card scrubbing
        if self.scrub_config.get('credit_cards', True):
            matches = self.cc_pattern.findall(scrubbed)
            if matches:
                scrubbed_items.extend(['credit_card'] * len(matches))
                scrubbed = self.cc_pattern.sub(self.replacements['credit_card'], scrubbed)
        
        # IP address scrubbing (optional)
        if self.scrub_config.get('ip_addresses', False):
            matches = self.ip_pattern.findall(scrubbed)
            if matches:
                scrubbed_items.extend(['ip_address'] * len(matches))
                scrubbed = self.ip_pattern.sub(self.replacements['ip_address'], scrubbed)
        
        # MAC address scrubbing (optional)
        if self.scrub_config.get('mac_addresses', False):
            matches = self.mac_pattern.findall(scrubbed)
            if matches:
                scrubbed_items.extend(['mac_address'] * len(matches))
                scrubbed = self.mac_pattern.sub(self.replacements['mac_address'], scrubbed)
        
        # Name scrubbing (optional - very aggressive)
        if self.scrub_config.get('names', False):
            for pattern in self.name_patterns:
                matches = pattern.findall(scrubbed)
                if matches:
                    scrubbed_items.extend(['name'] * len(matches))
                    scrubbed = pattern.sub(self.replacements['name'], scrubbed)

        for pattern in self.eu_pii_patterns:
            matches = pattern.findall(scrubbed)
            if matches:
                scrubbed_items.extend(['custom'] * len(matches))
                scrubbed = pattern.sub(self.replacements['custom'], scrubbed)
        
        # Log scrubbing events for compliance audit trail
        if scrubbed_items and self.log_events:
            pii_types = ', '.join(set(scrubbed_items))
            pii_count = len(scrubbed_items)
            security_logger.info(f"PII scrubbed from text: {pii_count} items ({pii_types}) - GDPR/CCPA compliance")
        
        return scrubbed
    
    def get_config_status(self) -> Dict[str, Any]:
        """
        Get current PII scrubbing configuration status
        
        Returns:
            Dictionary with configuration details for monitoring/documentation
        """
        return {
            'enabled': self.enabled,
            'config_source': 'config/pii_config.yaml' if hasattr(self, 'config') else 'defaults',
            'scrub_types': self.scrub_config.copy(),
            'replacements': self.replacements.copy(),
            'compliance': {
                'gdpr_compliant': self.config.get('compliance', {}).get('gdpr_compliant', True),
                'ccpa_compliant': self.config.get('compliance', {}).get('ccpa_compliant', True),
                'log_scrubbing_events': self.log_events
            }
        }
    
    def scrub_data_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively scrub PII from dictionary data
        
        Args:
            data: Dictionary that may contain PII in values
            
        Returns:
            Dictionary with PII scrubbed from string values
        """
        if not isinstance(data, dict):
            return data
        
        scrubbed_data = {}
        
        for key, value in data.items():
            if isinstance(value, str):
                scrubbed_data[key] = self.scrub_text(value)
            elif isinstance(value, dict):
                scrubbed_data[key] = self.scrub_data_dict(value)
            elif isinstance(value, list):
                scrubbed_data[key] = [
                    self.scrub_text(item) if isinstance(item, str) 
                    else self.scrub_data_dict(item) if isinstance(item, dict)
                    else item
                    for item in value
                ]
            else:
                scrubbed_data[key] = value
        
        return scrubbed_data

class LLMService:
    def __init__(self) -> None:
        self.config: Dict[str, Any] = get_llm_config()
        self.circuit_breaker = CircuitBreaker(failure_threshold=5, timeout=60)
        self.pii_scrubber = PIIScrubber()

    @staticmethod
    def _safe_fallback_response(summary: str, insight: str, trend: str, action: str) -> Dict[str, Any]:
        """Return a schema-stable fallback payload for UI and test callers."""
        return {
            "summary": summary,
            "key_insights": [insight],
            "trends": [trend],
            "recommended_actions": [action],
        }

    @staticmethod
    def _contains_unsafe_response_content(value: str) -> bool:
        patterns = [
            r"<script",
            r"\.\./",
            r"/etc/passwd",
            r"\$\{env\.",
            r"javascript:",
            r"\bsk-[a-z0-9-]+\b",
            r"\bpk-[a-z0-9-]+\b",
            r"postgresql://",
            r"system32\\config\\sam",
            r"\brm\s+-rf\b",
            r"\bapi\s+key\b",
        ]
        return any(re.search(pattern, value, re.IGNORECASE) for pattern in patterns)

    def _normalize_provider_response(self, insights: Dict[str, Any]) -> Dict[str, Any]:
        required_keys = ["summary", "key_insights", "trends", "recommended_actions"]
        if not all(key in insights for key in required_keys):
            security_logger.warning("Incomplete response structure from LLM")
            return self._safe_fallback_response(
                "AI insights are temporarily unavailable because the provider response was incomplete.",
                "The provider returned a partial payload instead of the expected schema.",
                "A schema validation check blocked unsafe provider output.",
                "Retry the request or switch to a verified model configuration."
            )

        summary = str(insights.get("summary", ""))
        if self._contains_unsafe_response_content(summary):
            return self._safe_fallback_response(
                "AI insights were blocked because the provider returned unsafe content.",
                "Unsafe text patterns were removed before the response reached the dashboard.",
                "The provider response triggered output sanitization safeguards.",
                "Retry the request after reviewing the configured model and prompt."
            )

        normalized = {
            "summary": sanitize_streamlit_output(summary),
            "key_insights": [],
            "trends": [],
            "recommended_actions": [],
        }

        for key in ["key_insights", "trends", "recommended_actions"]:
            values = insights.get(key, [])
            if not isinstance(values, list):
                continue
            for value in values:
                if not isinstance(value, str):
                    continue
                if self._contains_unsafe_response_content(value):
                    continue
                normalized[key].append(sanitize_streamlit_output(value))

        return normalized
        
    @retry_with_exponential_backoff(max_retries=3, base_delay=1.0)
    def _make_api_call(self, headers: Dict[str, str], data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make the actual API call with timeout and error handling.
        
        Args:
            headers: HTTP headers for the request
            data: Request payload
            
        Returns:
            API response data
            
        Raises:
            requests.RequestException: If the API call fails
        """
        response = requests.post(
            f"{self.config['api_base']}/chat/completions",
            headers=headers,
            json=data,
            timeout=30  # 30-second timeout
        )
        
        if response.status_code != 200:
            error_msg = f"{response.status_code} - {response.text}"
            raise requests.RequestException(f"API call failed: {error_msg}")
        
        return response.json()

    def generate_insights(self, prompt: str) -> Optional[Dict[str, Any]]:
        """
        Generate insights using the configured LLM with circuit breaker protection.
        
        Args:
            prompt: The prompt to send to the LLM
            
        Returns:
            Dict containing structured insights or None if the call fails
        """
        # Check circuit breaker before attempting call
        if not self.circuit_breaker.can_execute():
            security_logger.warning("Circuit breaker is OPEN - rejecting LLM API request")
            return {
                "summary": "AI Insights temporarily unavailable due to service issues. Please try again later.",
                "key_insights": ["Service is experiencing connectivity issues", "Circuit breaker is active to prevent cascading disruptions"],
                "trends": ["Monitoring system health and service connectivity"],
                "recommended_actions": ["Please refresh the page in a few minutes", "Check network connectivity", "Contact support if the issue persists"]
            }
        
        try:
            # Validate and sanitize input (use ai_prompt type for relaxed validation)
            if not security_manager.validate_input(prompt, "ai_prompt"):
                security_logger.warning("Invalid prompt detected")
                return {
                    "summary": "AI insights request was rejected by prompt safety validation.",
                    "key_insights": ["Potentially dangerous input was detected and blocked before any model call."],
                    "trends": ["No external AI request was made."],
                    "recommended_actions": ["Remove injected commands or unsafe patterns and try again."]
                }
            
            # Scrub PII from prompt for GDPR/CCPA compliance
            scrubbed_prompt = self.pii_scrubber.scrub_text(prompt)
            if scrubbed_prompt != prompt:
                security_logger.info("PII detected and scrubbed from prompt for LLM compliance")
                prompt = scrubbed_prompt
            
            # Rate limiting check
            if not security_manager.rate_limit_check("llm_api"):
                security_logger.warning("Rate limit exceeded for LLM API")
                return {
                    "summary": "AI insights are temporarily rate-limited.",
                    "key_insights": ["The request was blocked before reaching the AI provider."],
                    "trends": ["Traffic controls are currently active."],
                    "recommended_actions": ["Wait briefly and retry the request."]
                }
            headers = {
                "Authorization": f"Bearer {self.config['api_key']}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/your-repo/telecomdashboard",  # Required by OpenRouter
            }
            
            data = {
                "model": self.config["model"],
                "messages": [
                    {
                        "role": "system",
                        "content": """You are an expert telecommunications analyst AI. You MUST respond with valid JSON only. No explanatory text before or after the JSON.

Analyze the KPI data and provide clear, actionable insights. Format your response as a JSON object with this exact structure:
{
  "summary": "One paragraph overview of key findings",
  "key_insights": ["3-5 important observations"],
  "trends": ["2-3 significant trends"],
  "recommended_actions": ["3-5 specific, actionable recommendations"]
}

Focus on identifying patterns, anomalies, and suggesting specific corrective actions. Make your insights specific, data-driven, and actionable. Response must be valid JSON only."""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": self.config.get("temperature", 0.7),
                "max_tokens": self.config.get("max_tokens", 1000),
                "response_format": { "type": "json_object" }  # Gemini supports JSON responses well
            }
            
            security_logger.debug(
                "Making LLM API call",
                extra={"api_base": self.config.get("api_base"), "model": self.config.get("model")}
            )
            
            # Use the circuit breaker-protected API call
            response_data = self._make_api_call(headers, data)
            
            security_logger.debug(
                "Received LLM API response",
                extra={"response_keys": list(response_data.keys()) if isinstance(response_data, dict) else []}
            )
            
            # Parse the JSON string from the LLM response
            content = response_data["choices"][0]["message"]["content"]
            
            # Log the content for debugging
            security_logger.debug(f"LLM response content: {content[:200]}...")
            
            if not content or content.strip() == "":
                security_logger.error("Empty response from LLM")
                self.circuit_breaker.record_failure()
                return self._safe_fallback_response(
                    "AI insights are temporarily unavailable because the provider returned an empty response.",
                    "The upstream model did not return usable content.",
                    "A transient provider issue was detected.",
                    "Retry the request in a few moments."
                )
            
            try:
                insights = json.loads(content)

                # Record success for circuit breaker
                self.circuit_breaker.record_success()
                return self._normalize_provider_response(insights)
                
            except json.JSONDecodeError as e:
                security_logger.error(f"Failed to parse LLM response as JSON: {e}")
                security_logger.error(f"Raw LLM response content: {content}")
                self.circuit_breaker.record_failure()
                
                # Try to provide a fallback response
                return {
                    "summary": "Unable to process AI insights due to response format issue. Please check model configuration.",
                    "key_insights": ["LLM response parsing failed", f"Model: {self.config.get('model', 'unknown')}", "Consider switching to a supported model"],
                    "trends": ["Technical issue detected with current LLM configuration"],
                    "recommended_actions": ["Check OpenRouter model availability", "Verify model name is correct", "Consider using openai/gpt-4-turbo as alternative"]
                }
            
        except requests.exceptions.ConnectionError as e:
            security_logger.error(f"LLM API connection error: {e}")
            self.circuit_breaker.record_failure()
            return self._safe_fallback_response(
                "AI insights are temporarily unavailable because the provider could not be reached.",
                "The request failed before a model response was received.",
                "Connectivity to the AI provider is currently unstable.",
                "Check connectivity or retry the request shortly."
            )
        except requests.exceptions.Timeout as e:
            security_logger.error(f"LLM API timeout: {e}")
            self.circuit_breaker.record_failure()
            return self._safe_fallback_response(
                "AI insights timed out before the provider completed the request.",
                "The provider did not respond within the configured timeout window.",
                "Latency to the AI provider is currently elevated.",
                "Retry the request or reduce the prompt size."
            )
        except requests.exceptions.RequestException as e:
            security_logger.error(f"LLM API request error: {e}")
            self.circuit_breaker.record_failure()
            return self._safe_fallback_response(
                "AI insights are temporarily unavailable because the provider rejected the request.",
                "The request failed after provider-side validation or authentication checks.",
                "The AI provider returned an error response instead of insight data.",
                "Verify provider credentials and retry the request."
            )
        except json.JSONDecodeError as e:
            security_logger.error(f"LLM response JSON parsing error: {e}")
            self.circuit_breaker.record_failure()
            return self._safe_fallback_response(
                "AI insights are temporarily unavailable because the provider returned invalid data.",
                "The provider response could not be parsed safely.",
                "A response-format error was detected from the AI provider.",
                "Retry the request or switch to a known-good model configuration."
            )
        except KeyError as e:
            security_logger.error(f"LLM response missing expected key: {e}")
            self.circuit_breaker.record_failure()
            return self._safe_fallback_response(
                "AI insights are temporarily unavailable because the provider response was incomplete.",
                "The provider omitted one or more required response fields.",
                "A schema mismatch was detected in the AI provider response.",
                "Retry the request after checking the configured model."
            )
        except Exception as e:
            security_logger.error(f"Unexpected LLM service error: {e}")
            
            # Record failure for circuit breaker
            self.circuit_breaker.record_failure()
            
            return self._safe_fallback_response(
                "AI insights are temporarily unavailable due to an unexpected service issue.",
                "An internal error interrupted the insight generation workflow.",
                "Service health monitors detected an unexpected runtime failure.",
                "Retry the request after a short delay."
            )

    def format_insights_for_display(self, insights: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format raw insights into a structure suitable for display.
        
        Args:
            insights: Raw insights from LLM
            
        Returns:
            Dict containing formatted insights with HTML/markdown formatting
        """
        if not insights or not isinstance(insights, dict):
            return {
                "summary": "⚠️ Unable to generate insights at this time.",
                "key_insights": [],
                "trends": [],
                "recommended_actions": []
            }
        
        # Validate required keys are present
        required_keys = ['summary', 'key_insights', 'trends', 'recommended_actions']
        if not all(key in insights for key in required_keys):
            return {
                "summary": "⚠️ Insights format is incomplete.",
                "key_insights": [],
                "trends": [],
                "recommended_actions": []
            }
            
        # Add emoji indicators and formatting, with safe defaults and text sanitization
        try:
            from security_manager import sanitize_streamlit_output
            
            formatted = {
                "summary": f"📊 {sanitize_streamlit_output(insights.get('summary', 'No summary available'))}",
                "key_insights": [f"💡 {sanitize_streamlit_output(insight)}" for insight in insights.get('key_insights', []) if isinstance(insight, str)],
                "trends": [f"📈 {sanitize_streamlit_output(trend)}" for trend in insights.get('trends', []) if isinstance(trend, str)],
                "recommended_actions": [f"✅ {sanitize_streamlit_output(action)}" for action in insights.get('recommended_actions', []) if isinstance(action, str)]
            }
            
            return formatted
        except Exception as e:
            security_logger.error(f"Error formatting insights for display: {e}")
            return {
                "summary": "⚠️ Error formatting insights.",
                "key_insights": [],
                "trends": [],
                "recommended_actions": []
            }
