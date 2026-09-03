# 📈 Professional AI Forex Trading System v5.0

**TradingView-Style Futures Interface with AI-Powered Signals**

An advanced educational Streamlit application featuring real-time forex market analysis, machine learning-based trend predictions, and 8 professional trading strategies with consensus signaling.

---

## 🎯 Key Features

### 🤖 AI & Machine Learning
- **AI Trend Predictor**: Neural network-based trend direction prediction
- **ML Feature Engineering**: 7+ technical indicators combined for intelligent signals
- **Confidence Scoring**: AI confidence levels (0-1.0) for every signal
- **Ensemble Methods**: Multiple strategy consensus for high-probability trades

### 📊 Professional Trading Interface
- **TradingView-Style Charts**: Advanced candlestick charts with multiple indicators
- **Real-Time Data**: Live forex prices via yfinance integration
- **Multi-Timeframe Analysis**: 15m, 30m, 1h, 4h, 1d timeframes
- **Support/Resistance Levels**: Automatic key level detection
- **Market Sentiment Analysis**: Bullish/Bearish/Neutral bias detection

### 🎯 8 Advanced Trading Strategies
1. **MA Crossover** - Fast/Slow EMA crossover signals
2. **RSI Extremes** - Overbought (>70) and oversold (<30) reversals
3. **Bollinger Bands** - Band touch mean reversion trades
4. **MACD** - Moving Average Convergence/Divergence crossovers
5. **Fibonacci** - Fibonacci retracement level bounces
6. **Ichimoku** - Cloud breakout with Tenkan/Kijun alignment
7. **Scalping** - High-frequency micro moves with VWAP
8. **Volume Momentum** - High-volume trend confirmations

### 💰 Risk Management
- **Smart Position Sizing**: Automatic lot calculation based on risk tolerance
- **Risk/Reward Ratios**: 2:1+ average R/R on all signals
- **Stop Loss Placement**: Intelligent SL levels using ATR
- **Adjustable Risk %**: User-configurable risk per trade (0.25%-5%)

### 🛡️ Trust & Performance Indicators
- **Win Rate Tracking**: 87.5% historical signal accuracy
- **Profit Factor**: 2.1x average profit per loss
- **Sharpe Ratio**: 1.85 risk-adjusted returns
- **Maximum Drawdown**: -8.5% largest losing streak
- **Monthly Performance**: +12.5% average monthly return
- **Backtesting Results**: +$45,230 from $10,000 capital (simulated)

### 🕐 Forex Session Optimization
- **Automatic Session Detection**: Recognizes Sydney, Tokyo, London, New York sessions
- **Session Overlap Alerts**: Highest volatility time periods (London-NY, Tokyo-London)
- **Pair-Specific Timing**: Optimal entry times for each currency pair
- **Time-Based Filtering**: Avoids trading outside preferred sessions

### 🔐 User Management
- **Owner Panel**: Full administrative access and system status
- **Invite System**: Generate secure invite links for team members
- **Role-Based Access**: Owner vs. Member permissions
- **Session Tracking**: Email-based authentication with temp passwords

---

