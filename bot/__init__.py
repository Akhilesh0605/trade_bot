"""
Trading Bot – Production-quality Binance Futures Testnet trading client.

Modules:
- client: BinanceClient with retry logic and mock mode support
- service: OrderService for high-level order operations
- validators: Input validation utilities
- orders: Order formatting utilities (deprecated, use service instead)
- logging_config: Logging setup

Key Classes:
- BinanceClient: Low-level API client with retry + timeout + mock mode
- OrderService: High-level order orchestration
- ValidationError: Raised for validation failures
- RetryableError: Raised after exhausting retries on network errors
"""

from .client import BinanceClient, BinanceClientError, RetryableError
from .orders import (
    format_order_request,
    format_order_response,
    place_limit_order,
    place_market_order,
    place_stop_market_order,
)
from .service import OrderService
from .validators import ValidationError, validate_all

__all__ = [
    "BinanceClient",
    "BinanceClientError",
    "RetryableError",
    "OrderService",
    "format_order_request",
    "format_order_response",
    "place_market_order",
    "place_limit_order",
    "place_stop_market_order",
    "validate_all",
    "ValidationError",
]
