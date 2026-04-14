"""
Order Service Layer - High-level order orchestration.

Responsibilities:
- Coordinate between validators, client, and formatters
- Handle order placement with proper error handling
- Maintain clean separation of concerns
"""

from typing import Any, Dict, Optional

from .client import BinanceClient, BinanceClientError, RetryableError
from .logging_config import setup_logger
from .validators import ValidationError

logger = setup_logger()


class OrderService:
    """
    Service layer for order operations.
    
    Provides high-level methods for placing market, limit, and stop-market orders
    with integrated validation, error handling, and logging.
    """

    def __init__(self, client: BinanceClient):
        """
        Initialize OrderService with a BinanceClient.
        
        Args:
            client: BinanceClient instance
        """
        self.client = client
        logger.debug("OrderService initialized")

    def place_market_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
    ) -> Dict[str, Any]:
        """
        Place a market order.
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            side: 'BUY' or 'SELL'
            quantity: Order quantity
            
        Returns:
            Order response dict (orderId, status, executedQty, avgPrice, etc.)
            
        Raises:
            ValidationError: Invalid input parameters
            BinanceClientError: Binance API error
            RetryableError: Network error after max retries
        """
        logger.info(
            "Placing MARKET order | symbol=%s side=%s qty=%s",
            symbol,
            side,
            quantity,
        )

        try:
            response = self.client.new_order(
                symbol=symbol,
                side=side,
                type="MARKET",
                quantity=quantity,
            )
            logger.info("MARKET order placed successfully | orderId=%s", response.get("orderId"))
            return response
        except (BinanceClientError, RetryableError) as exc:
            logger.error("Failed to place MARKET order: %s", exc)
            raise

    def place_limit_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        time_in_force: str = "GTC",
    ) -> Dict[str, Any]:
        """
        Place a limit order.
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            side: 'BUY' or 'SELL'
            quantity: Order quantity
            price: Limit price
            time_in_force: 'GTC' (Good-Till-Cancel), 'IOC' (Immediate-Or-Cancel), etc.
            
        Returns:
            Order response dict
            
        Raises:
            ValidationError: Invalid input parameters
            BinanceClientError: Binance API error
            RetryableError: Network error after max retries
        """
        logger.info(
            "Placing LIMIT order | symbol=%s side=%s qty=%s price=%s tif=%s",
            symbol,
            side,
            quantity,
            price,
            time_in_force,
        )

        try:
            response = self.client.new_order(
                symbol=symbol,
                side=side,
                type="LIMIT",
                quantity=quantity,
                price=price,
                timeInForce=time_in_force,
            )
            logger.info("LIMIT order placed successfully | orderId=%s", response.get("orderId"))
            return response
        except (BinanceClientError, RetryableError) as exc:
            logger.error("Failed to place LIMIT order: %s", exc)
            raise

    def place_stop_market_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        stop_price: float,
    ) -> Dict[str, Any]:
        """
        Place a stop-market order.
        
        A stop-market order triggers a market order when the stop price is reached.
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            side: 'BUY' or 'SELL'
            quantity: Order quantity
            stop_price: Stop trigger price
            
        Returns:
            Order response dict
            
        Raises:
            ValidationError: Invalid input parameters
            BinanceClientError: Binance API error
            RetryableError: Network error after max retries
        """
        logger.info(
            "Placing STOP_MARKET order | symbol=%s side=%s qty=%s stop_price=%s",
            symbol,
            side,
            quantity,
            stop_price,
        )

        try:
            response = self.client.new_order(
                symbol=symbol,
                side=side,
                type="STOP_MARKET",
                quantity=quantity,
                stopPrice=stop_price,
            )
            logger.info("STOP_MARKET order placed successfully | orderId=%s", response.get("orderId"))
            return response
        except (BinanceClientError, RetryableError) as exc:
            logger.error("Failed to place STOP_MARKET order: %s", exc)
            raise

    def get_order(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """
        Retrieve details of an existing order.
        
        Args:
            symbol: Trading pair
            order_id: Order ID
            
        Returns:
            Order details dict
        """
        logger.debug("Fetching order details | symbol=%s orderId=%s", symbol, order_id)
        try:
            return self.client.get_order(symbol, order_id)
        except (BinanceClientError, RetryableError) as exc:
            logger.error("Failed to get order: %s", exc)
            raise

    def cancel_order(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """
        Cancel an existing order.
        
        Args:
            symbol: Trading pair
            order_id: Order ID to cancel
            
        Returns:
            Cancelled order details
        """
        logger.info("Cancelling order | symbol=%s orderId=%s", symbol, order_id)
        try:
            return self.client.cancel_order(symbol, order_id)
        except (BinanceClientError, RetryableError) as exc:
            logger.error("Failed to cancel order: %s", exc)
            raise
