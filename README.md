A professional trading bot for Binance Futures Testnet with Streamlit interface.

## Features

- 📊 **Real-time Market Data** - Live prices for major cryptocurrencies
- 🛎️ **Order Placement** - MARKET and LIMIT orders with TP/SL
- 📈 **Interactive UI** - Clean Streamlit web interface
- 💰 **Account Management** - Balance and positions tracking
- 📜 **Order History** - Recent orders display
- 🛑 **Risk Management** - Close all positions with one click
- ⚡ **Testnet Support** - Safe trading on Binance Testnet

Project Structure
binance-futures-bot/
├── bot/                    # Core bot modules
│   ├── __init__.py
│   ├── client.py          # Binance API wrapper
│   ├── orders.py          # Order service
│   ├── validators.py      # Input validation
│   ├── interactive.py     # CLI interface
│   ├── logging_config.py  # Logging setup
│   └── cli.py            # Command line interface
├── streamlit_app.py       # Web interface
├── requirements.txt       # Dependencies
├── .env.example          # Environment template
├── .gitignore            # Git ignore rules
└── README.md             # This file

## Quick Start

1. **Clone the repository:**
```bash
git clone https://github.com/Ansh7473/Trading-Bot-on-Binance-Futures-Testnet
cd Trading-Bot-on-Binance-Futures-Testnet


python -m venv .venv
# On Windows:
.venv\\Scripts\\activate
# On Mac/Linux:
source .venv/bin/activate

pip install -r requirements.txt


BINANCE_API_KEY=your_testnet_api_key
BINANCE_API_SECRET=your_testnet_api_secret


Getting API Credentials
Go to Binance Testnet
Create account or login
Go to API Management
Get from: https://testnet.binancefuture.com/
Create new API key
Copy API Key and Secret to .env file


Usage
Web Interface (Recommended)
streamlit run streamlit_app.py
Command Line
python -m bot.cli place-order
Features
Order Types
MARKET - Execute at current price
LIMIT - Execute at specified price
Risk Management
Take Profit - Auto close at profit target
Stop Loss - Auto close at loss limit
Close All - Close all positions instantly
Safety Features
Input validation
Error handling
Testnet only (no real funds)
Detailed logging
Important Notes
⚠️ Educational Use Only

Trading involves risk
Test with small amounts first
Never share API keys
Configured for Testnet only
Support
For issues:

Check the Issues page
Create new issue with details
