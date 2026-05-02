"""CLI and order parameter validation."""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from typing import Any

from bot.types import OrderSide, OrderType


class ValidationError(Exception):
    """Raised when user input or order parameters are invalid."""


_SYMBOL_RE = re.compile(r"^[A-Z0-9]{4,32}$")


class OrderSideInput(StrEnum):
    BUY = "BUY"
    SELL = "SELL"


class OrderTypeInput(StrEnum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"


def validate_symbol(symbol: str) -> str:
    s = symbol.strip().upper()
    if not _SYMBOL_RE.match(s):
        raise ValidationError(
            "Symbol must be 4–32 alphanumeric uppercase characters (e.g. BTCUSDT)."
        )
    return s


def validate_side(side: str) -> OrderSide:
    s = side.strip().upper()
    try:
        return OrderSide(OrderSideInput(s))
    except ValueError as e:
        raise ValidationError("Side must be BUY or SELL.") from e


def validate_order_type(order_type: str) -> OrderType:
    t = order_type.strip().upper()
    try:
        return OrderType(OrderTypeInput(t))
    except ValueError as e:
        raise ValidationError("Order type must be MARKET or LIMIT.") from e


def validate_quantity(quantity: str) -> str:
    q = quantity.strip()
    if not q:
        raise ValidationError("Quantity is required.")
    try:
        d = Decimal(q)
    except InvalidOperation as e:
        raise ValidationError("Quantity must be a valid decimal number.") from e
    if d <= 0:
        raise ValidationError("Quantity must be greater than zero.")
    return q


def validate_price_for_limit(price: str | None) -> str:
    if price is None or not str(price).strip():
        raise ValidationError("Price is required for LIMIT orders.")
    p = str(price).strip()
    try:
        d = Decimal(p)
    except InvalidOperation as e:
        raise ValidationError("Price must be a valid decimal number.") from e
    if d <= 0:
        raise ValidationError("Price must be greater than zero.")
    return p


def validate_no_price_for_market(price: Any) -> None:
    if price is not None and str(price).strip():
        raise ValidationError("Price must not be set for MARKET orders.")


def build_order_params(
    symbol: str,
    side: str,
    order_type: str,
    quantity: str,
    price: str | None,
) -> dict[str, str]:
    """Validate and return normalized string parameters for order placement."""
    sym = validate_symbol(symbol)
    s = validate_side(side)
    ot = validate_order_type(order_type)
    qty = validate_quantity(quantity)

    if ot is OrderType.MARKET:
        validate_no_price_for_market(price)
        pr: str | None = None
    else:
        pr = validate_price_for_limit(price)

    out: dict[str, str | None] = {
        "symbol": sym,
        "side": s.value,
        "type": ot.value,
        "quantity": qty,
        "price": pr,
    }
    return out
