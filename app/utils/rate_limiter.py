"""
Advanced API Rate Limiting với Circuit Breaker và Adaptive Backoff
"""
import time
import logging
from enum import Enum
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Optional, Callable, Any
import threading

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"       # Normal operation
    OPEN = "open"          # Blocking requests
    HALF_OPEN = "half_open" # Testing if service recovered

@dataclass
class RateLimitConfig:
    """Rate limiting configuration"""
    requests_per_minute: int = 60
    burst_limit: int = 10
    backoff_multiplier: float = 1.5
    max_backoff: int = 300  # 5 minutes
    circuit_failure_threshold: int = 5
    circuit_timeout: int = 60  # seconds
    adaptive_scaling: bool = True

class AdaptiveRateLimiter:
    """
    Advanced rate limiter với adaptive backoff và circuit breaker
    """
    
    def __init__(self, service_name: str, config: RateLimitConfig):
        self.service_name = service_name
        self.config = config
        
        # Rate limiting state
        self._requests = []
        self._last_request_time = 0
        self._current_interval = 60 / config.requests_per_minute
        self._lock = threading.RLock()
        
        # Circuit breaker state
        self._circuit_state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time = None
        self._next_attempt_time = None
        
        # Adaptive scaling
        self._success_count = 0
        self._recent_response_times = []
        
        logger.info(f"Initialized rate limiter for {service_name}")
    
    def can_make_request(self) -> tuple[bool, float]:
        """
        Kiểm tra có thể make request không
        Returns: (can_request, wait_time)
        """
        with self._lock:
            current_time = time.time()
            
            # Check circuit breaker
            if self._circuit_state == CircuitState.OPEN:
                if current_time < self._next_attempt_time:
                    wait_time = self._next_attempt_time - current_time
                    return False, wait_time
                else:
                    # Transition to half-open
                    self._circuit_state = CircuitState.HALF_OPEN
                    logger.info(f"Circuit breaker {self.service_name}: OPEN -> HALF_OPEN")
            
            # Check rate limiting
            time_since_last = current_time - self._last_request_time
            if time_since_last < self._current_interval:
                wait_time = self._current_interval - time_since_last
                return False, wait_time
            
            # Clean old requests for burst limiting
            minute_ago = current_time - 60
            self._requests = [req_time for req_time in self._requests if req_time > minute_ago]
            
            # Check burst limit
            if len(self._requests) >= self.config.burst_limit:
                # Calculate wait time to oldest request + 60s
                oldest_request = min(self._requests)
                wait_time = (oldest_request + 60) - current_time
                return False, max(0, wait_time)
            
            return True, 0
    
    def record_request(self, response_time: Optional[float] = None):
        """Record a successful request"""
        with self._lock:
            current_time = time.time()
            self._last_request_time = current_time
            self._requests.append(current_time)
            
            # Record success for circuit breaker
            if self._circuit_state == CircuitState.HALF_OPEN:
                self._circuit_state = CircuitState.CLOSED
                self._failure_count = 0
                logger.info(f"Circuit breaker {self.service_name}: HALF_OPEN -> CLOSED")
            
            self._success_count += 1
            
            # Record response time for adaptive scaling
            if response_time:
                self._recent_response_times.append(response_time)
                # Keep only last 10 response times
                if len(self._recent_response_times) > 10:
                    self._recent_response_times.pop(0)
            
            # Adaptive scaling - reduce interval if performing well
            if (self.config.adaptive_scaling and 
                self._success_count > 0 and 
                self._success_count % 10 == 0):
                self._adapt_rate_limit()
    
    def record_failure(self, error_code: Optional[int] = None):
        """Record a failed request"""
        with self._lock:
            current_time = time.time()
            self._failure_count += 1
            self._last_failure_time = current_time
            
            # Update interval based on error type
            if error_code == 429:  # Rate limited
                self._current_interval = min(
                    self._current_interval * self.config.backoff_multiplier,
                    self.config.max_backoff
                )
                logger.warning(f"Rate limit hit for {self.service_name}, "
                             f"increasing interval to {self._current_interval:.2f}s")
            
            # Check circuit breaker threshold
            if (self._failure_count >= self.config.circuit_failure_threshold and
                self._circuit_state != CircuitState.OPEN):
                
                self._circuit_state = CircuitState.OPEN
                self._next_attempt_time = current_time + self.config.circuit_timeout
                logger.error(f"Circuit breaker {self.service_name}: -> OPEN "
                           f"(failures: {self._failure_count})")
    
    def _adapt_rate_limit(self):
        """Adaptive rate limiting based on performance"""
        if not self._recent_response_times:
            return
        
        avg_response_time = sum(self._recent_response_times) / len(self._recent_response_times)
        
        # If response times are good, we can be more aggressive
        if avg_response_time < 1.0:  # Less than 1 second
            # Reduce interval by 10%
            new_interval = self._current_interval * 0.9
            min_interval = 60 / self.config.requests_per_minute
            self._current_interval = max(new_interval, min_interval)
            
        elif avg_response_time > 3.0:  # More than 3 seconds
            # Increase interval by 20%
            new_interval = self._current_interval * 1.2
            self._current_interval = min(new_interval, self.config.max_backoff)
    
    def get_stats(self) -> dict:
        """Get current rate limiter statistics"""
        with self._lock:
            current_time = time.time()
            
            # Count requests in last minute
            minute_ago = current_time - 60
            recent_requests = len([req for req in self._requests if req > minute_ago])
            
            avg_response_time = None
            if self._recent_response_times:
                avg_response_time = sum(self._recent_response_times) / len(self._recent_response_times)
            
            return {
                "service_name": self.service_name,
                "circuit_state": self._circuit_state.value,
                "current_interval": round(self._current_interval, 2),
                "requests_last_minute": recent_requests,
                "failure_count": self._failure_count,
                "success_count": self._success_count,
                "avg_response_time": round(avg_response_time, 3) if avg_response_time else None,
                "time_until_next_request": max(0, self._current_interval - (current_time - self._last_request_time))
            }

