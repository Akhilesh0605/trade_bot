"""
Input validation for order parameters.

Validates:
- Trading pair symbols
- Order sides (BUY/SELL)
- Order types (MARKET/LIMIT/STOP_MARKET)
- Quantities (must be > 0)
- Prices (required for LIMIT/STOP_MARKET, must be > 0)
"""

from typing import Optional


VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT", "STOP_MARKET"}


class ValidationError(Exception):
    """Raised when input validation fails."""

    pass


def validate_symbol(symbol: str) -> str:
    """
    Validate trading pair symbol.
    
    Args:
        symbol: Trading pair symbol (e.g., 'BTCUSDT')
        
    Returns:
        Normalized symbol (uppercase, stripped)
        
    Raises:
        ValidationError: If symbol is invalid
    """
    symbol = symbol.strip().upper()
    if not symbol or not symbol.isalpha():
        raise ValidationError(
            f"Invalid symbol '{symbol}'. Must be alphabetic, e.g. BTCUSDT."
        )
    return symbol


def validate_side(side: str) -> str:
    """
    Validate order side.
    
    Args:
        side: Order side (BUY or SELL)
        
    Returns:
        Normalized side (uppercase, stripped)
        
    Raises:
        ValidationError: If side is not BUY or SELL
    """
    side = side.strip().upper()
    if side not in VALID_SIDES:
        raise ValidationError(
            f"Invalid side '{side}'. Must be one of: {', '.join(sorted(VALID_SIDES))}."
        )
    return side


def validate_order_type(order_type: str) -> str:
    """
    Validate order type.
    
    Args:
        order_type: Order type (MARKET, LIMIT, or STOP_MARKET)
        
    Returns:
        Normalized order type (uppercase, stripped)
        
    Raises:
        ValidationError: If order type is invalid
    """
    order_type = order_type.strip().upper()
    if order_type not in VALID_ORDER_TYPES:
        raise ValidationError(
            f"Invalid order type '{order_type}'. Must be one of: {', '.join(sorted(VALID_ORDER_TYPES))}."
        )
    return order_type


def validate_quantity(quantity: str) -> float:
    """
    Validate order quantity.
    
    Args:
        quantity: Order quantity as string or number
        
    Returns:
        Quantity as float
        
    Raises:
        ValidationError: If quantity is not a positive number
    """
    try:
        qty = float(quantity)
    except (ValueError, TypeError):
        raise ValidationError(f"Invalid quantity '{quantity}'. Must be a positive number.")
    if qty <= 0:
        raise ValidationError(f"Quantity must be greater than 0. Got: {qty}")
    return qty


def validate_price(price: Optional[str], order_type: str) -> Optional[float]:
    """
    Validate order price.
    
    Args:
        price: Price as string or number (or None)
        order_type: Order type (determines if price is required)
        
    Returns:
        Price as float, or None if not required for this order type
        
    Raises:
        ValidationError: If price is invalid or missing when required
    """
    if order_type == "LIMIT":
        if price is None:
            raise ValidationError("Price is required for LIMIT orders.")
        try:
            p = float(price)
        except (ValueError, TypeError):
            raise ValidationError(f"Invalid price '{price}'. Must be a positive number.")
        if p <= 0:
            raise ValidationError(f"Price must be greater than 0. Got: {p}")
        return p
    
    if order_type == "STOP_MARKET":
        if price is None:
            raise ValidationError("Stop price is required for STOP_MARKET orders.")
        try:
            p = float(price)
        except (ValueError, TypeError):
            raise ValidationError(f"Invalid stop price '{price}'. Must be a positive number.")
        if p <= 0:
            raise ValidationError(f"Stop price must be greater than 0. Got: {p}")
        return p
    
    # MARKET orders don't need a price
    return None


def validate_all(
    symbol: str,
    side: str,
    order_type: str,
    quantity: str,
    price: Optional[str] = None,
) -> dict:
    """
    Run all validations and return a clean params dict.
    
    Args:
        symbol: Trading pair symbol
        side: Order side (BUY/SELL)
        order_type: Order type (MARKET/LIMIT/STOP_MARKET)
        quantity: Order quantity
        price: Price (optional, required for LIMIT/STOP_MARKET)
        
    Returns:
        Dict with validated parameters: {symbol, side, order_type, quantity, price}
        
    Raises:
        ValidationError: If any validation fails
    """
    sym = validate_symbol(symbol)
    s = validate_side(side)
    ot = validate_order_type(order_type)
    qty = validate_quantity(quantity)
    p = validate_price(price, ot)
    return {"symbol": sym, "side": s, "order_type": ot, "quantity": qty, "price": p}
