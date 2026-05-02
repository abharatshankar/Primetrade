"""High-level order placement for USD-M Futures."""

from __future__ import annotations

import logging
from typing import Any

from bot.client import BinanceAPIError, BinanceFuturesClient
from bot.types import OrderSide, OrderType

logger = logging.getLogger(__name__)

ORDER_PATH = "/fapi/v1/order"


def place_usdm_order(
    client: BinanceFuturesClient,
    *,
    symbol: str,
    side: OrderSide,
    order_type: OrderType,
    quantity: str,
    price: str | None = None,
    time_in_force: str = "GTC",
) -> dict[str, Any]:
    """
    Place a MARKET or LIMIT order on USD-M Futures.

    ``price`` is required for LIMIT and must be omitted for MARKET at the API layer.
    """
    params: dict[str, Any] = {
        "symbol": symbol,
        "side": side.value,
        "type": order_type.value,
        "quantity": quantity,
    }

    if order_type is OrderType.LIMIT:
        if not price:
            raise ValueError("price is required for LIMIT orders")
        params["price"] = price
        params["timeInForce"] = time_in_force
    elif order_type is OrderType.MARKET:
        pass
    else:
        raise ValueError(f"Unsupported order type: {order_type}")

    logger.info(
        "Placing %s %s order: symbol=%s qty=%s",
        side.value,
        order_type.value,
        symbol,
        quantity,
    )
    if price:
        logger.info("Limit price=%s timeInForce=%s", price, time_in_force)

    return client.signed_request("POST", ORDER_PATH, params)


def summarize_response(data: dict[str, Any]) -> dict[str, Any]:
    """Extract commonly displayed fields from order response."""
    keys = ("orderId", "status", "executedQty", "avgPrice", "clientOrderId", "symbol", "side", "type")
    return {k: data.get(k) for k in keys if k in data}