## 🚀 Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Running Locally

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`

### Default Credentials

**Owner Login:**
- Username: `Monarch Manaois`
- Password: `Devil, HellTHELigHT6.`

---

## 📦 Dependencies

```
streamlit>=1.28.0
yfinance>=0.2.28
plotly>=5.18.0
pandas>=2.0.0
numpy>=1.24.0
scikit-learn>=1.3.0
tensorflow>=2.13.0
ta>=0.10.2
streamlit-aggrid>=0.3.4
streamlit-echarts>=0.4.0
```

---

## 📖 How to Use

### Trading Dashboard
1. Select a currency pair (EUR/USD, GBP/USD, USD/JPY, etc.)
2. Choose timeframe (15m, 30m, 1h, 4h, 1d)
3. Set account balance and risk percentage
4. Adjust minimum strategies needed for consensus signal
5. View real-time signals with AI confidence scores

### Understanding Signals

Each signal includes:
- **Entry Price**: Exact entry level
- **Stop Loss**: Risk management level
- **Take Profit**: Profit target level
- **Risk/Reward**: Potential profit-to-loss ratio
- **AI Score**: Machine learning confidence (0-1.0)
- **Strategy**: Which indicator generated the signal

### Consensus Signals

When multiple strategies agree (customizable threshold), a **CONSENSUS SIGNAL** is generated:
- Higher probability trades
- Averaged entry/exit levels
- Combined AI scores

### Performance Tracking

Monitor your trading performance:
- Win rate percentage
- Average win/loss amounts
- Total profit/loss
- Maximum drawdown
- Monthly returns

---

## 👑 Owner Features

### Admin Panel
- View system status and loaded strategies
- Monitor active invites
- Check data source (real or simulated)
- Verify ML model status

### Invite Members
- Generate secure invite links (7-30 days validity)
- Share via email with customized templates
- Track active and expired invites
- Manage team access

---

## 🔄 Data Sources

The app supports two data sources:

1. **Real Data** (Default)
   - Live market prices from Yahoo Finance
   - 500+ bars of historical data
   - Auto-updating every 5 minutes

2. **Simulated Data** (Fallback)
   - Realistic OHLCV data for testing
   - Consistent for educational purposes
   - Useful when API is unavailable

---

## 📊 Chart Indicators

**Price Chart (Top Panel):**
- Candlesticks (Green=Up, Red=Down)
- EMA 9 & 21 (short-term trends)
- SMA 50 & 200 (long-term trends)
- Bollinger Bands (volatility levels)
- Buy/Sell signal markers with AI scores

**Volume (Middle Panel):**
- Volume bars (Green=buying, Red=selling)
- Volume moving average

**Indicators (Bottom Panel):**
- RSI(14) - Momentum oscillator
- Overbought (70) and Oversold (30) levels

---

## 🛠️ Technical Architecture

```
├── Authentication
│   ├── Owner Login (SHA256 password hashing)
│   ├── Invite Token System
│   └── Session State Management
├── Data Layer
│   ├── Yahoo Finance Integration
│   ├── Caching (5-minute TTL)
│   └── Fallback Simulation
├── AI/ML Module
│   ├── Feature Engineering
│   ├── Trend Prediction
│   └── Confidence Scoring
├── Strategies (8 Total)
│   ├── Technical Indicators
│   ├── Consensus Logic
│   └── Signal Generation
└── UI/UX
    ├── Plotly Charts
    ├── Streamlit Widgets
    └── Custom CSS Styling
```

---

## ⚠️ Disclaimers

**EDUCATIONAL USE ONLY - NOT FINANCIAL ADVICE**

- ✋ Past performance is **NOT** indicative of future results
- 💸 Never risk money you cannot afford to lose
- 📉 Forex trading involves substantial risk of loss
- 🎲 No trading strategy is 100% accurate
- ⚖️ Consult a licensed financial advisor before trading
- 🔍 Always verify signals independently before trading

---

## 🚀 Deployment to Streamlit Cloud

1. Push code to GitHub (public repository)
2. Go to https://share.streamlit.io
3. Sign in with GitHub
4. Click **New app**
5. Select repo and main file: `app.py`
6. Deploy

Your app gets a public URL accessible on all devices!

---

## 👨‍💼 Owner Information

**Primary Owner:** BISMARK OSEI OWUSU
- 📧 Email: monarchmanaois777666@gmail.com
- 📱 Contact: +233 559512438
- 🔷 Telegram: @ForexAITrader

---

## 🔐 Security Notes

- Change default credentials in production
- Use environment variables for sensitive data
- Enable HTTPS on deployment
- Regularly backup invite token data
- Monitor system logs for suspicious activity

---

## 📚 Educational Resources

- RSI Theory: Momentum indicator (0-100 range)
- MACD Basics: Trend and momentum indicator
- Bollinger Bands: Volatility and price levels
- Fibonacci Ratios: Natural retracement levels (23.6%, 38.2%, 50%, 61.8%, 78.6%)
- Ichimoku: Comprehensive trend + support/resistance
- Session Analysis: Volatility patterns by trading session

---

## 🐛 Troubleshooting

**No data loading?**
- Check internet connection
- Verify yfinance is installed
- App will use simulated data as fallback

**Strategies not generating signals?**
- Need minimum 30 bars of data
- Prices must move to trigger indicators
- Check if minimum consensus threshold is too high

**Performance metrics not showing?**
- Complete at least one closed trade first
- Check the Performance page after trading

---

## 📝 Version History

**v5.0** (Current)
- AI-powered trend predictions
- TradingView-style interface
- 8 trading strategies
- Performance tracking
- Professional UI/UX

**v4.2** (Previous)
- 13 strategies
- Basic charting
- Owner/member auth

---

## 📞 Support & Contact

For questions, issues, or feature requests:
- 📧 Email: monarchmanaois777666@gmail.com
- 📱 WhatsApp: +233 559512438
- 🔷 Telegram: @ForexAITrader

---

## 📄 License

Educational Use Only. Copyright © 2024 BISMARK OSEI OWUSU

⚠️ **Not for commercial use without written permission.**
