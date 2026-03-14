# --------------------------------------------------------------
# bot/interactive.py – interactive order wizard for Binance Futures
# --------------------------------------------------------------
import sys
import time
from typing import Optional, Tuple

import questionary
import typer                               # <-- needed for typer.Exit
from questionary import Choice, Separator
from rich.console import Console
from rich.table import Table

from .client import BinanceFuturesClient
from .orders import OrderService, OrderResult
from .validators import (
    validate_symbol,
    validate_side,
    validate_order_type,
    validate_quantity,
    validate_price,
)
from .logging_config import get_logger

logger = get_logger(__name__)
console = Console()

# ----------------------------------------------------------------------
# Safety ceiling (USDT). Adjust if you really need a larger budget.
# ----------------------------------------------------------------------
SAFE_MAX_NOTIONAL = 1_000.0   # 1 000 USDT is a comfortable default on test‑net


# ----------------------------------------------------------------------
# Helper – fetch the *MAX_NOTIONAL* filter for a symbol (Binance‑provided)
# ----------------------------------------------------------------------
def _get_max_notional(symbol: str) -> float:
    """
    Returns the maximum notional (USDT) allowed for a single order.
    If Binance does not expose the filter we fall back to a huge number,
    then later we cap it with our own SAFE_MAX_NOTIONAL.
    """
    client = BinanceFuturesClient()
    exchange_info = client.client.futures_exchange_info()
    for s in exchange_info["symbols"]:
        if s["symbol"] == symbol:
            for f in s["filters"]:
                if f["filterType"] == "MAX_NOTIONAL":
                    return float(f["maxNotional"])
    # No filter → return a huge placeholder
    return 1_000_000_000.0


# ----------------------------------------------------------------------
# Helper – poll the order until it reaches a terminal state
# ----------------------------------------------------------------------
def wait_for_fill(
    symbol: str,
    order_id: int,
    timeout: int = 30,
    interval: int = 2,
) -> dict:
    """
    Repeatedly call `futures_get_order` until the order status is a
    terminal state (FILLED, CANCELED, REJECTED, EXPIRED) or the timeout
    expires. Returns the final order dict.
    """
    client = BinanceFuturesClient()
    deadline = time.time() + timeout

    while time.time() < deadline:
        order = client.client.futures_get_order(symbol=symbol, orderId=order_id)
        status = order.get("status")
        logger.debug(f"Polling order {order_id}: status={status}")

        if status in ("FILLED", "CANCELED", "REJECTED", "EXPIRED"):
            return order

        time.sleep(interval)

    raise TimeoutError(
        f"Order {order_id} still has status {status} after {timeout}s"
    )


# ----------------------------------------------------------------------
# Helper – show the current market price (nice UX)
# ----------------------------------------------------------------------
def _show_current_price(symbol: str) -> float:
    client = BinanceFuturesClient()
    ticker = client.client.futures_symbol_ticker(symbol=symbol)
    price = float(ticker["price"])
    console.print(f"[dim]💹 Current market price for {symbol}: {price:.2f} USDT[/dim]")
    return price


# ----------------------------------------------------------------------
# Helper – ask for a quantity (supports =<USDT> shortcut & safety checks)
# ----------------------------------------------------------------------
def _ask_quantity(symbol: str, price: Optional[float]) -> float:
    """
    Prompt the user for a quantity.
    * Plain number → interpreted as BTC quantity.
    * `=<USDT>` → interpreted as the amount in USDT you want to spend.
    In both cases we compute the notional (price × qty) and reject the input
    if it exceeds the smaller of Binance's MAX_NOTIONAL and our own
    SAFE_MAX_NOTIONAL.
    """
    max_notional = _get_max_notional(symbol)
    effective_limit = min(max_notional, SAFE_MAX_NOTIONAL)

    while True:
        raw = questionary.text(
            "🪙 Quantity (or `=<USDT>` to specify notional)",
            validate=lambda x: x.strip() != "" or "Quantity required",
        ).ask()
        raw = raw.strip()

        # --------------------------------------------------------------
        # 1️⃣  Notional shortcut (`=<USDT>`)
        # --------------------------------------------------------------
        if raw.startswith("="):
            try:
                notional = float(raw[1:])
                if notional <= 0:
                    raise ValueError
            except ValueError:
                console.print("[red]❌ Notional must be a positive number after `=`[/red]")
                continue

            # Need current price if we don't already have one
            cur_price = price if price is not None else _show_current_price(symbol)
            qty = notional / cur_price
            calc_notional = qty * cur_price
            console.print(
                f"[dim]✅ Using price {cur_price:.2f} → computed quantity {qty:.6f} "
                f"(notional ≈ {calc_notional:.2f} USDT)[/dim]"
            )
        else:
            # --------------------------------------------------------------
            # 2️⃣  Plain BTC quantity
            # --------------------------------------------------------------
            try:
                qty = validate_quantity(raw)
                cur_price = price if price is not None else _show_current_price(symbol)
                calc_notional = qty * cur_price
            except ValueError as e:
                console.print(f"[red]❌ {e}[/red]")
                continue

        # --------------------------------------------------------------
        # 3️⃣  Enforce notional limit
        # --------------------------------------------------------------
        if calc_notional > effective_limit:
            console.print(
                f"[red]❌ Notional {calc_notional:.2f} USDT exceeds the allowed limit of "
                f"{effective_limit:.2f} USDT for {symbol}. "
                "Please lower the quantity or use a smaller notional (e.g. `=100`).[/red]"
            )
            continue

        # All good – return quantity rounded to 6 decimals (most futures accept that)
        return round(qty, 6)


