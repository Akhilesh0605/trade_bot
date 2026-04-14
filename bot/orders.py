"""
Order formatting and display utilities.

Provides clean formatting for order requests and responses.
For actual order placement, use OrderService from bot.service.
"""

from typing import Any, Dict, Optional

from .logging_config import setup_logger

logger = setup_logger()


def format_order_request(
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: Optional[float] = None,
) -> str:
    """
    Format an order request summary for display.
    
    Args:
        symbol: Trading pair
        side: BUY or SELL
        order_type: MARKET, LIMIT, or STOP_MARKET
        quantity: Order quantity
        price: Optional price for LIMIT/STOP_MARKET orders
        
    Returns:
        Formatted order summary string
    """
    parts = [
        f"  Symbol    : {symbol}",
        f"  Side      : {side}",
        f"  Type      : {order_type}",
        f"  Quantity  : {quantity}",
    ]
    if price is not None:
        label = "Stop Price" if order_type == "STOP_MARKET" else "Price"
        parts.append(f"  {label:<10}: {price}")
    return "\n".join(parts)


def format_order_response(response: Dict[str, Any]) -> str:
    """
    Format an order response for display.
    
    Args:
        response: Order response dict from API
        
    Returns:
        Formatted order response string
    """
    lines = [
        f"  Order ID     : {response.get('orderId', 'N/A')}",
        f"  Client OID   : {response.get('clientOrderId', 'N/A')}",
        f"  Symbol       : {response.get('symbol', 'N/A')}",
        f"  Status       : {response.get('status', 'N/A')}",
        f"  Executed Qty : {response.get('executedQty', 'N/A')}",
        f"  Avg Price    : {response.get('avgPrice', 'N/A')}",
        f"  Time in Force: {response.get('timeInForce', 'N/A')}",
    ]
    return "\n".join(lines)


# ──────────────────────────────────────────────────────────────────────
# Deprecated functions (kept for backward compatibility, use service.py)
# ──────────────────────────────────────────────────────────────────────

from .client import BinanceClient


def place_market_order(
    client: BinanceClient,
    symbol: str,
    side: str,
    quantity: float,
) -> Dict[str, Any]:
    """
    DEPRECATED: Use OrderService.place_market_order() instead.
    
    Place a market order.
    """
    logger.warning("place_market_order() is deprecated, use OrderService instead")
    logger.info(
        "Placing MARKET order | symbol=%s side=%s qty=%s", symbol, side, quantity
    )
    print("\n── Order Request ─────────────────────────")
    print(format_order_request(symbol, side, "MARKET", quantity))

    response = client.new_order(
        symbol=symbol,
        side=side,
        type="MARKET",
        quantity=quantity,
    )

    print("\n── Order Response ────────────────────────")
    print(format_order_response(response))
    print("✅  MARKET order placed successfully!\n")
    logger.info("MARKET order success | response=%s", response)
    return response


def place_limit_order(
    client: BinanceClient,
    symbol: str,
    side: str,
    quantity: float,
    price: float,
    time_in_force: str = "GTC",
) -> Dict[str, Any]:
    """
    DEPRECATED: Use OrderService.place_limit_order() instead.
    
    Place a limit order.
    """
    logger.warning("place_limit_order() is deprecated, use OrderService instead")
    logger.info(
        "Placing LIMIT order | symbol=%s side=%s qty=%s price=%s",
        symbol,
        side,
        quantity,
        price,
    )
    print("\n── Order Request ─────────────────────────")
    print(format_order_request(symbol, side, "LIMIT", quantity, price))

    response = client.new_order(
        symbol=symbol,
        side=side,
        type="LIMIT",
        quantity=quantity,
        price=price,
        timeInForce=time_in_force,
    )

    print("\n── Order Response ────────────────────────")
    print(format_order_response(response))
    print("✅  LIMIT order placed successfully!\n")
    logger.info("LIMIT order success | response=%s", response)
    return response


def place_stop_market_order(
    client: BinanceClient,
    symbol: str,
    side: str,
    quantity: float,
    stop_price: float,
) -> Dict[str, Any]:
    """
    DEPRECATED: Use OrderService.place_stop_market_order() instead.
    
    Place a stop-market order.
    """
    logger.warning("place_stop_market_order() is deprecated, use OrderService instead")
    logger.info(
        "Placing STOP_MARKET order | symbol=%s side=%s qty=%s stop_price=%s",
        symbol,
        side,
        quantity,
        stop_price,
    )
    print("\n── Order Request ─────────────────────────")
    print(format_order_request(symbol, side, "STOP_MARKET", quantity, stop_price))

    response = client.new_order(
        symbol=symbol,
        side=side,
        type="STOP_MARKET",
        quantity=quantity,
        stopPrice=stop_price,
    )

    print("\n── Order Response ────────────────────────")
    print(format_order_response(response))
    print("✅  STOP_MARKET order placed successfully!\n")
    logger.info("STOP_MARKET order success | response=%s", response)
    return response
