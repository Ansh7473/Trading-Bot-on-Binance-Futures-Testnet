# streamlit_app.py
import streamlit as st
import pandas as pd
from datetime import datetime

# Import your existing bot components
from bot.client import BinanceFuturesClient
from bot.orders import OrderService, OrderResult
from bot.validators import (
    validate_symbol,
    validate_side,
    validate_order_type,
    validate_quantity,
    validate_price,
)
from bot.logging_config import get_logger, get_order_logger

# ----------------------------------------------------------------------
# Loggers
# ----------------------------------------------------------------------
logger = get_logger(__name__)          # generic logger (debug/info)
order_logger = get_order_logger()      # user‑facing logger (info / error)

# ----------------------------------------------------------------------
# Page configuration
# ----------------------------------------------------------------------
st.set_page_config(
    page_title="Binance Futures Trading Bot",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------------------------------------------------
# Sidebar – Binance API credentials UI
# ----------------------------------------------------------------------
def credentials_box():
    """Render a sidebar where the user can paste their API key/secret."""
    with st.sidebar:
        st.header("🔑 Binance API Credentials")
        st.caption(
            "⚠️ These values are stored **only** in the current session. "
            "They are never written to disk or logged."
        )

        api_key_input = st.text_input("API Key", type="password", key="api_key_input")
        api_secret_input = st.text_input(
            "API Secret", type="password", key="api_secret_input"
        )

        # --------------------------------------------------------------
        # Save credentials
        # --------------------------------------------------------------
        if st.button("💾 Save Credentials"):
            if not api_key_input or not api_secret_input:
                st.error("Both API Key and Secret are required.")
            else:
                # Store in session_state – lives in memory only
                st.session_state.api_key = api_key_input.strip()
                st.session_state.api_secret = api_secret_input.strip()
                st.success("✅ Credentials saved – re‑initialising app")
                # <-- NEW stable API
                st.rerun()

        # --------------------------------------------------------------
        # Clear credentials
        # --------------------------------------------------------------
        if st.session_state.get("api_key"):
            if st.button("🗑️ Clear Credentials"):
                for k in [
                    "api_key",
                    "api_secret",
                    "api_key_input",
                    "api_secret_input",
                ]:
                    if k in st.session_state:
                        del st.session_state[k]
                st.success("🗑️ Credentials cleared")
                # Remove the app instance so we don’t keep a stale client
                if "app" in st.session_state:
                    del st.session_state.app
                # <-- NEW stable API
                st.rerun()

# ----------------------------------------------------------------------
# Core TradingApp class – now receives API credentials explicitly
# ----------------------------------------------------------------------
class TradingApp:
    def __init__(self, api_key: str | None = None, api_secret: str | None = None):
        """
        Initialise the Binance client only when we have valid credentials.
        If credentials are missing / invalid we keep `self.client = None`
        so the UI can show a friendly warning instead of crashing.
        """
        try:
            # Pass the credentials (or None – client will fall back to .env)
            self.client = BinanceFuturesClient(api_key=api_key, api_secret=api_secret)
            self.order_service = OrderService()
            st.success("✅ Connected to Binance Futures Testnet")
        except Exception as e:
            order_logger.error(f"Failed to initialise Binance client: {e}")
            st.error(f"❌ Binance client error: {e}")
            # Leave attributes as None – UI will guard against usage
            self.client = None
            self.order_service = None

    # ------------------------------------------------------------------
    # ACCOUNT HELPERS (guard against missing client)
    # ------------------------------------------------------------------
    def get_account_balance(self):
        """Get USDT balance"""
        if not self.client:
            logger.error("Attempted to fetch balance without a client")
            return 0.0
        try:
            bal = self.client.client.futures_account_balance()
            for item in bal:
                if item["asset"] == "USDT":
                    return float(item["balance"])
            return 0.0
        except Exception as e:
            logger.error(f"Error getting balance: {e}")
            return 0.0

    def get_positions(self):
        """Get current positions"""
        if not self.client:
            logger.error("Attempted to fetch positions without a client")
            return []
        try:
            pos = self.client.client.futures_account()["positions"]
            return [p for p in pos if float(p["positionAmt"]) != 0]
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return []

    def get_market_price(self, symbol):
        """Get current market price"""
        if not self.client:
            logger.error("Attempted to fetch price without a client")
            return 0.0
        try:
            ticker = self.client.client.futures_symbol_ticker(symbol=symbol)
            return float(ticker["price"])
        except Exception as e:
            logger.error(f"Error getting price for {symbol}: {e}")
            return 0.0

    def get_symbol_info(self, symbol):
        """Get symbol info (filters, etc.)"""
        if not self.client:
            logger.error("Attempted to fetch symbol info without a client")
            return None
        try:
            exchange_info = self.client.client.futures_exchange_info()
            for s in exchange_info["symbols"]:
                if s["symbol"] == symbol:
                    return s
            return None
        except Exception as e:
            logger.error(f"Error getting symbol info: {e}")
            return None

    def get_price_filter(self, symbol):
        """Return tickSize for the symbol (used for step sizes)"""
        info = self.get_symbol_info(symbol)
        if info:
            for f in info["filters"]:
                if f["filterType"] == "PRICE_FILTER":
                    return float(f["tickSize"])
        return 0.01  # fallback

    # ------------------------------------------------------------------
    # TP / SL helper (unchanged – just uses self.client)
    # ------------------------------------------------------------------
    def place_tp_sl_order(
        self,
        symbol,
        side,
        order_type,
        quantity,
        price=None,
        stop_price=None,
    ):
        """Place Take‑Profit / Stop‑Loss orders with proper parameters."""
        if not self.client:
            raise RuntimeError("Binance client not initialised")
        try:
            payload = {
                "symbol": symbol,
                "side": side,
                "type": order_type,
                "quantity": quantity,
            }

            # For TAKE_PROFIT and STOP orders
            if order_type in [
                "TAKE_PROFIT",
                "TAKE_PROFIT_MARKET",
                "STOP",
                "STOP_MARKET",
            ]:
                if stop_price:
                    payload["stopPrice"] = stop_price

            # LIMIT variants need a price
            if order_type in ["TAKE_PROFIT_LIMIT", "STOP_LIMIT"]:
                if price is None:
                    raise ValueError(f"Price is required for {order_type}")
                payload["price"] = price
                if stop_price:
                    payload["stopPrice"] = stop_price

            if order_type in ["LIMIT", "TAKE_PROFIT_LIMIT", "STOP_LIMIT"]:
                payload["timeInForce"] = "GTC"

            logger.info(f"Placing TP/SL order: {payload}")
            return self.client.client.futures_create_order(**payload)
        except Exception as e:
            logger.error(f"Error placing TP/SL order: {e}")
            raise

# ----------------------------------------------------------------------
# MAIN APP
# ----------------------------------------------------------------------
def main():
    # --------------------------------------------------------------
    # 1️⃣  Show the credentials UI first
    # --------------------------------------------------------------
    credentials_box()

    # --------------------------------------------------------------
    # 2️⃣  If credentials are NOT present -> show a warning and stop
    # --------------------------------------------------------------
    if not (st.session_state.get("api_key") and st.session_state.get("api_secret")):
        st.warning(
            "🔑 Please enter your Binance API Key & Secret in the sidebar to use the bot."
        )
        return  # Stop execution – the rest of the UI needs a client

    # --------------------------------------------------------------
    # 3️⃣  Initialise (or re‑initialise) the TradingApp **once**
    # --------------------------------------------------------------
    if "app" not in st.session_state:
        # First time – create the app with the credentials we just received
        st.session_state.app = TradingApp(
            api_key=st.session_state.api_key,
            api_secret=st.session_state.api_secret,
        )
    else:
        # Credentials might have changed (e.g., user cleared and re‑entered)
        # Re‑create the app if the stored client is None
        if st.session_state.app.client is None:
            st.session_state.app = TradingApp(
                api_key=st.session_state.api_key,
                api_secret=st.session_state.api_secret,
            )

    app = st.session_state.app

    # --------------------------------------------------------------
    # 4️⃣  Page header
    # --------------------------------------------------------------
    st.markdown('<h1 class="main-header">🚀 Binance Futures Trading Bot</h1>', unsafe_allow_html=True)

    # --------------------------------------------------------------
    # 5️⃣  Sidebar – account info (balance, positions, refresh)
    # --------------------------------------------------------------
    with st.sidebar:
        st.header("💰 Account Info")

        if st.button("🔄 Refresh Data"):
            # Public API – safe to use
            st.rerun()

        # USDT balance
        balance = app.get_account_balance()
        st.metric("USDT Balance", f"${balance:,.2f}")

        # Open positions count
        positions = app.get_positions()
        st.metric("Open Positions", len(positions))

        if positions:
            st.subheader("📊 Current Positions")
            for pos in positions:
                amt = float(pos["positionAmt"])
                side = "LONG" if amt > 0 else "SHORT"
                st.write(f"{pos['symbol']}: {abs(amt):.6f} ({side})")

    # --------------------------------------------------------------
    # 6️⃣  Main UI – market data, order form, history, quick actions
    # --------------------------------------------------------------
    col1, col2 = st.columns([2, 1])

    # ------------------------------------------------------------------
    # Left column – market data & order form
    # ------------------------------------------------------------------
    with col1:
        st.header("📊 Market Data")

        # Symbol selector
        symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT", "DOTUSDT", "LINKUSDT"]
        selected_symbol = st.selectbox(
            "Select Symbol", symbols, key="symbol_select"
        )

        # Current market price
        current_price = app.get_market_price(selected_symbol)
        st.metric(f"{selected_symbol} Price", f"${current_price:,.2f}")

        # ------------------------------------------------------------------
        # Order form (unchanged logic – only the surrounding TP/SL handling stays)
        # ------------------------------------------------------------------
        st.header("🛎️ Place Order")

        # --------------------------------------------------------------
        # Quick TP/SL % buttons (outside the form – needed because
        # st.button() cannot be inside a form)
        # --------------------------------------------------------------
        st.markdown("**Quick TP/SL %**")
        col_tp, col_sl = st.columns(2)

        with col_tp:
            if st.button("TP +2%", key="tp_2pct"):
                # For BUY -> TP above price, for SELL -> TP below price
                if st.session_state.get("side_select") == "BUY":
                    st.session_state.tp_input = current_price * 1.02
                else:
                    st.session_state.tp_input = current_price * 0.98

        with col_sl:
            if st.button("SL -2%", key="sl_2pct"):
                if st.session_state.get("side_select") == "BUY":
                    st.session_state.sl_input = current_price * 0.98
                else:
                    st.session_state.sl_input = current_price * 1.02

        # Initialise TP/SL session variables (only once)
        if "tp_input" not in st.session_state:
            st.session_state.tp_input = 0.0
        if "sl_input" not in st.session_state:
            st.session_state.sl_input = 0.0

        # ------------------------------------------------------------------
        # The actual order form (still inside a Streamlit form)
        # ------------------------------------------------------------------
        with st.form("order_form"):
            col1_form, col2_form, col3_form = st.columns(3)

            # ----------------------------------------------------------
            # Column 1 – side & order type
            # ----------------------------------------------------------
            with col1_form:
                side = st.selectbox("Side", ["BUY", "SELL"], key="side_select")
                order_type = st.selectbox(
                    "Order Type", ["MARKET", "LIMIT"], key="order_type_select"
                )

            # ----------------------------------------------------------
            # Column 2 – quantity & optional limit price
            # ----------------------------------------------------------
            with col2_form:
                quantity = st.number_input(
                    "Quantity",
                    min_value=0.002,
                    value=0.01,
                    step=0.001,
                    format="%.6f",
                    key="quantity_input",
                )
                if order_type == "LIMIT":
                    price = st.number_input(
                        "Price",
                        min_value=0.01,
                        value=current_price,
                        step=app.get_price_filter(selected_symbol),
                        format=f"%.{len(str(app.get_price_filter(selected_symbol)).split('.')[1])}f",
                        key="price_input",
                    )
                else:
                    price = None

            # ----------------------------------------------------------
            # Column 3 – optional TP / SL (use session‑state values)
            # ----------------------------------------------------------
            with col3_form:
                st.markdown(
                    '<p class="optional-field">Optional TP/SL (leave empty for none)</p>',
                    unsafe_allow_html=True,
                )

                tp_price_input = st.number_input(
                    "Take‑Profit",
                    min_value=0.0,
                    value=st.session_state.tp_input,
                    step=app.get_price_filter(selected_symbol),
                    format=f"%.{len(str(app.get_price_filter(selected_symbol)).split('.')[1])}f",
                    key="tp_input_form",
                    help="Enter 0 or leave empty for no TP",
                )
                sl_price_input = st.number_input(
                    "Stop‑Loss",
                    min_value=0.0,
                    value=st.session_state.sl_input,
                    step=app.get_price_filter(selected_symbol),
                    format=f"%.{len(str(app.get_price_filter(selected_symbol)).split('.')[1])}f",
                    key="sl_input_form",
                    help="Enter 0 or leave empty for no SL",
                )

            # ----------------------------------------------------------
            # Submit button (the only button inside the form)
            # ----------------------------------------------------------
            submitted = st.form_submit_button("🚀 Place Order")
            if submitted:
                try:
                    # ------------------- VALIDATE -------------------
                    sym = validate_symbol(selected_symbol)
                    sd = validate_side(side)
                    ot = validate_order_type(order_type)
                    qty = validate_quantity(str(quantity))

                    prc = (
                        validate_price(str(price))
                        if price and order_type == "LIMIT"
                        else None
                    )
                    tp = (
                        validate_price(str(tp_price_input))
                        if tp_price_input > 0
                        else None
                    )
                    sl = (
                        validate_price(str(sl_price_input))
                        if sl_price_input > 0
                        else None
                    )

                    # ------------------- PLACE MAIN ORDER -------------------
                    if ot == "LIMIT" and prc is None:
                        st.error("Price is required for LIMIT orders")
                        return

                    result = app.order_service.place_order(
                        symbol=sym, side=sd, order_type=ot, quantity=qty, price=prc
                    )
                    if not result.success:
                        st.error(f"❌ Order failed: {result.error_msg}")
                        return

                    st.success(f"✅ Order placed! ID: {result.order_id}")

                    # ------------------- OPTIONAL TP / SL -------------------
                    opposite_side = "SELL" if side == "BUY" else "BUY"

                    # ---- Take‑Profit -------------------------------------------------
                    if tp:
                        if (side == "BUY" and tp > current_price) or (
                            side == "SELL" and tp < current_price
                        ):
                            app.place_tp_sl_order(
                                symbol=sym,
                                side=opposite_side,
                                order_type="TAKE_PROFIT_MARKET",
                                quantity=qty,
                                stop_price=tp,
                            )
                            st.success(f"✅ TP placed @ ${tp:.2f}")
                        else:
                            st.warning(
                                f"⚠️ TP ${tp:.2f} not valid for {side} (must be {'above' if side == 'BUY' else 'below'} market ${current_price:.2f})"
                            )

                    # ---- Stop‑Loss -------------------------------------------------
                    if sl:
                        if (side == "BUY" and sl < current_price) or (
                            side == "SELL" and sl > current_price
                        ):
                            app.place_tp_sl_order(
                                symbol=sym,
                                side=opposite_side,
                                order_type="STOP_MARKET",
                                quantity=qty,
                                stop_price=sl,
                            )
                            st.success(f"✅ SL placed @ ${sl:.2f}")
                        else:
                            st.warning(
                                f"⚠️ SL ${sl:.2f} not valid for {side} (must be {'below' if side == 'BUY' else 'above'} market ${current_price:.2f})"
                            )

                    if not tp and not sl:
                        st.info("ℹ️ No TP/SL set (left empty)")

                    # Reset TP/SL fields for the next order
                    st.session_state.tp_input = 0.0
                    st.session_state.sl_input = 0.0

                except Exception as e:
                    st.error(f"❌ Unexpected error: {e}")

    # ------------------------------------------------------------------
    # Right column – order history, quick actions, risk management
    # ------------------------------------------------------------------
    with col2:
        st.header("📜 Order History")

        if st.button("🔄 Refresh Orders", key="refresh_orders"):
            try:
                orders = app.client.client.futures_get_all_orders(
                    symbol=selected_symbol, limit=10
                )
                if orders:
                    df = pd.DataFrame(orders)[
                        ["orderId", "symbol", "side", "type", "origQty", "price", "status", "time"]
                    ]
                    df["time"] = pd.to_datetime(df["time"], unit="ms")
                    st.dataframe(df.sort_values("time", ascending=False))
                else:
                    st.info("No orders found")
            except Exception as e:
                st.error(f"Error fetching orders: {e}")

        st.header("📈 Quick Actions")
        col_quick1, col_quick2 = st.columns(2)

        # ---- Market BUY 0.01 -------------------------------------------------
        with col_quick1:
            if st.button("🟢 Market BUY 0.01", key="quick_buy"):
                try:
                    res = app.order_service.place_order(
                        symbol=selected_symbol,
                        side="BUY",
                        order_type="MARKET",
                        quantity=0.01,
                    )
                    if res.success:
                        st.success("✅ Market BUY placed")
                    else:
                        st.error(res.error_msg)
                except Exception as e:
                    st.error(f"❌ {e}")

        # ---- Market SELL 0.01 ------------------------------------------------
        with col_quick2:
            if st.button("🔴 Market SELL 0.01", key="quick_sell"):
                try:
                    res = app.order_service.place_order(
                        symbol=selected_symbol,
                        side="SELL",
                        order_type="MARKET",
                        quantity=0.01,
                    )
                    if res.success:
                        st.success("✅ Market SELL placed")
                    else:
                        st.error(res.error_msg)
                except Exception as e:
                    st.error(f"❌ {e}")

        st.header("🛑 Risk Management")
        if st.button("🔴 Close All Positions", key="close_all"):
            try:
                pos = app.get_positions()
                if not pos:
                    st.info("No open positions")
                else:
                    for p in pos:
                        sym = p["symbol"]
                        amt = float(p["positionAmt"])
                        if amt == 0:
                            continue
                        close_side = "SELL" if amt > 0 else "BUY"
                        close_qty = abs(amt)
                        result = app.order_service.place_order(
                            symbol=sym,
                            side=close_side,
                            order_type="MARKET",
                            quantity=close_qty,
                        )
                        if result.success:
                            st.success(f"✅ Closed {sym}: {close_qty:.6f} ({close_side})")
                        else:
                            st.error(f"❌ Failed to close {sym}: {result.error_msg}")
            except Exception as e:
                st.error(f"❌ {e}")

# ----------------------------------------------------------------------
if __name__ == "__main__":
    main()