# ----------------------------------------------------------------------
# Small prompting helpers (symbol, side, etc.)
# ----------------------------------------------------------------------
def _ask_symbol() -> str:
    while True:
        raw = questionary.text(
            "🔤 Symbol (e.g. BTCUSDT)",
            validate=lambda x: x.strip() != "" or "Symbol required",
        ).ask()
        try:
            return validate_symbol(raw.strip())
        except ValueError as e:
            console.print(f"[red]❌ {e}[/red]")


def _ask_side() -> str:
    return questionary.select(
        "↔️  Side",
        choices=[Choice("BUY"), Choice("SELL")],
        default="BUY",
    ).ask()


def _ask_order_type() -> str:
    return questionary.select(
        "📄 Order type",
        choices=[Choice("MARKET"), Choice("LIMIT")],
        default="MARKET",
    ).ask()


def _ask_price(symbol: str) -> float:
    """Prompt for a limit price – defaults to the current market price."""
    cur_price = _show_current_price(symbol)
    while True:
        raw = questionary.text(
            f"💰 Limit price (default = {cur_price:.2f})",
            default=str(cur_price),
        ).ask()
        try:
            return validate_price(raw)
        except ValueError as e:
            console.print(f"[red]❌ {e}[/red]")


def _ask_tp_sl() -> Tuple[Optional[float], Optional[float]]:
    """Prompt optionally for Take‑Profit and Stop‑Loss prices."""
    tp_raw = questionary.text(
        "🟢 Take‑Profit price (empty = none)",
        default="",
    ).ask()
    sl_raw = questionary.text(
        "🔴 Stop‑Loss price (empty = none)",
        default="",
    ).ask()
    tp_val = validate_price(tp_raw) if tp_raw.strip() != "" else None
    sl_val = validate_price(sl_raw) if sl_raw.strip() != "" else None
    return tp_val, sl_val


def _ask_reduce_only() -> bool:
    return questionary.confirm(
        "🔀 Reduce‑Only (close only existing positions?)",
        default=False,
    ).ask()


def _ask_tif() -> str:
    return questionary.select(
        "⏱️  Time‑in‑Force",
        choices=[Choice("GTC"), Choice("IOC"), Choice("FOK")],
        default="GTC",
    ).ask()


def _display_summary(
    symbol: str,
    side: str,
    order_type: str,
    qty: float,
    price: Optional[float],
    tp: Optional[float],
    sl: Optional[float],
    reduce_only: bool,
    tif: str,
):
    table = Table(title="🛎️  Order Summary", show_header=False, box=None)
    table.add_row("Symbol", symbol)
    table.add_row("Side", side)
    table.add_row("Type", order_type)
    table.add_row("Quantity", f"{qty:.6f}")
    if order_type == "LIMIT":
        table.add_row("Limit Price", f"{price:.2f}")
    if tp:
        table.add_row("Take‑Profit", f"{tp:.2f}")
    if sl:
        table.add_row("Stop‑Loss", f"{sl:.2f}")
    table.add_row("Reduce‑Only", "YES" if reduce_only else "NO")
    table.add_row("TIF", tif)
    console.print(table)


