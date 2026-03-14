# bot/validators.py
import re
from typing import Literal

from .logging_config import get_logger

logger = get_logger(__name__)

VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT"}   # extendable for the Bonus section
DECIMAL_REGEX = re.compile(r"^\d+(\.\d+)?$")

def validate_symbol(symbol: str) -> str:
    if not symbol or not isinstance(symbol, str):
        raise ValueError("symbol must be a non‑empty string")
    # Binance symbols are all‑caps, 6‑12 characters, e.g. BTCUSDT
    if not re.fullmatch(r"[A-Z]{6,12}", symbol):
        raise ValueError(f"invalid symbol format: {symbol}")
    return symbol.upper()

def validate_side(side: str) -> Literal["BUY", "SELL"]:
    side = side.upper()
    if side not in VALID_SIDES:
        raise ValueError(f"side must be one of {VALID_SIDES}")
    return side

def validate_order_type(order_type: str) -> Literal["MARKET", "LIMIT"]:
    order_type = order_type.upper()
    if order_type not in VALID_ORDER_TYPES:
        raise ValueError(f"order_type must be one of {VALID_ORDER_TYPES}")
    return order_type

def validate_quantity(qty: str) -> float:
    if not DECIMAL_REGEX.match(qty):
        raise ValueError("quantity must be a positive decimal number")
    qty_f = float(qty)
    if qty_f <= 0:
        raise ValueError("quantity must be > 0")
    return qty_f

def validate_price(price: str | None) -> float | None:
    if price is None:
        return None
    if not DECIMAL_REGEX.match(price):
        raise ValueError("price must be a positive decimal number")
    p = float(price)
    if p <= 0:
        raise ValueError("price must be > 0")
    return p
