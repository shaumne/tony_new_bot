# EMA-MACD-VWAP Trading Bot for Bitget

A cryptocurrency trading bot that implements a strategy based on EMA, MACD, and VWAP indicators on the Bitget exchange.

## Strategy Description

The trading strategy places orders based on the following conditions:

### Long Entry
- EMA (9,21) bullish crossover and MACD (12,26) bullish crossover at or around the VWAP lower band
- EMA (9,21) bullish crossover and MACD (12,26) bullish crossover at or around the VWAP middle line
- EMA (9,21) bullish crossover and MACD (12,26) bullish crossover at or around the VWAP upper band

### Short Entry
- EMA (9,21) bearish crossover and MACD (12,26) bearish crossover at or around the VWAP lower band
- EMA (9,21) bearish crossover and MACD (12,26) bearish crossover at or around the VWAP middle line
- EMA (9,21) bearish crossover and MACD (12,26) bearish crossover at or around the VWAP upper band

### Risk Management
- Stop Loss: 2X ATR from entry price
- Take Profit 1: 3X ATR from entry price
- Take Profit 2: 5X ATR from entry price

### Exit Conditions
- Close Long order at both EMA and MACD bearish crossover
- Close Short order at both EMA and MACD bullish crossover

### Trade Parameters
- Risk per trade: 50% of wallet amount (configurable)
- Maximum number of open orders: 2 (configurable)
- Maximum trades per day: 6 (configurable)

## Installation

### Prerequisites
- Python 3.8 or higher
- Bitget account with API keys

### Setup

1. Clone the repository:
```bash
git clone https://github.com/shaumne/tony_new_bot
cd bitget-trading-bot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file from the provided example:
```bash
cp .env.example .env
```

4. Edit the `.env` file with your Bitget API credentials and preferences:
```
# Exchange API credentials
BITGET_API_KEY=your_api_key_here
BITGET_SECRET_KEY=your_secret_key_here
BITGET_PASSPHRASE=your_passphrase_here

# Trading parameters
SYMBOL=BTC/USDT
TIMEFRAME=15m
RISK_PERCENTAGE=50
MAX_OPEN_ORDERS=2
MAX_DAILY_TRADES=6

# Email notification settings
EMAIL_ENABLED=True
EMAIL_SENDER=your_email@example.com
EMAIL_PASSWORD=your_email_password
EMAIL_RECIPIENT=recipient@example.com
```

## Usage

### Running the Bot

To start the trading bot in live mode:
```bash
python -m src.main --mode live
```

To run in paper trading mode (set `TRADING_MODE=paper` in your `.env` file).

### Backtesting

To run a backtest for a specific period:
```bash
python -m src.main --mode backtest --backtest-start 2023-01-01 --backtest-end 2023-02-01
```

Or use the dates configured in your `.env` file:
```bash
python -m src.main --mode backtest
```

## AWS Deployment

### EC2 Setup

1. Launch an EC2 instance (t2.micro should be sufficient)
2. Install required packages:
```bash
sudo apt update
sudo apt install -y python3-pip git
```

3. Clone the repository:
```bash
git clone https://github.com/yourusername/bitget-trading-bot.git
cd bitget-trading-bot
```

4. Install dependencies:
```bash
pip3 install -r requirements.txt
```

5. Create and configure your `.env` file

### Running as a Service

Create a systemd service file:
```bash
sudo nano /etc/systemd/system/trading-bot.service
```

Add the following content:
```
[Unit]
Description=Trading Bot Service
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/bitget-trading-bot
ExecStart=/usr/bin/python3 -m src.main --mode live
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl enable trading-bot
sudo systemctl start trading-bot
```

Check the status:
```bash
sudo systemctl status trading-bot
```

View logs:
```bash
sudo journalctl -u trading-bot -f
```

## Monitoring and Maintenance

### Logs
Logs are saved in the `logs/` directory with a date-based filename.

### Email Notifications
The bot sends email notifications for:
- New trades
- Take profit/stop loss hits
- Error conditions

## Customization

Most parameters can be configured through the `.env` file. For more advanced customization, you can modify:

- Strategy parameters in `src/strategy/ema_macd_vwap_strategy.py`
- Indicator calculations in `src/indicators/technical_indicators.py`
- Exchange interaction in `src/data/bitget_client.py`

## Troubleshooting

Common issues:
- API connection errors: Check your API keys and internet connection
- Insufficient balance: Ensure you have enough funds for trading
- Order placement failures: Check exchange-specific order requirements

## License

This project is licensed under the MIT License. 