# ----------------------------------------------------------------------
# MAIN interactive flow – called from `cli.py`
# ----------------------------------------------------------------------
def interactive_place_order() -> None:
    """
    Full interactive workflow:
    1️⃣ Ask for every field (symbol, side, type, qty, price, TP/SL, etc.).
    2️⃣ Show a summary and ask for confirmation.
    3️⃣ Send the primary order.
    4️⃣ Poll until the order is filled (or fails) and display the final result.
    5️⃣ If TP/SL were supplied, place opposite‑side orders.
    """
    # ------------------- 1️⃣ Gather user input ------------------- #
    symbol = _ask_symbol()
    side = _ask_side()
    order_type = _ask_order_type()

    price: Optional[float] = None
    if order_type == "LIMIT":
        price = _ask_price(symbol)

    qty = _ask_quantity(symbol, price)

    tp_price, sl_price = _ask_tp_sl()
    reduce_only = _ask_reduce_only()
    tif = _ask_tif()

    # ------------------- 2️⃣ Show summary & confirm ------------------- #
    _display_summary(
        symbol=symbol,
        side=side,
        order_type=order_type,
        qty=qty,
        price=price,
        tp=tp_price,
        sl=sl_price,
        reduce_only=reduce_only,
        tif=tif,
    )

    if not questionary.confirm("🚀 Ready to send this order?", default=True).ask():
        console.print("[yellow]🛑 Order cancelled by user.[/yellow]")
        raise typer.Exit(code=0)          # <-- works now because typer is imported

    # ------------------- 3️⃣ Place the primary order ------------------- #
    service = OrderService()
    result: OrderResult = service.place_order(
        symbol=symbol,
        side=side,
        order_type=order_type,
        quantity=qty,
        price=price,
    )

    if not result.success:
        console.print(f"[red]❌ Order failed – {result.error_msg}[/red]")
        raise typer.Exit(code=1)

    console.print("\n[bold cyan]=== Binance Response (initial) ===[/bold cyan]")
    console.print("[green]✅ Order placed – now waiting for fill…[/green]")

    # ------------------- 4️⃣ Wait until the order reaches a terminal state ------------------- #
    try:
        final_order = wait_for_fill(
            symbol=symbol,
            order_id=result.order_id,
            timeout=30,       # seconds – tweak if you want to wait longer
            interval=2,
        )
        final_status = final_order.get("status")
        exec_qty = final_order.get("executedQty", "0")
        avg_price = final_order.get("avgPrice", "0")
        console.print(f"[bold]Final status:[/bold] {final_status}")
        console.print(f"[bold]ExecutedQty:[/bold] {exec_qty}")
        console.print(f"[bold]AvgPrice:[/bold] {avg_price}")
    except TimeoutError as te:
        console.print(f"[yellow]⚠️  {te} – the order may still be open.[/yellow]")
    except Exception as e:
        logger.exception("Error while polling order")
        console.print(f"[red]❌ Unexpected error while waiting for fill: {e}[/red]")
        raise typer.Exit(code=1)

    # ------------------- 5️⃣ Optional TP / SL orders ------------------- #
    if tp_price or sl_price:
        opposite_side = "SELL" if side == "BUY" else "BUY"
        client = BinanceFuturesClient()

        # ---- Take‑Profit -------------------------------------------------
        if tp_price:
            try:
                logger.info("Placing TP order")
                client.client.futures_create_order(
                    symbol=symbol,
                    side=opposite_side,
                    type="TAKE_PROFIT_LIMIT",
                    quantity=qty,
                    price=tp_price,
                    stopPrice=tp_price,
                    timeInForce=tif,
                    reduceOnly=reduce_only,
                )
                console.print("[green]✅ Take‑Profit order placed[/green]")
            except Exception as e:
                logger.error(f"Failed to place TP: {e}")
                console.print("[red]❌ Could not place TP order[/red]")

        # ---- Stop‑Loss -------------------------------------------------
        if sl_price:
            try:
                logger.info("Placing SL order")
                client.client.futures_create_order(
                    symbol=symbol,
                    side=opposite_side,
                    type="STOP_MARKET",
                    quantity=qty,
                    stopPrice=sl_price,
                    reduceOnly=reduce_only,
                    timeInForce=tif,
                )
                console.print("[green]✅ Stop‑Loss order placed[/green]")
            except Exception as e:
                logger.error(f"Failed to place SL: {e}")
                console.print("[red]❌ Could not place SL order[/red]")

    # ------------------------------------------------------------------
    # Finished – exit with success
    # ------------------------------------------------------------------
    raise typer.Exit(code=0)
