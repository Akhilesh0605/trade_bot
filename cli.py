#!/usr/bin/env python3
"""
Binance Futures Testnet – Trading Bot CLI

Production-quality CLI with improved error handling, formatting, and reliability.

Usage examples:
  python cli.py place --symbol BTCUSDT --side BUY  --type MARKET --quantity 0.01
  python cli.py place --symbol BTCUSDT --side SELL --type LIMIT  --quantity 0.01 --price 50000
  python cli.py place --symbol BTCUSDT --side BUY  --type STOP_MARKET --quantity 0.01 --price 40000
  python cli.py balance
  
Environment variables:
  BINANCE_API_KEY: Your Binance API key
  BINANCE_API_SECRET: Your Binance API secret
  USE_MOCK: Set to 'true' to use mock mode (no real API calls)
"""

import argparse
import os
import sys

from dotenv import load_dotenv

from bot.client import BinanceClient, BinanceClientError, RetryableError
from bot.logging_config import setup_logger
from bot.orders import format_order_request, format_order_response
from bot.service import OrderService
from bot.validators import ValidationError, validate_all

load_dotenv()
logger = setup_logger()


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def get_client() -> BinanceClient:
    """
    Load API credentials and create a BinanceClient.
    
    Returns:
        Configured BinanceClient instance
        
    Raises:
        SystemExit: If credentials are missing
    """
    api_key = os.getenv("BINANCE_API_KEY", "").strip()
    api_secret = os.getenv("BINANCE_API_SECRET", "").strip()
    
    if not api_key or not api_secret:
        print(
            "❌  API credentials not found.\n"
            "    Set BINANCE_API_KEY and BINANCE_API_SECRET in your .env file or environment."
        )
        logger.error("Missing API credentials.")
        sys.exit(1)
    
    return BinanceClient(api_key, api_secret)


def print_section(title: str) -> None:
    """Print a formatted section header."""
    print(f"\n── {title:<41}──")


def print_success(message: str) -> None:
    """Print a success message."""
    print(f"✅  {message}")


def print_error(message: str) -> None:
    """Print an error message."""
    print(f"❌  {message}")


# ──────────────────────────────────────────────
# Sub-command handlers
# ──────────────────────────────────────────────

def handle_place(args: argparse.Namespace) -> None:
    """
    Handle the 'place' subcommand.
    
    Validates input, creates an OrderService, and places the order.
    Displays formatted output and error messages.
    """
    # Validate input parameters
    try:
        params = validate_all(
            symbol=args.symbol,
            side=args.side,
            order_type=args.type,
            quantity=str(args.quantity),
            price=str(args.price) if args.price is not None else None,
        )
    except ValidationError as exc:
        print_error(f"Validation error: {exc}")
        logger.warning("Validation error: %s", exc)
        sys.exit(1)

    # Create client and service
    client = get_client()
    service = OrderService(client)

    # Display order request
    print_section("Order Request")
    print(format_order_request(
        params["symbol"],
        params["side"],
        params["order_type"],
        params["quantity"],
        params["price"],
    ))

    # Place the order
    try:
        if params["order_type"] == "MARKET":
            response = service.place_market_order(
                symbol=params["symbol"],
                side=params["side"],
                quantity=params["quantity"],
            )
        elif params["order_type"] == "LIMIT":
            response = service.place_limit_order(
                symbol=params["symbol"],
                side=params["side"],
                quantity=params["quantity"],
                price=params["price"],
            )
        elif params["order_type"] == "STOP_MARKET":
            response = service.place_stop_market_order(
                symbol=params["symbol"],
                side=params["side"],
                quantity=params["quantity"],
                stop_price=params["price"],
            )
        else:
            print_error(f"Unknown order type: {params['order_type']}")
            sys.exit(1)

        # Display order response
        print_section("Order Response")
        print(format_order_response(response))
        print_success(f"{params['order_type']} order placed successfully! (ID: {response.get('orderId')})")
        print()
        logger.info("Order placed successfully | type=%s orderId=%s", params["order_type"], response.get("orderId"))

    except ValidationError as exc:
        print_error(f"Validation error: {exc}")
        logger.error("Validation error: %s", exc)
        sys.exit(1)
    except BinanceClientError as exc:
        print_error(f"Binance API error [{exc.code}]: {exc.message}")
        logger.error("BinanceClientError: %s", exc)
        sys.exit(1)
    except RetryableError as exc:
        print_error(f"Network error: {exc.message}")
        logger.error("RetryableError: %s", exc)
        sys.exit(1)
    except Exception as exc:
        print_error(f"Unexpected error: {exc}")
        logger.error("Unexpected error: %s", exc, exc_info=True)
        sys.exit(1)


def handle_balance(args: argparse.Namespace) -> None:
    """
    Handle the 'balance' subcommand.
    
    Displays account balances with formatted output.
    """
    client = get_client()
    
    try:
        balances = client.get_account_balance()
        print_section("Account Balances")
        
        has_balance = False
        for asset in balances:
            avail = float(asset.get("availableBalance", 0))
            if avail > 0:
                has_balance = True
                print(f"  {asset['asset']:<10} Available: {avail:>15.4f}  Wallet: {asset.get('balance', 'N/A')}")
        
        if not has_balance:
            print("  (No balances found)")
        
        print()
        logger.info("Balance retrieved successfully")
        
    except BinanceClientError as exc:
        print_error(f"Binance API error [{exc.code}]: {exc.message}")
        logger.error("BinanceClientError: %s", exc)
        sys.exit(1)
    except RetryableError as exc:
        print_error(f"Network error: {exc.message}")
        logger.error("RetryableError: %s", exc)
        sys.exit(1)
    except Exception as exc:
        print_error(f"Unexpected error: {exc}")
        logger.error("Unexpected error: %s", exc, exc_info=True)
        sys.exit(1)


# ──────────────────────────────────────────────
# Argument parser
# ──────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser."""
    parser = argparse.ArgumentParser(
        prog="trading_bot",
        description="Binance Futures Testnet – Trading Bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Place a MARKET order:
    python cli.py place --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01
  
  Place a LIMIT order:
    python cli.py place --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.01 --price 50000
  
  Place a STOP_MARKET order:
    python cli.py place --symbol BTCUSDT --side BUY --type STOP_MARKET --quantity 0.01 --price 40000
  
  Check account balances:
    python cli.py balance

Environment:
  Set USE_MOCK=true to use mock mode (for testing without real API calls)
        """,
    )
    
    sub = parser.add_subparsers(dest="command", required=True, help="Command to execute")

    # ── place ──
    place = sub.add_parser("place", help="Place a new order")
    place.add_argument(
        "--symbol",
        required=True,
        help="Trading pair, e.g. BTCUSDT",
    )
    place.add_argument(
        "--side",
        required=True,
        choices=["BUY", "SELL"],
        help="BUY or SELL",
    )
    place.add_argument(
        "--type",
        required=True,
        choices=["MARKET", "LIMIT", "STOP_MARKET"],
        help="Order type",
    )
    place.add_argument(
        "--quantity",
        required=True,
        type=float,
        help="Order quantity",
    )
    place.add_argument(
        "--price",
        required=False,
        type=float,
        default=None,
        help="Price (required for LIMIT / STOP_MARKET)",
    )

    # ── balance ──
    sub.add_parser("balance", help="Show account balances")

    return parser


def main() -> None:
    """Main entry point."""
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "place":
        handle_place(args)
    elif args.command == "balance":
        handle_balance(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
