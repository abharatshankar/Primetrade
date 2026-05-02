#!/usr/bin/env python3
"""CLI entry point for Binance USD-M Futures Testnet order placement."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

# Allow running as `python cli.py` from project root without install
_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from bot.client import (
    BinanceAPIError,
    BinanceFuturesClient,
    MissingCredentialsError,
)
from bot.logging_config import setup_logging
from bot.orders import ORDER_PATH, place_usdm_order, summarize_response
from bot.types import OrderSide, OrderType
from bot.validators import ValidationError, build_order_params

logger = logging.getLogger(__name__)


def _print_request_summary(params: dict[str, str | None], base_url: str) -> None:
    print("\n--- Order request summary ---")
    print(f"Base URL:    {base_url}")
    print(f"Endpoint:    POST {ORDER_PATH}")
    print(f"Symbol:      {params['symbol']}")
    print(f"Side:        {params['side']}")
    print(f"Order type:  {params['type']}")
    print(f"Quantity:    {params['quantity']}")
    if params.get("price"):
        print(f"Price:       {params['price']}")
        print("Time in force: GTC (LIMIT)")
    print("-----------------------------\n")


def _print_response_details(data: dict) -> None:
    print("--- Order response ---")
    summary = summarize_response(data)
    print(json.dumps(summary, indent=2))
    print("----------------------\n")


def cmd_place_order(args: argparse.Namespace) -> int:
    log_path = setup_logging(log_dir=args.log_dir, log_filename=args.log_file)
    logger.info("Log file: %s", log_path)

    client = BinanceFuturesClient(base_url=args.base_url)
    try:
        try:
            params = build_order_params(
                args.symbol,
                args.side,
                args.order_type,
                args.quantity,
                args.price,
            )
        except ValidationError as e:
            print(f"Validation failed: {e}", file=sys.stderr)
            logger.warning("Validation error: %s", e)
            return 2

        try:
            client.require_credentials()
        except MissingCredentialsError as e:
            print(f"Configuration error: {e}", file=sys.stderr)
            logger.error("%s", e)
            return 3

        _print_request_summary(params, client.base_url)

        price = params.get("price")
        try:
            response = place_usdm_order(
                client,
                symbol=params["symbol"],
                side=OrderSide(params["side"]),
                order_type=OrderType(params["type"]),
                quantity=params["quantity"],
                price=price,
            )
        except BinanceAPIError as e:
            print(f"Order failed: {e}", file=sys.stderr)
            logger.error("Order placement failed: %s", e)
            if e.payload is not None:
                logger.debug("Error payload: %s", e.payload)
            return 4
        except Exception as e:
            print(f"Unexpected error: {e}", file=sys.stderr)
            logger.exception("Unexpected failure")
            return 5

        _print_response_details(response)
        oid = response.get("orderId", "?")
        status = response.get("status", "?")
        print(f"Success: order accepted (orderId={oid}, status={status}).")
        logger.info("Order success orderId=%s status=%s", oid, status)
        return 0
    finally:
        client.close()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Place MARKET or LIMIT orders on Binance USD-M Futures Testnet.",
    )
    p.add_argument(
        "--base-url",
        default=None,
        help="Override base URL (default: testnet or BINANCE_FUTURES_BASE_URL).",
    )
    p.add_argument(
        "--log-dir",
        default=None,
        help="Directory for log files (default: logs/ or TRADING_BOT_LOG_DIR).",
    )
    p.add_argument(
        "--log-file",
        default="trading_bot.log",
        help="Log file name inside log directory (default: trading_bot.log).",
    )

    p.add_argument("--symbol", required=True, help="e.g. BTCUSDT")
    p.add_argument(
        "--side",
        required=True,
        type=str.upper,
        choices=("BUY", "SELL"),
        help="Order side (BUY or SELL)",
    )
    p.add_argument(
        "--order-type",
        required=True,
        type=str.upper,
        choices=("MARKET", "LIMIT"),
        dest="order_type",
        help="MARKET or LIMIT",
    )
    p.add_argument("--quantity", required=True, help="Order quantity as decimal string")
    p.add_argument(
        "--price",
        default=None,
        help="Limit price (required for LIMIT; must not be used for MARKET).",
    )

    p.set_defaults(func=cmd_place_order)
    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    code = args.func(args)
    raise SystemExit(code)


if __name__ == "__main__":
    main()
