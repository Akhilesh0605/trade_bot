import hashlib
import hmac
import os
import time
from typing import Any, Dict, Optional
from urllib.parse import urlencode

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .logging_config import setup_logger

logger = setup_logger()

BASE_URL = "https://testnet.binancefuture.com"


class BinanceClientError(Exception):
    """Raised when the Binance API returns an error response."""

    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(f"Binance API Error {code}: {message}")


class RetryableError(Exception):
    """Raised when a request fails after all retry attempts."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class BinanceClient:
    """
    Binance Futures Testnet API client with retry logic and mock mode support.
    
    Features:
    - Automatic retry with exponential backoff (1s, 2s, 4s)
    - Request timeout (5 seconds)
    - Mock mode support via USE_MOCK environment variable
    - Request execution time logging
    """

    # Configuration constants
    MAX_RETRIES = 3
    TIMEOUT_SECONDS = 5
    INITIAL_BACKOFF = 1  # seconds
    
    def __init__(self, api_key: str, api_secret: str, use_mock: Optional[bool] = None):
        """
        Initialize BinanceClient.
        
        Args:
            api_key: Binance API key
            api_secret: Binance API secret
            use_mock: Whether to use mock mode. If None, reads from USE_MOCK env var.
        """
        self.api_key = api_key
        self.api_secret = api_secret
        
        # Determine mock mode
        if use_mock is None:
            use_mock = os.getenv("USE_MOCK", "false").lower() == "true"
        self.use_mock = use_mock
        
        self.session = self._build_session()
        logger.info(
            "BinanceClient initialised | Base URL: %s | Mock Mode: %s",
            BASE_URL,
            self.use_mock,
        )

    def _build_session(self) -> requests.Session:
        """Build a session with retry logic and headers."""
        session = requests.Session()
        session.headers.update({
            "X-MBX-APIKEY": self.api_key,
            "Content-Type": "application/x-www-form-urlencoded",
        })
        
        # Retry strategy: exponential backoff for connection errors
        retry_strategy = Retry(
            total=self.MAX_RETRIES,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST", "DELETE"],
            backoff_factor=self.INITIAL_BACKOFF,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        
        return session

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _sign(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Sign request parameters with HMAC-SHA256."""
        params["timestamp"] = int(time.time() * 1000)
        query_string = urlencode(params)
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        params["signature"] = signature
        return params

    def _generate_mock_response(
        self, endpoint: str, method: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate a realistic mock response for testing without hitting the API.
        
        Args:
            endpoint: API endpoint (e.g., "/fapi/v1/order")
            method: HTTP method (GET, POST, DELETE)
            params: Request parameters
            
        Returns:
            Mock response dict matching Binance API format
        """
        if endpoint == "/fapi/v1/order" and method == "POST":
            # Mock order creation response
            return {
                "orderId": 12345678,
                "symbol": params.get("symbol", "BTCUSDT"),
                "status": "FILLED",
                "clientOrderId": f"mock_{int(time.time())}",
                "price": params.get("price", "65000"),
                "avgPrice": params.get("price", "65000"),
                "origQty": params.get("quantity", 1.0),
                "executedQty": params.get("quantity", 1.0),
                "cumQuote": "65000",
                "timeInForce": params.get("timeInForce", "GTC"),
                "type": params.get("type", "MARKET"),
                "reduceOnly": False,
                "side": params.get("side", "BUY"),
                "stopPrice": params.get("stopPrice", "0"),
                "workingType": "CONTRACT_PRICE",
                "priceProtect": False,
                "origType": params.get("type", "MARKET"),
                "time": int(time.time() * 1000),
                "updateTime": int(time.time() * 1000),
            }
        elif endpoint == "/fapi/v1/order" and method == "GET":
            # Mock get order response
            return {
                "avgPrice": "65000",
                "clientOrderId": "mock_order",
                "cumQuote": "65000",
                "executedQty": "1.0",
                "orderId": params.get("orderId", 12345678),
                "origQty": "1.0",
                "origType": "MARKET",
                "price": "65000",
                "reduceOnly": False,
                "side": "BUY",
                "status": "FILLED",
                "symbol": params.get("symbol", "BTCUSDT"),
                "timeInForce": "GTC",
                "type": "MARKET",
                "updateTime": int(time.time() * 1000),
                "time": int(time.time() * 1000),
            }
        elif endpoint == "/fapi/v1/time":
            # Mock server time
            return {"serverTime": int(time.time() * 1000)}
        elif endpoint == "/fapi/v2/balance":
            # Mock account balance
            return [
                {
                    "accountAlias": "default",
                    "asset": "USDT",
                    "balance": "1000.00",
                    "crossWalletBalance": "1000.00",
                    "crossUnPnl": "0",
                    "availableBalance": "1000.00",
                    "maxWithdrawAmount": "1000.00",
                    "marginAvailable": True,
                    "updateTime": int(time.time() * 1000),
                }
            ]
        else:
            # Generic mock response
            return {}

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        signed: bool = False,
    ) -> Dict[str, Any]:
        """
        Execute an HTTP request with retry logic and timeout.
        
        Args:
            method: HTTP method (GET, POST, DELETE)
            endpoint: API endpoint path
            params: Request parameters/payload
            signed: Whether to sign the request
            
        Returns:
            Parsed JSON response
            
        Raises:
            BinanceClientError: On API errors or invalid responses
            RetryableError: After exhausting all retry attempts
        """
        url = BASE_URL + endpoint
        params = params or {}
        
        if signed:
            params = self._sign(params)

        # Return mock response if in mock mode
        if self.use_mock:
            logger.debug(
                "MOCK REQUEST  %s %s | params=%s",
                method.upper(),
                endpoint,
                params,
            )
            response = self._generate_mock_response(endpoint, method, params)
            logger.debug("MOCK RESPONSE %s %s | body=%s", method.upper(), endpoint, response)
            return response

        # Real request with retry logic
        start_time = time.time()
        attempt = 0
        last_exception = None

        logger.debug(
            "REQUEST  %s %s | params=%s",
            method.upper(),
            endpoint,
            {k: v for k, v in params.items() if k != "signature"},  # Don't log signature
        )

        for attempt in range(self.MAX_RETRIES):
            try:
                response = self.session.request(
                    method,
                    url,
                    params=params,
                    timeout=self.TIMEOUT_SECONDS,
                )
                
                duration = time.time() - start_time
                logger.debug(
                    "RESPONSE %s %s | status=%s duration=%.2fs body=%s",
                    method.upper(),
                    endpoint,
                    response.status_code,
                    duration,
                    response.text[:500],
                )

                try:
                    data = response.json()
                except ValueError as exc:
                    logger.error("Non-JSON response: %s", response.text)
                    raise BinanceClientError(-1, f"Non-JSON response: {response.text}") from exc

                # Check for API errors
                if isinstance(data, dict) and "code" in data and int(data.get("code", 200)) != 200:
                    if int(data["code"]) < 0:
                        logger.error("API error: code=%s msg=%s", data["code"], data.get("msg"))
                        raise BinanceClientError(data["code"], data.get("msg", "Unknown error"))

                logger.info(
                    "Request completed successfully | endpoint=%s duration=%.2fs",
                    endpoint,
                    duration,
                )
                return data

            except requests.exceptions.Timeout as exc:
                last_exception = exc
                logger.warning(
                    "Request timeout (attempt %d/%d) | endpoint=%s | error=%s",
                    attempt + 1,
                    self.MAX_RETRIES,
                    endpoint,
                    exc,
                )
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.INITIAL_BACKOFF ** (attempt + 1))
                    
            except requests.exceptions.ConnectionError as exc:
                last_exception = exc
                logger.warning(
                    "Connection error (attempt %d/%d) | endpoint=%s | error=%s",
                    attempt + 1,
                    self.MAX_RETRIES,
                    endpoint,
                    exc,
                )
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.INITIAL_BACKOFF ** (attempt + 1))
                    
            except (BinanceClientError, requests.exceptions.RequestException) as exc:
                # Don't retry on non-retryable errors
                if isinstance(exc, BinanceClientError):
                    raise
                last_exception = exc
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.INITIAL_BACKOFF ** (attempt + 1))

        # All retries exhausted
        duration = time.time() - start_time
        logger.error(
            "Request failed after %d attempts | endpoint=%s duration=%.2fs | last_error=%s",
            self.MAX_RETRIES,
            endpoint,
            duration,
            last_exception,
        )
        raise RetryableError(
            f"Request failed after {self.MAX_RETRIES} attempts: {last_exception}"
        )

    # ------------------------------------------------------------------
    # Public API methods
    # ------------------------------------------------------------------

    def get_server_time(self) -> int:
        """
        Get the current server time from Binance.
        
        Returns:
            Server time in milliseconds
        """
        data = self._request("GET", "/fapi/v1/time")
        return data["serverTime"]

    def new_order(self, **params) -> Dict[str, Any]:
        """
        Place a new order.
        
        Args:
            **params: Order parameters (symbol, side, type, quantity, price, etc.)
            
        Returns:
            Order response dict with orderId, status, executedQty, avgPrice, etc.
        """
        return self._request("POST", "/fapi/v1/order", params=params, signed=True)

    def get_order(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """
        Get order details.
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            order_id: Order ID
            
        Returns:
            Order details dict
        """
        return self._request(
            "GET",
            "/fapi/v1/order",
            params={"symbol": symbol, "orderId": order_id},
            signed=True,
        )

    def cancel_order(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """
        Cancel an existing order.
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            order_id: Order ID to cancel
            
        Returns:
            Cancelled order details
        """
        return self._request(
            "DELETE",
            "/fapi/v1/order",
            params={"symbol": symbol, "orderId": order_id},
            signed=True,
        )

    def get_account_balance(self) -> Dict[str, Any]:
        """
        Get account balance information.
        
        Returns:
            List of asset balances with availableBalance, balance, etc.
        """
        return self._request("GET", "/fapi/v2/balance", params={}, signed=True)