class APIServiceManager:
    """
    Central manager cho tất cả API services với rate limiting
    """
    
    def __init__(self):
        self._limiters = {}
        self._configs = {
            "coingecko": RateLimitConfig(
                requests_per_minute=50,  # CoinGecko free tier
                burst_limit=5,
                circuit_failure_threshold=3
            ),
            "taapi": RateLimitConfig(
                requests_per_minute=1,   # Very conservative for TAAPI
                burst_limit=1,
                backoff_multiplier=2.0,
                circuit_failure_threshold=2
            ),
            "alternative_me": RateLimitConfig(
                requests_per_minute=30,  # Fear & Greed API
                burst_limit=3,
                circuit_failure_threshold=3
            )
        }
        
        # Initialize limiters
        for service, config in self._configs.items():
            self._limiters[service] = AdaptiveRateLimiter(service, config)
    
    def get_limiter(self, service_name: str) -> AdaptiveRateLimiter:
        """Get rate limiter for specific service"""
        if service_name not in self._limiters:
            # Create default limiter for unknown services
            config = RateLimitConfig()
            self._limiters[service_name] = AdaptiveRateLimiter(service_name, config)
        
        return self._limiters[service_name]
    
    def can_call_api(self, service_name: str) -> tuple[bool, float]:
        """Check if we can call specific API"""
        limiter = self.get_limiter(service_name)
        return limiter.can_make_request()
    
    def record_api_call(self, service_name: str, success: bool, 
                       response_time: Optional[float] = None, 
                       error_code: Optional[int] = None):
        """Record API call result"""
        limiter = self.get_limiter(service_name)
        
        if success:
            limiter.record_request(response_time)
        else:
            limiter.record_failure(error_code)
    
    def get_all_stats(self) -> dict:
        """Get statistics for all services"""
        return {
            service: limiter.get_stats() 
            for service, limiter in self._limiters.items()
        }

# Global service manager instance
api_service_manager = APIServiceManager()

# Decorator for API calls với automatic rate limiting
def rate_limited_api_call(service_name: str, timeout: float = 5.0):
    """
    Decorator cho API calls với automatic rate limiting và circuit breaker
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            limiter = api_service_manager.get_limiter(service_name)
            
            # Check if we can make request
            can_request, wait_time = limiter.can_make_request()
            if not can_request:
                logger.warning(f"Rate limited {service_name}, wait {wait_time:.2f}s")
                return None, f"Rate limited, wait {wait_time:.2f}s", 429
            
            # Make request
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                response_time = time.time() - start_time
                
                # Record success
                limiter.record_request(response_time)
                
                return result
                
            except Exception as e:
                response_time = time.time() - start_time
                
                # Determine error code
                error_code = None
                if "429" in str(e) or "rate limit" in str(e).lower():
                    error_code = 429
                elif "timeout" in str(e).lower():
                    error_code = 408
                else:
                    error_code = 500
                
                # Record failure
                limiter.record_failure(error_code)
                
                logger.error(f"API call failed for {service_name}: {e}")
                raise
        
        return wrapper
    return decorator
