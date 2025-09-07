"""
Base API Client with rate limiting, retry logic, and error handling
"""

import asyncio
import time
from typing import Dict, Any, Optional, Union
from datetime import datetime, timedelta
import httpx
import logging
from abc import ABC, abstractmethod

from ..config import settings
from ..logging_config import get_logger

logger = get_logger("api_client")


class RateLimiter:
    """Simple rate limiter for API requests"""
    
    def __init__(self, max_requests: int = 100, time_window: int = 60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []
    
    async def acquire(self) -> None:
        """Wait if necessary to respect rate limits"""
        now = time.time()
        
        # Remove old requests outside the time window
        self.requests = [req_time for req_time in self.requests if now - req_time < self.time_window]
        
        # If we're at the limit, wait
        if len(self.requests) >= self.max_requests:
            oldest_request = min(self.requests)
            wait_time = self.time_window - (now - oldest_request)
            if wait_time > 0:
                logger.info(f"Rate limit reached, waiting {wait_time:.2f} seconds")
                await asyncio.sleep(wait_time)
        
        # Record this request
        self.requests.append(now)


class APIError(Exception):
    """Base exception for API errors"""
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(message)


class BaseAPIClient(ABC):
    """Base class for API clients with common functionality"""
    
    def __init__(self, base_url: str, timeout: int = 30, rate_limit: int = 100):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.rate_limiter = RateLimiter(max_requests=rate_limit, time_window=60)
        self.client = httpx.AsyncClient(timeout=timeout)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    @abstractmethod
    def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for requests"""
        pass
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        retries: int = 3
    ) -> Dict[str, Any]:
        """Make an authenticated API request with retry logic"""
        
        await self.rate_limiter.acquire()
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        # Merge headers
        request_headers = self.get_auth_headers()
        if headers:
            request_headers.update(headers)
        
        for attempt in range(retries + 1):
            try:
                logger.debug(f"Making {method} request to {url} (attempt {attempt + 1})")
                
                response = await self.client.request(
                    method=method,
                    url=url,
                    json=data if method in ['POST', 'PUT', 'PATCH'] else None,
                    params=params,
                    headers=request_headers
                )
                
                # Handle response
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:  # Rate limited
                    wait_time = int(response.headers.get('Retry-After', 60))
                    logger.warning(f"Rate limited, waiting {wait_time} seconds")
                    await asyncio.sleep(wait_time)
                    continue
                elif 500 <= response.status_code < 600:  # Server errors - retry
                    if attempt < retries:
                        wait_time = 2 ** attempt  # Exponential backoff
                        logger.warning(f"Server error {response.status_code}, retrying in {wait_time}s")
                        await asyncio.sleep(wait_time)
                        continue
                
                # For other errors, raise immediately
                error_data = None
                try:
                    error_data = response.json()
                except:
                    error_data = {"error": response.text}
                
                raise APIError(
                    message=f"API request failed: {response.status_code}",
                    status_code=response.status_code,
                    response_data=error_data
                )
                
            except httpx.TimeoutException:
                if attempt < retries:
                    wait_time = 2 ** attempt
                    logger.warning(f"Request timeout, retrying in {wait_time}s")
                    await asyncio.sleep(wait_time)
                    continue
                raise APIError("Request timeout after all retries")
            
            except httpx.RequestError as e:
                if attempt < retries:
                    wait_time = 2 ** attempt
                    logger.warning(f"Request error: {e}, retrying in {wait_time}s")
                    await asyncio.sleep(wait_time)
                    continue
                raise APIError(f"Request failed: {str(e)}")
        
        raise APIError("Max retries exceeded")
    
    async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make GET request"""
        return await self._make_request('GET', endpoint, params=params)
    
    async def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make POST request"""
        return await self._make_request('POST', endpoint, data=data)
    
    async def put(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make PUT request"""
        return await self._make_request('PUT', endpoint, data=data)
    
    async def delete(self, endpoint: str) -> Dict[str, Any]:
        """Make DELETE request"""
        return await self._make_request('DELETE', endpoint)
