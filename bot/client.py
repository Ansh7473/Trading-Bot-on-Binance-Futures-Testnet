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

from .logging_config import get_order_logger, get_logger

# Use specialized loggers
order_logger = get_order_logger()
debug_logger = get_logger("client")  # For debug messages

class BinanceFuturesClient:
    """
    Wrapper around python‑binance Futures client that logs every
    request/response automatically and adds a `reduce_only` flag.
    """
    def __init__(self):
        load_dotenv()                     # pull credentials from .env
        api_key = os.getenv("BINANCE_API_KEY")
        api_secret = os.getenv("BINANCE_API_SECRET")

        if not api_key or not api_secret:
            order_logger.error("API credentials missing - check .env file")
            raise EnvironmentError("Missing Binance credentials")

        # `testnet=True` forces the futures base URL to https://testnet.binancefuture.com
        self.client = Client(api_key, api_secret, testnet=True)

        order_logger.info("✅ Connected to Binance Futures Testnet")

    # ------------------------------------------------------------------
    # Generic request logger – useful for debugging
    # ------------------------------------------------------------------
    def _log_and_handle(self, fn, *args, **kwargs) -> Dict[str, Any]:
        try:
            debug_logger.debug(f"API call: {fn.__name__}")
            response = fn(*args, **kwargs)
            debug_logger.debug(f"API response: {response}")
            return response
        except BinanceAPIException as e:
            order_logger.error(f"API error: {e.message}")
            raise
        except BinanceRequestException as e:
            order_logger.error(f"Network error: {e}")
            raise
        except BinanceOrderException as e:
            order_logger.error(f"Order rejected: {e.message}")
            raise
        except Exception as e:
            order_logger.error(f"Unexpected error: {e}")
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
        Wraps `futures_create_order`.  All arguments map 1‑to‑1 to the Binance
        endpoint (price is sent only for LIMIT orders, reduceOnly is optional).
        """
        
        # Log the order attempt
        price_str = f" @ ${price}" if price else " @ market"
        order_logger.info(f"Placing {order_type} {side}: {quantity} {symbol}{price_str}")
        
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

        response = self._log_and_handle(self.client.futures_create_order, **payload)
        
        # Log successful order
        if 'orderId' in response:
            order_logger.info(f"✅ Order placed: #{response['orderId']} - {response['status']}")
        
        return response
