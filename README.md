# 🚀 Binance Futures Testnet Trading Bot

A professional-grade trading bot with a sleek **Streamlit interface** designed for safe, real-time trading on the Binance Futures Testnet. Perfect for testing strategies and managing positions without risking real capital.

---

[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue?logo=python)](https://www.python.org/downloads/)
[![Streamlit 1.38+](https://img.shields.io/badge/streamlit-1.38%2B-ff4b4b?logo=streamlit)](https://streamlit.io/)
[![Binance API](https://img.shields.io/badge/binance-api-orange?logo=binance)](https://binance-docs.github.io/apidocs/futures/en/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Testnet](https://img.shields.io/badge/environment-testnet-lightgrey)](#-quick-start)

---


## ✨ Features

* 📊 **Real-time Market Data** – Live price tracking for major cryptocurrencies.
* 🛎️ **Advanced Order Placement** – Support for **MARKET** and **LIMIT** orders with integrated **Take Profit (TP)** and **Stop Loss (SL)**.
* 📈 **Interactive UI** – A modern, clean web dashboard built with Streamlit.
* 💰 **Account Management** – Live tracking of your balance, margin, and open positions.
* 📜 **Order History** – Easy access to your recent trade history and logs.
* 🛑 **Risk Management** – One-click **"Close All Positions"** panic button for instant exit.


---

## 📂 Project Structure

```text
binance-futures-bot/
├── bot/                   # Core Logic
│   ├── client.py          # Binance API Wrapper
│   ├── orders.py          # Order Execution Service
│   ├── validators.py      # Input Safety Checks
│   ├── logging_config.py  # Logging Setup
│   └── cli.py             # Command Line Interface
├── streamlit_app.py       # Web Dashboard
├── .env.example           # Environment Template
├── requirements.txt       # Dependencies
└── README.md              # Project Documentation
## Quick Start

🛠️ Quick Start
Follow these steps to get your trading bot up and running in minutes.


### **Step 1:** Clone the repository
```bash
git clone https://github.com/Ansh7473/union_autobot.git
cd union_autobot
```

### **Step 1:** Clone the repository
```bash
git clone https://github.com/Ansh7473/Trading-Bot-on-Binance-Futures-Testnet
cd Trading-Bot-on-Binance-Futures-Testnet
2. Set Up Virtual Environment
```

### **Step 2:** Set Up Virtual Environment
```bash

python -m venv .venv
.venv\Scripts\activate

```
### **Step 3:** Dependencies
```bash

pip install -r requirements.txt

```

### **Step 4:** Set Up env
```bash

BINANCE_API_KEY=your_testnet_api_key
BINANCE_API_SECRET=your_testnet_api_secret

```


```bash
python3 -m venv .venv
source .venv/bin/activate
 Install Dependencies
```
### **Step 5:** How To Obtain Keys 

```bash
Go to Binance Futures Testnet. 

Log in https://demo.binance.com/en/my/wallet/demo/main and navigate to API Management.

Create a new API Key and Secret.

Create a file named .env in the root folder and add your credentials:

```
### **Step 6:** How To Use

🚀 Usage
🖥️ Web Interface (Recommended)
Launch the interactive dashboard to manage trades visually:
```bash
streamlit run streamlit_app.py


```
⌨️ Command Line Interface
Execute orders directly from the terminal
```bash


python cli.py interactive

```
### INFO
🛡️ Safety & Risk Management
Input Validation: Every order is checked for valid syntax and bounds before being sent to the exchange.

Error Handling: Detailed logging and visual alerts for failed API calls or insufficient margin.

Testnet Only: The bot is pre-configured for the Testnet environment to ensure no real funds are ever used.

### ⚠️ Important Notes
[!WARNING]

Educational Use Only: This software is for educational and testing purposes. Cryptocurrency trading involves significant risk. Always start with small position sizes even on Testnet.

Privacy: Never share your .env file or commit it to GitHub.

API Security: Ensure your Testnet API keys have "Futures" permissions enabled.

### 🤝 Support & Contribution
Found a bug or have a feature request?

Check the Issues page.

Open a new issue with detailed steps to reproduce.

Pull requests are welcome!

### Created by Ansh7473
