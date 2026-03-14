# --------------------------------------------------------------
# bot/client.py – thin wrapper around python‑binance Futures client
# --------------------------------------------------------------
import os
from typing import Dict, Any

from binance.client import Client
from binance.exceptions import (
    BinanceAPIException,
    BinanceRequestException,
    BinanceOrderException,
)
from dotenv import load_dotenv

# ------------------------------------------------------------------
# Logging helpers (keep the same names you use elsewhere)
# ------------------------------------------------------------------
from .logging_config import get_order_logger, get_logger

# Use a dedicated logger for order‑related messages
order_logger = get_order_logger()
# Debug‑only logger (kept separate so we don’t pollute the console)
debug_logger = get_logger("client")


class BinanceFuturesClient:
    """
    Wrapper around python‑binance Futures client.
    It can be instantiated **with** explicit API credentials
    (useful for the Streamlit UI) **or** fall back to the
    values stored in a .env file.
    """

    def __init__(self, api_key: str | None = None, api_secret: str | None = None):
        # Load .env for fallback values
        load_dotenv()

        # If the caller supplied a key/secret use them,
        # otherwise read from the environment.
        if api_key is None:
            api_key = os.getenv("BINANCE_API_KEY")
        if api_secret is None:
            api_secret = os.getenv("BINANCE_API_SECRET")

        # ------------------------------------------------------------------
        # Validate that we actually have credentials
        # ------------------------------------------------------------------
        if not api_key or not api_secret:
            order_logger.error(
                "API credentials missing – provide BINANCE_API_KEY & BINANCE_API_SECRET"
            )
            raise EnvironmentError("Missing Binance credentials")

        # testnet=True forces the futures base URL to the Binance test‑net
        self.client = Client(api_key, api_secret, testnet=True)

        order_logger.info("✅ Connected to Binance Futures Testnet")

    # ------------------------------------------------------------------
    # Generic request logger – useful for debugging (now uses debug_logger)
    # ------------------------------------------------------------------
    def _log_and_handle(self, fn, *args, **kwargs) -> Dict[str, Any]:
        try:
            debug_logger.debug(
                f"Calling Binance API: {fn.__name__} args={args} kwargs={kwargs}"
            )
            response = fn(*args, **kwargs)
            debug_logger.debug(f"Binance response: {response}")
            return response
        except BinanceAPIException as e:
            order_logger.error(f"Binance API error {e.status_code}: {e.message}")
            raise
        except BinanceRequestException as e:
            order_logger.error(f"Network/request error: {e}")
            raise
        except BinanceOrderException as e:
            order_logger.error(f"Order rejected: {e.message}")
            raise
        except Exception as e:
            order_logger.exception(f"Unexpected error while calling Binance: {e}")
            raise

    # ------------------------------------------------------------------
    # Public method used by OrderService (now supports reduceOnly)
    # ------------------------------------------------------------------
    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: float | None = None,
        time_in_force: str = "GTC",
        reduce_only: bool = False,
    ) -> Dict[str, Any]:
        """
        Wraps `futures_create_order`. All arguments map 1‑to‑1 to the Binance
        endpoint (price is sent only for LIMIT orders, reduceOnly is optional).
        """
        # ------------------------------------------------------------------
        # Build the payload
        # ------------------------------------------------------------------
        payload: Dict[str, Any] = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": quantity,
            "reduceOnly": reduce_only,
        }

        if order_type == "LIMIT":
            payload.update(
                {
                    "price": price,
                    "timeInForce": time_in_force,
                }
            )
        # MARKET orders ignore price / timeInForce – Binance will ignore them.

        # Log the request (debug only)
        debug_logger.debug(f"Prepared payload for {order_type} order: {payload}")

        # Send the request via the generic logger/handler
        return self._log_and_handle(self.client.futures_create_order, **payload)
