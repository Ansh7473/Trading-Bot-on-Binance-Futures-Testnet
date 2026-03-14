#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
cli.py – entry point for the Binance Futures Testnet trading bot
"""

import sys
from typing import Optional

import typer

# Minimal imports only
from bot.orders import OrderService
from bot.validators import (
    validate_symbol,
    validate_side,
    validate_order_type,
    validate_quantity,
    validate_price,
)
from bot.logging_config import get_logger

logger = get_logger(__name__)

# Create Typer app FIRST (before any other imports that might register commands)
app = typer.Typer(add_completion=False, help="✅ Binance Futures Testnet trading bot")

# Import interactive AFTER creating app to avoid any command registration issues
from bot.interactive import interactive_place_order

order_service = OrderService()

@app.command(name="place-order")
def place_order(
    symbol: str = typer.Option(..., "--symbol", "-s", help="Trading pair, e.g. BTCUSDT"),
    side: str = typer.Option(..., "--side", "-S", help="BUY or SELL"),
    order_type: str = typer.Option(..., "--type", "-t", help="MARKET or LIMIT"),
    quantity: str = typer.Option(..., "--quantity", "-q", help="Order quantity"),
    price: Optional[str] = typer.Option(None, "--price", "-p", help="Limit price"),
):
    """Place a market or limit order."""
    try:
        sym = validate_symbol(symbol)
        sd = validate_side(side)
        ot = validate_order_type(order_type)
        qty = validate_quantity(quantity)
        prc = validate_price(price)

        if ot == "LIMIT" and prc is None:
            raise ValueError("price is required for LIMIT orders")
    except ValueError as ve:
        logger.error(f"❌ Validation error: {ve}")
        raise typer.Exit(code=1)

    result = order_service.place_order(
        symbol=sym, side=sd, order_type=ot, quantity=qty, price=prc
    )

    typer.echo("\n=== Order Summary ===")
    typer.echo(f"Symbol: {sym}, Side: {sd}, Type: {ot}, Quantity: {qty}")
    if ot == "LIMIT":
        typer.echo(f"Price: {prc}")

    typer.echo("\n=== Binance Response ===")
    if result.success:
        typer.echo("✅ Order placed successfully")
        typer.echo(f"orderId: {result.order_id}, status: {result.status}")
        raise typer.Exit(code=0)
    else:
        typer.echo(f"❌ Order failed – {result.error_msg}")
        raise typer.Exit(code=1)

@app.command()
def interactive():
    """Launch the interactive wizard."""
    interactive_place_order()

def main():
    try:
        app()
    except Exception as exc:
        logger.exception(f"Unhandled exception: {exc}")
        sys.exit(1)

if __name__ == "__main__":
    main()
