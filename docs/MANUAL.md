# EMA-MACD-VWAP Trading Bot User Manual

## Table of Contents

1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Running the Bot](#running-the-bot)
5. [Backtesting](#backtesting)
6. [Monitoring & Maintenance](#monitoring--maintenance)
7. [Troubleshooting](#troubleshooting)
8. [AWS Deployment](#aws-deployment)
9. [Frequently Asked Questions](#frequently-asked-questions)

## Introduction

The EMA-MACD-VWAP Trading Bot is a cryptocurrency trading automation tool designed to execute trades on the Bitget exchange based on a combination of technical indicators:

- Exponential Moving Average (EMA) crossovers
- Moving Average Convergence Divergence (MACD) crossovers
- Volume Weighted Average Price (VWAP) bands

The strategy is designed to identify potential trend reversals and momentum shifts, taking advantage of price movements while managing risk through predefined stop-loss and take-profit levels.

## Installation

### Prerequisites

- Python 3.8 or higher
- Git
- Bitget account with API access
- (Optional) AWS account for cloud deployment

### Local Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/bitget-trading-bot.git
cd bitget-trading-bot
```

2. Run the setup script:
```bash
chmod +x scripts/setup_env.sh
./scripts/setup_env.sh
```

This will:
- Create a Python virtual environment
- Install required dependencies
- Set up the initial configuration files

## Configuration

All configuration is managed through the `.env` file. Copy the example file and edit it with your settings:

```bash
cp .env.example .env
```

### Essential Configuration Parameters

#### Exchange API Credentials
```
BITGET_API_KEY=your_api_key_here
BITGET_SECRET_KEY=your_secret_key_here
BITGET_PASSPHRASE=your_passphrase_here
```

#### Trading Parameters
```
SYMBOL=BTC/USDT       # Trading pair
TIMEFRAME=15m         # Candlestick timeframe (15m, 1h, 4h, etc.)
RISK_PERCENTAGE=50    # Risk per trade (% of wallet)
MAX_OPEN_ORDERS=2     # Maximum concurrent open positions
MAX_DAILY_TRADES=6    # Maximum trades per day
```

#### Strategy Parameters
```
EMA_SHORT=9              # Short EMA period
EMA_LONG=21              # Long EMA period
MACD_FAST=12             # MACD fast period
MACD_SLOW=26             # MACD slow period
MACD_SIGNAL=9            # MACD signal period
VWAP_LOOKBACK=14         # VWAP calculation period
ATR_PERIOD=14            # ATR calculation period
STOP_LOSS_ATR_MULTIPLIER=2       # Stop loss (x ATR)
TAKE_PROFIT1_ATR_MULTIPLIER=3    # Take profit 1 (x ATR)
TAKE_PROFIT2_ATR_MULTIPLIER=5    # Take profit 2 (x ATR)
VWAP_BAND_THRESHOLD=0.0015       # Threshold for "near VWAP band" detection
```

#### Email Notifications
```
EMAIL_ENABLED=True
EMAIL_SENDER=your_email@example.com
EMAIL_PASSWORD=your_email_password
EMAIL_RECIPIENT=recipient@example.com
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
```

#### Trading Mode
```
TRADING_MODE=paper  # paper or live
```

For Gmail, you'll need to create an App Password if you have 2-factor authentication enabled.

## Running the Bot

### Live Trading

Activate the virtual environment:
```bash
source venv/bin/activate
```

Start the bot:
```bash
python -m src.main --mode live
```

The bot will:
1. Connect to Bitget using your API credentials
2. Fetch market data at regular intervals
3. Calculate technical indicators
4. Look for entry and exit signals based on the strategy
5. Execute trades when conditions are met
6. Send email notifications for trades and errors

### Paper Trading

For testing without risking real funds, set `TRADING_MODE=paper` in your `.env` file.

## Backtesting

Run a backtest to evaluate the strategy's performance on historical data:

```bash
python -m src.main --mode backtest --backtest-start 2023-01-01 --backtest-end 2023-02-01
```

This will:
1. Fetch historical data for the specified period
2. Simulate trades according to the strategy
3. Calculate performance metrics (win rate, return, max drawdown)
4. Display the results

## Monitoring & Maintenance

### Logs

Logs are stored in the `logs/` directory with date-based filenames. They contain detailed information about the bot's operations, including:

- Indicator calculations
- Trade signals
- Order execution
- Errors and warnings

### Email Notifications

If enabled, the bot will send emails for:
- New trade entries (with stop loss and take profit levels)
- Trade exits (including reason and profit/loss)
- Take profit 1's being reached (suggesting stop loss adjustment)
- Error conditions

## Troubleshooting

### Common Issues

1. **API Connection Errors**
   - Check your internet connection
   - Verify API keys are correct and have appropriate permissions
   - Ensure your IP is whitelisted in your Bitget account settings

2. **Order Placement Failures**
   - Check account balance
   - Verify minimum order size requirements
   - Check if the symbol is valid and tradeable

3. **Email Notification Issues**
   - For Gmail, ensure "Less secure app access" is enabled or use App Passwords
   - Check spam/junk folders
   - Verify SMTP settings

### Debugging

For more detailed logs, set `LOG_LEVEL=DEBUG` in your `.env` file.

## AWS Deployment

### Automated Deployment

1. Edit the `scripts/deploy_to_aws.sh` script with your EC2 instance details:
```bash
EC2_USER="ubuntu"
EC2_HOST="your-ec2-instance-public-dns"
EC2_KEY_PATH="~/.ssh/your-key.pem"
```

2. Run the deployment script:
```bash
chmod +x scripts/deploy_to_aws.sh
./scripts/deploy_to_aws.sh
```

### Manual Deployment

1. Launch an EC2 instance (t2.micro is sufficient)
2. Set up your security group to allow SSH access
3. Connect to your instance
4. Follow the installation steps for local setup
5. Create a systemd service:
```bash
sudo nano /etc/systemd/system/trading-bot.service
```

Add:
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

6. Enable and start the service:
```bash
sudo systemctl enable trading-bot
sudo systemctl start trading-bot
```

7. Check logs:
```bash
sudo journalctl -u trading-bot -f
```

## Frequently Asked Questions

### How much money should I allocate to this bot?

Only trade with funds you can afford to lose. Start with a small amount to test the bot's performance in your specific market conditions.

### Can I modify the strategy?

Yes! The strategy is implemented in `src/strategy/ema_macd_vwap_strategy.py`. You can modify the entry/exit conditions, risk management, or add new indicators.

### Is this bot profitable?

Past performance doesn't guarantee future returns. The bot's performance depends on market conditions, parameter settings, and risk management. Always backtest and paper trade before using real funds.

### How can I optimize the strategy parameters?

Run multiple backtests with different parameter combinations to find the optimal settings for your target market and timeframe.

### Does this bot work for other exchanges?

The bot is currently designed for Bitget, but it can be adapted for other exchanges supported by the CCXT library by modifying the `BitgetClient` class.

### What's the difference between paper trading and backtesting?

- Paper trading simulates trades in real-time with current market data but doesn't use real money
- Backtesting simulates trades on historical data to evaluate past performance

### How do I know if the bot is running correctly?

Check the logs for regular market data fetching, indicator calculations, and trade signal evaluations. You should also receive email notifications if configured. 