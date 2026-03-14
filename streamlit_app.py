# streamlit_app.py
import streamlit as st
import pandas as pd
from datetime import datetime
import time

# Import your existing bot components
from bot.client import BinanceFuturesClient
from bot.orders import OrderService, OrderResult
from bot.validators import validate_symbol, validate_side, validate_order_type, validate_quantity, validate_price
from bot.logging_config import get_logger

logger = get_logger(__name__)

# Page configuration
st.set_page_config(
    page_title="Binance Futures Trading Bot",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #00D4AA;
        text-align: center;
        margin-bottom: 2rem;
    }
    .success-box {
        background-color: #00D4AA20;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #00D4AA;
    }
    .error-box {
        background-color: #FF4B4B20;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #FF4B4B;
    }
    .metric-card {
        background-color: #1E1E1E;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
    }
    .optional-field {
        color: #888;
        font-style: italic;
    }
</style>
""", unsafe_allow_html=True)

class TradingApp:
    def __init__(self):
        try:
            self.client = BinanceFuturesClient()
            self.order_service = OrderService()
            st.success("✅ Connected to Binance Futures Testnet")
        except Exception as e:
            st.error(f"❌ Failed to initialize: {e}")
    
    def get_account_balance(self):
        """Get USDT balance"""
        try:
            balance = self.client.client.futures_account_balance()
            for item in balance:
                if item['asset'] == 'USDT':
                    return float(item['balance'])
            return 0.0
        except Exception as e:
            logger.error(f"Error getting balance: {e}")
            return 0.0
    
    def get_positions(self):
        """Get current positions"""
        try:
            positions = self.client.client.futures_account()['positions']
            return [p for p in positions if float(p['positionAmt']) != 0]
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return []
    
    def get_market_price(self, symbol):
        """Get current market price"""
        try:
            ticker = self.client.client.futures_symbol_ticker(symbol=symbol)
            return float(ticker['price'])
        except Exception as e:
            logger.error(f"Error getting price for {symbol}: {e}")
            return 0.0
    
    def get_symbol_info(self, symbol):
        """Get symbol information including price filters"""
        try:
            exchange_info = self.client.client.futures_exchange_info()
            for s in exchange_info['symbols']:
                if s['symbol'] == symbol:
                    return s
            return None
        except Exception as e:
            logger.error(f"Error getting symbol info: {e}")
            return None
    
    def get_price_filter(self, symbol):
        """Get price filter for a symbol"""
        symbol_info = self.get_symbol_info(symbol)
        if symbol_info:
            for f in symbol_info['filters']:
                if f['filterType'] == 'PRICE_FILTER':
                    return float(f['tickSize'])
        return 0.01  # Default
    
    def place_tp_sl_order(self, symbol, side, order_type, quantity, price=None, stop_price=None):
        """Place TP/SL orders with proper parameters"""
        try:
            payload = {
                "symbol": symbol,
                "side": side,
                "type": order_type,
                "quantity": quantity,
            }
            
            # For TAKE_PROFIT and STOP orders
            if order_type in ["TAKE_PROFIT", "TAKE_PROFIT_MARKET", "STOP", "STOP_MARKET"]:
                if stop_price:
                    payload["stopPrice"] = stop_price
            
            # For LIMIT variants
            if order_type in ["TAKE_PROFIT_LIMIT", "STOP_LIMIT"]:
                if price is None:
                    raise ValueError(f"Price is required for {order_type} orders")
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

def main():
    st.markdown('<h1 class="main-header">🚀 Binance Futures Trading Bot</h1>', unsafe_allow_html=True)
    
    # Initialize app
    if 'app' not in st.session_state:
        st.session_state.app = TradingApp()
    
    app = st.session_state.app
    
    # Sidebar - Account Info
    with st.sidebar:
        st.header("💰 Account Info")
        
        # Refresh button
        if st.button("🔄 Refresh Data"):
            st.rerun()
        
        # Balance
        balance = app.get_account_balance()
        st.metric("USDT Balance", f"${balance:,.2f}")
        
        # Positions
        positions = app.get_positions()
        st.metric("Open Positions", len(positions))
        
        if positions:
            st.subheader("📊 Current Positions")
            for pos in positions:
                position_amt = float(pos['positionAmt'])
                if position_amt != 0:
                    side = "LONG" if position_amt > 0 else "SHORT"
                    st.write(f"{pos['symbol']}: {abs(position_amt):.6f} ({side})")
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("📊 Market Data")
        
        # Symbol selector
        symbols = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'DOTUSDT', 'LINKUSDT']
        selected_symbol = st.selectbox("Select Symbol", symbols, key="symbol_select")
        
        # Real-time price
        current_price = app.get_market_price(selected_symbol)
        st.metric(f"{selected_symbol} Price", f"${current_price:,.2f}")
        
        # Get price filter for the symbol
        tick_size = app.get_price_filter(selected_symbol)
        
        # Order form
        st.header("🛎️ Place Order")
        
        # Initialize session state for TP/SL if not exists
        if 'tp_input' not in st.session_state:
            st.session_state.tp_input = 0.0
        if 'sl_input' not in st.session_state:
            st.session_state.sl_input = 0.0
        
        # Quick percentage buttons (outside the form)
        st.markdown("**Quick TP/SL %**")
        col_tp, col_sl = st.columns(2)
        with col_tp:
            if st.button("TP +2%", key="tp_2pct"):
                # Calculate TP based on side
                if 'side_select' in st.session_state and st.session_state.side_select == "BUY":
                    st.session_state.tp_input = current_price * 1.02
                else:
                    st.session_state.tp_input = current_price * 0.98
                st.rerun()
        with col_sl:
            if st.button("SL -2%", key="sl_2pct"):
                # Calculate SL based on side
                if 'side_select' in st.session_state and st.session_state.side_select == "BUY":
                    st.session_state.sl_input = current_price * 0.98
                else:
                    st.session_state.sl_input = current_price * 1.02
                st.rerun()
        
        with st.form("order_form"):
            col1_form, col2_form, col3_form = st.columns(3)
            
            with col1_form:
                side = st.selectbox("Side", ["BUY", "SELL"], key="side_select")
                order_type = st.selectbox("Order Type", ["MARKET", "LIMIT"], key="order_type_select")
            
            with col2_form:
                # Changed min_value from 0.001 to 0.002 as requested
                quantity = st.number_input("Quantity", min_value=0.002, value=0.01, step=0.001, format="%.6f", key="quantity_input")
                if order_type == "LIMIT":
                    price = st.number_input("Price", min_value=0.01, value=current_price, step=tick_size, format=f"%.{len(str(tick_size).split('.')[1])}f", key="price_input")
                else:
                    price = None
            
            with col3_form:
                st.markdown('<p class="optional-field">Optional TP/SL (leave empty for none)</p>', unsafe_allow_html=True)
                
                # TP/SL inputs - use session state values
                tp_price_input = st.number_input(
                    "Take Profit Price", 
                    min_value=0.0,  # Allow 0 to indicate no TP
                    value=st.session_state.tp_input,  # Use session state
                    step=tick_size, 
                    format=f"%.{len(str(tick_size).split('.')[1])}f", 
                    key="tp_input_form",
                    help="Enter 0 or leave as 0 for no Take Profit"
                )
                
                sl_price_input = st.number_input(
                    "Stop Loss Price", 
                    min_value=0.0,  # Allow 0 to indicate no SL
                    value=st.session_state.sl_input,  # Use session state
                    step=tick_size, 
                    format=f"%.{len(str(tick_size).split('.')[1])}f", 
                    key="sl_input_form",
                    help="Enter 0 or leave as 0 for no Stop Loss"
                )
            
            # Submit button inside the form
            submitted = st.form_submit_button("🚀 Place Order")
            
            if submitted:
                try:
                    # Validate inputs
                    sym = validate_symbol(selected_symbol)
                    sd = validate_side(side)
                    ot = validate_order_type(order_type)
                    qty = validate_quantity(str(quantity))
                    
                    # Handle optional prices
                    prc = validate_price(str(price)) if price and order_type == "LIMIT" else None
                    
                    # Handle TP/SL - only validate if > 0
                    tp = None
                    sl = None
                    
                    if tp_price_input > 0:
                        tp = validate_price(str(tp_price_input))
                    
                    if sl_price_input > 0:
                        sl = validate_price(str(sl_price_input))
                    
                    if ot == "LIMIT" and prc is None:
                        st.error("Price is required for LIMIT orders")
                    else:
                        # Place main order
                        result = app.order_service.place_order(
                            symbol=sym, side=sd, order_type=ot, quantity=qty, price=prc
                        )
                        
                        if result.success:
                            st.success(f"✅ Order placed successfully! Order ID: {result.order_id}")
                            
                            # Place TP/SL orders if specified
                            opposite_side = "SELL" if side == "BUY" else "BUY"
                            
                            if tp and tp > 0:
                                try:
                                    # Check if TP is valid (above price for BUY, below for SELL)
                                    if (side == "BUY" and tp > current_price) or (side == "SELL" and tp < current_price):
                                        # Use TAKE_PROFIT_MARKET instead of TAKE_PROFIT_LIMIT
                                        app.place_tp_sl_order(
                                            symbol=sym, side=opposite_side, order_type="TAKE_PROFIT_MARKET",
                                            quantity=qty, stop_price=tp
                                        )
                                        st.success(f"✅ Take Profit order placed at ${tp:.2f}")
                                    else:
                                        st.warning(f"⚠️ TP price ${tp:.2f} is not valid for {side} order (should be {'above' if side == 'BUY' else 'below'} current price ${current_price:.2f})")
                                except Exception as e:
                                    st.error(f"❌ Failed to place TP: {e}")
                            
                            if sl and sl > 0:
                                try:
                                    # Check if SL is valid (below price for BUY, above for SELL)
                                    if (side == "BUY" and sl < current_price) or (side == "SELL" and sl > current_price):
                                        # Use STOP_MARKET for stop loss
                                        app.place_tp_sl_order(
                                            symbol=sym, side=opposite_side, order_type="STOP_MARKET",
                                            quantity=qty, stop_price=sl
                                        )
                                        st.success(f"✅ Stop Loss order placed at ${sl:.2f}")
                                    else:
                                        st.warning(f"⚠️ SL price ${sl:.2f} is not valid for {side} order (should be {'below' if side == 'BUY' else 'above'} current price ${current_price:.2f})")
                                except Exception as e:
                                    st.error(f"❌ Failed to place SL: {e}")
                            
                            if not tp and not sl:
                                st.info("ℹ️ No TP/SL orders placed (left empty)")
                            
                            # Reset TP/SL inputs after successful order
                            st.session_state.tp_input = 0.0
                            st.session_state.sl_input = 0.0
                                
                        else:
                            st.error(f"❌ Order failed: {result.error_msg}")
                            
                except Exception as e:
                    st.error(f"❌ Error: {e}")
    
    with col2:
        st.header("📜 Order History")
        
        # Simple order history (you'd typically store this in a database)
        if st.button("🔄 Refresh Orders", key="refresh_orders"):
            try:
                orders = app.client.client.futures_get_all_orders(symbol=selected_symbol, limit=10)
                if orders:
                    df = pd.DataFrame(orders)[['orderId', 'symbol', 'side', 'type', 'origQty', 'price', 'status', 'time']]
                    df['time'] = pd.to_datetime(df['time'], unit='ms')
                    st.dataframe(df.sort_values('time', ascending=False))
                else:
                    st.info("No orders found")
            except Exception as e:
                st.error(f"Error fetching orders: {e}")
        
        st.header("📈 Quick Actions")
        
        # Quick market orders
        col1_quick, col2_quick = st.columns(2)
        
        with col1_quick:
            if st.button("🟢 Market BUY 0.01", key="quick_buy"):
                try:
                    result = app.order_service.place_order(
                        symbol=selected_symbol, side="BUY", order_type="MARKET", quantity=0.01
                    )
                    if result.success:
                        st.success("✅ Market BUY order placed")
                    else:
                        st.error(f"❌ {result.error_msg}")
                except Exception as e:
                    st.error(f"❌ Error: {e}")
        
        with col2_quick:
            if st.button("🔴 Market SELL 0.01", key="quick_sell"):
                try:
                    result = app.order_service.place_order(
                        symbol=selected_symbol, side="SELL", order_type="MARKET", quantity=0.01
                    )
                    if result.success:
                        st.success("✅ Market SELL order placed")
                    else:
                        st.error(f"❌ {result.error_msg}")
                except Exception as e:
                    st.error(f"❌ Error: {e}")
        
        # Close all positions button
        st.header("🛑 Risk Management")
        if st.button("🔴 Close All Positions", key="close_all"):
            try:
                positions = app.get_positions()
                if not positions:
                    st.info("No open positions to close")
                else:
                    for pos in positions:
                        symbol = pos['symbol']
                        position_amt = float(pos['positionAmt'])
                        if position_amt != 0:
                            # Determine side to close (opposite of current position)
                            close_side = "SELL" if position_amt > 0 else "BUY"
                            close_qty = abs(position_amt)
                            
                            result = app.order_service.place_order(
                                symbol=symbol, side=close_side, order_type="MARKET", quantity=close_qty
                            )
                            if result.success:
                                st.success(f"✅ Closed {symbol} position: {close_qty:.6f} ({close_side})")
                            else:
                                st.error(f"❌ Failed to close {symbol}: {result.error_msg}")
            except Exception as e:
                st.error(f"❌ Error closing positions: {e}")

if __name__ == "__main__":
    main()
