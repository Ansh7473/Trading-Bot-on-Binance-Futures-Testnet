# --------------------------------------------------------------
# bot/client.py – thin wrapper around python‑binance Futures client
# --------------------------------------------------------------
import os
from typing import Dict, Any
from pathlib import Path

from binance.client import Client
from binance.exceptions import (
    BinanceAPIException,
    BinanceRequestException,
    BinanceOrderException,
)
from dotenv import load_dotenv

# ------------------------------------------------------------------
# Logging helpers (keep your existing loggers)
# ------------------------------------------------------------------
from .logging_config import get_order_logger, get_logger

order_logger = get_order_logger()          # user‑visible messages
debug_logger = get_logger("client")        # low‑level debug messages


class BinanceFuturesClient:
    """
    Wrapper around python‑binance Futures client.

    * **api_key / api_secret** – can be passed explicitly (from the Streamlit UI) or
      fall back to a .env file (your original behaviour).
    * **proxy_url** – optional HTTP/HTTPS proxy in the form
      ``http://user:pass@host:port``.
      When a proxy is supplied every request made by the python‑binance
      library is routed through it.
    """
    def __init__(
        self,
        api_key: str | None = None,
        api_secret: str | None = None,
        proxy_url: str | None = None,          # <-- NEW
    ):
        # Load .env only for fallback values
        load_dotenv()

        if api_key is None:
            api_key = os.getenv("BINANCE_API_KEY")
        if api_secret is None:
            api_secret = os.getenv("BINANCE_API_SECRET")

        # --------------------------------------------------------------
        # Validate credentials
        # --------------------------------------------------------------
        if not api_key or not api_secret:
            order_logger.error(
                "API credentials missing – provide BINANCE_API_KEY & BINANCE_API_SECRET"
            )
            raise EnvironmentError("Missing Binance credentials")

        # --------------------------------------------------------------
        # Build request‑params dict for the python‑binance client.
        # The library forwards this dict directly to ``requests``.
        # --------------------------------------------------------------
        request_params: Dict[str, Any] = {}
        if proxy_url:
            # ``proxies`` expects a dict of scheme → URL
            request_params["proxies"] = {"https": proxy_url}
            order_logger.info(f"🔌 Using proxy: {proxy_url}")

        # ``testnet=True`` forces the futures base URL to https://testnet.binancefuture.com
        self.client = Client(
            api_key,
            api_secret,
            testnet=True,
            requests_params=request_params,   # <-- proxy (or empty dict)
        )
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
        Wraps ``futures_create_order``. All arguments map 1‑to‑1 to Binance.
        """
        payload: Dict[str, Any] = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": quantity,
            "reduceOnly": reduce_only,
        }

        if order_type == "LIMIT":
            payload.update({"price": price, "timeInForce": time_in_force})

        debug_logger.debug(f"Prepared payload for {order_type} order: {payload}")

        return self._log_and_handle(self.client.futures_create_order, **payload)
