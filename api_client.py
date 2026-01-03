"""API client for Finscreener Developer API communication."""

import os
import json
import logging
from typing import Any, Dict, Optional
from datetime import datetime, timezone
from dotenv import load_dotenv
import httpx

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Configuration - All developer API calls go through /api prefix
API_BASE = os.getenv("FINSCREENER_API_BASE", "https://api.finscreener.in")
API_KEY = os.getenv("FINSCREENER_API_KEY", "")


class FinscreenerClient:
    """HTTP client for Finscreener Developer API.

    This client uses the Developer API (/api/) which requires API key authentication.
    Rate limits apply:
    - Detail endpoints (company/director/GST details): 100 requests/day
    - Other endpoints: Higher limits based on subscription
    """

    def __init__(self, api_key: Optional[str] = None, api_base: Optional[str] = None):
        self.api_key = api_key or API_KEY
        self.api_base = (api_base or API_BASE).rstrip("/")
        self._jwt_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
        self._rate_limit_info: Dict[str, Any] = {}
        self._validate_config()

    def _validate_config(self):
        """Validate required configuration."""
        if not self.api_key:
            logger.warning("FINSCREENER_API_KEY not set. API calls will fail.")
        elif not self.api_key.startswith("fsk_"):
            logger.warning("API key should start with 'fsk_' prefix.")

    async def _ensure_jwt_token(self):
        """Exchange API key for JWT token if needed."""
        # Check if we have a valid token
        if self._jwt_token and self._token_expires_at:
            if datetime.now(timezone.utc) < self._token_expires_at:
                return

        if not self.api_key:
            return

        if not self.api_key.startswith("fsk_"):
            # Assume it's already a JWT token
            self._jwt_token = self.api_key
            return

        # Exchange API key for JWT token via Developer API
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.api_base}/api/auth/login",
                    json={"api_key": self.api_key},
                    timeout=30.0
                )
                if response.status_code == 200:
                    data = response.json()
                    # Handle nested response format
                    token_data = data.get("token", data)
                    self._jwt_token = token_data.get("access_token")
                    if self._jwt_token:
                        # Token expires in 60 minutes, refresh at 50 minutes
                        self._token_expires_at = datetime.now(timezone.utc).replace(
                            minute=datetime.now(timezone.utc).minute + 50
                        )
                        logger.info("Successfully obtained JWT token from API key")
                else:
                    error_msg = response.text
                    try:
                        error_json = response.json()
                        error_msg = error_json.get("detail", error_json.get("message", error_msg))
                    except:
                        pass
                    logger.warning(f"Failed to exchange API key for JWT: {error_msg}")
            except Exception as e:
                logger.warning(f"Error exchanging API key: {e}")

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self._jwt_token:
            headers["Authorization"] = f"Bearer {self._jwt_token}"
        return headers

    def get_rate_limit_info(self) -> Dict[str, Any]:
        """Get the last known rate limit info from detail endpoints."""
        return self._rate_limit_info

    async def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        timeout: float = 30.0,
        use_api_prefix: bool = True
    ) -> Dict[str, Any]:
        """Make an async HTTP request to Finscreener Developer API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (e.g., /company/details)
            params: Query parameters
            json_data: JSON body for POST/PUT requests
            timeout: Request timeout in seconds
            use_api_prefix: Whether to add /api prefix (default True)

        Returns:
            Response data as dictionary
        """
        # Build URL with /api prefix for developer API
        if use_api_prefix and not endpoint.startswith("/api"):
            endpoint = f"/api{endpoint}"

        url = f"{self.api_base}{endpoint}"

        # Ensure we have a JWT token
        await self._ensure_jwt_token()

        headers = self._get_headers()

        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=json_data,
                    timeout=timeout
                )

                # Handle rate limit response
                if response.status_code == 429:
                    try:
                        error_json = response.json()
                        detail = error_json.get("detail", {})
                        return {
                            "success": False,
                            "error": f"Rate limit exceeded: {detail.get('message', 'Daily limit reached')}",
                            "rate_limit": {
                                "limit": detail.get("limit", 100),
                                "used": detail.get("used", 100),
                                "resets_at": detail.get("resets_at", "End of day")
                            }
                        }
                    except:
                        return {"success": False, "error": "Rate limit exceeded. Try again tomorrow."}

                # Handle other error responses
                if response.status_code >= 400:
                    error_detail = response.text
                    try:
                        error_json = response.json()
                        error_detail = error_json.get("detail", error_json.get("message", error_detail))
                    except:
                        pass
                    return {
                        "success": False,
                        "error": f"API Error ({response.status_code}): {error_detail}"
                    }

                result = response.json()

                # Store rate limit info if present
                if isinstance(result, dict) and "rate_limit" in result:
                    self._rate_limit_info = result["rate_limit"]

                return result

            except httpx.TimeoutException:
                return {"success": False, "error": "Request timed out. Try with a simpler query."}
            except httpx.RequestError as e:
                return {"success": False, "error": f"Request failed: {str(e)}"}
            except Exception as e:
                logger.exception("Unexpected error during API request")
                return {"success": False, "error": f"Unexpected error: {str(e)}"}

    # Convenience methods
    async def get(self, endpoint: str, params: Optional[Dict] = None, **kwargs) -> Dict[str, Any]:
        """Make GET request."""
        return await self.request("GET", endpoint, params=params, **kwargs)

    async def post(self, endpoint: str, json_data: Optional[Dict] = None, params: Optional[Dict] = None, **kwargs) -> Dict[str, Any]:
        """Make POST request."""
        return await self.request("POST", endpoint, params=params, json_data=json_data, **kwargs)

    async def put(self, endpoint: str, json_data: Optional[Dict] = None, **kwargs) -> Dict[str, Any]:
        """Make PUT request."""
        return await self.request("PUT", endpoint, json_data=json_data, **kwargs)

    async def delete(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make DELETE request."""
        return await self.request("DELETE", endpoint, **kwargs)


# Global client instance
client = FinscreenerClient()


def format_response(data: Any, title: str = "") -> str:
    """Format API response for display.

    Args:
        data: Response data (dict or list)
        title: Optional title for the output

    Returns:
        Formatted string representation
    """
    if isinstance(data, dict):
        if data.get("success") == False:
            error_msg = data.get("error", "Unknown error")
            rate_limit = data.get("rate_limit")
            if rate_limit:
                return f"Error: {error_msg}\n\nRate Limit Info:\n- Daily Limit: {rate_limit.get('limit', 100)}\n- Used Today: {rate_limit.get('used', 0)}\n- Resets: {rate_limit.get('resets_at', 'End of day')}"
            return f"Error: {error_msg}"

        # Handle standard API response format
        if "data" in data:
            data = data["data"]

    output = []
    if title:
        output.append(f"## {title}\n")

    if isinstance(data, list):
        if not data:
            return "No results found."

        for i, item in enumerate(data, 1):
            if isinstance(item, dict):
                # Filter out None values and format nicely
                item_parts = []
                for k, v in item.items():
                    if v is not None and k not in ["_id", "id"]:
                        item_parts.append(f"**{k}**: {v}")
                output.append(f"{i}. " + " | ".join(item_parts[:4]))  # Limit to 4 fields per line
            else:
                output.append(f"{i}. {item}")
    elif isinstance(data, dict):
        for key, value in data.items():
            if value is not None:
                if isinstance(value, (dict, list)):
                    output.append(f"**{key}**: {json.dumps(value, indent=2, default=str)}")
                else:
                    output.append(f"**{key}**: {value}")
    else:
        output.append(str(data))

    return "\n".join(output) if output else "No data available."
