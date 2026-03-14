# bot/orders.py
from dataclasses import dataclass
from typing import Dict, Any

from .client import BinanceFuturesClient
from .logging_config import get_order_logger

order_logger = get_order_logger()

@dataclass
class OrderResult:
    success: bool
    order_id: int | None = None
    status: str | None = None
    executed_qty: str | None = None
    avg_price: str | None = None
    raw: Dict[str, Any] | None = None
    error_msg: str | None = None


class OrderService:
    """
    Encapsulates order‑placement workflow:
    1. Validate/transform input (done upstream by validators)
    2. Call BinanceFuturesClient
    3. Convert Binance response into a friendly `OrderResult`
    """
    def __init__(self):
        self.client = BinanceFuturesClient()

    def place_order(self,
                    symbol: str,
                    side: str,
                    order_type: str,
                    quantity: float,
                    price: float | None = None) -> OrderResult:
        
        try:
            # Log the order attempt
            price_str = f" @ ${price:.2f}" if price else ""
            order_logger.info(f"🛎️  {order_type} {side}: {quantity} {symbol}{price_str}")
            
            response = self.client.place_order(
                symbol=symbol,
                side=side,
                order_type=order_type,
                quantity=quantity,
                price=price,
            )

            # The most relevant fields Binance returns for a successful order:
            result = OrderResult(
                success=True,
                order_id=int(response.get("orderId")),
                status=response.get("status"),
                executed_qty=response.get("executedQty"),
                avg_price=response.get("avgPrice"),
                raw=response,
            )
            
            # Log successful order with details
            if result.executed_qty and float(result.executed_qty) > 0:
                order_logger.info(f"✅ FILLED: {result.executed_qty} {symbol} @ ${result.avg_price}")
            else:
                order_logger.info(f"✅ Order accepted: #{result.order_id} - {result.status}")
                
            return result

        except Exception as exc:
            error_msg = str(exc)
            order_logger.error(f"❌ Order failed: {error_msg}")
            return OrderResult(
                success=False,
                error_msg=error_msg,
                raw=None,
            )
