# 🛢 Oil Market Intelligence

> **Live dashboard:** [oil-intelligence.streamlit.app](https://oil-intelligence.streamlit.app)  
> **Built by:** Saujas Purohit | MSc Geo-Energy with ML & Data Science, Imperial College London

A live oil market analysis tool monitoring the balance between **crude supply, storage, demand, and pricing** using weekly EIA data — replicating the kind of supply/demand signal analysis used by energy market analysts at firms like Wood Mackenzie, LSEG, Shell, and BP.

---

## Live Dashboard

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://oil-intelligence.streamlit.app)

---

## What It Does

The dashboard tracks six interconnected signals across the oil value chain:

| Signal | What it measures | Why it matters |
|--------|-----------------|----------------|
| **Inventory signal** | Weekly US crude stock changes (EIA) | Core supply/demand balance indicator |
| **Crack spread (3-2-1)** | Refinery profit margin | Leading indicator of crude demand |
| **WTI-Brent spread** | Geopolitical risk premium | US vs global market dynamics |
| **Signal backtest** | Historical predictive power of the inventory signal | Validates the analytical framework |
| **Refinery inputs** | Crude volumes processed by US refineries | Actual demand-side confirmation |
| **Market regime** | Combined signal classification | Single-view market state summary |

---

## Key Features

- **Live KPI metrics** — Brent, WTI, WTI-Brent spread, crack spread, inventory signal, market regime updated weekly
- **Auto-generated market commentary** — plain-English interpretation of current market signals
- **Signal backtest** — tests whether the inventory signal predicts forward Brent returns across 1, 4, 8, and 13-week horizons, with cumulative PnL vs buy-and-hold benchmark
- **Market regime matrix** — classifies the market into seven states (Demand-driven bull, Supply shock, Demand destruction etc.) by combining inventory and crack spread signals
- **Geopolitical annotations** — WTI-Brent spread chart annotated with key market events (OPEC cuts, Iran sanctions, Russia-Ukraine)
- **Adjustable date range** — analyse any period from 2010 to present

---

## Project Structure

```
oil-intelligence/
├── src/
│   ├── data_loader.py   # All EIA data fetching
│   ├── signals.py       # Signal calculations and backtest logic
│   └── charts.py        # All matplotlib chart functions
├── dashboard/
│   └── app.py           # Streamlit app
├── notebooks/
│   ├── 01_inventory_signal.ipynb
│   └── 02_crack_spread.ipynb
├── data/                # Local CSV cache
├── .env.example         # API key template
├── requirements.txt
└── README.md
```

---

## Quickstart

```bash
# 1. Clone the repo
git clone https://github.com/SaujP/oil-intelligence.git
cd oil-intelligence

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate   # Mac/Linux
# venv\Scripts\activate   # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Add your EIA API key
cp .env.example .env
# Edit .env and paste your key
# Get a free key at: https://www.eia.gov/opendata/

# 5. Run the dashboard
streamlit run dashboard/app.py
```

---

## Data Sources

All data sourced from the **US Energy Information Administration (EIA)** — the official US government energy statistics agency. No paid subscriptions required.

| Dataset | Source | Frequency |
|---------|--------|-----------|
| US Crude Inventory | EIA Weekly Petroleum Status Report | Weekly |
| Brent & WTI Spot Prices | EIA Petroleum Spot Prices Excel | Weekly |
| RBOB Gasoline & Heating Oil | EIA Petroleum Spot Prices Excel | Weekly |
| Refinery Crude Inputs | EIA Refinery Operations | Weekly |

---

## Methodology

### Inventory Signal
Weekly US crude stocks from EIA. A 4-week rolling average of the week-on-week change smooths seasonal noise.

- **Bullish** - 4-week average draw > 1,000 kb/week (supply tighter than demand)
- **Bearish** - 4-week average build > 1,000 kb/week (supply exceeding demand)
- **Neutral** - within +/-1,000 kb/week

### 3-2-1 Crack Spread
Approximates the gross refinery margin. For every 3 barrels of crude, a refinery produces approximately 2 barrels of gasoline and 1 barrel of distillate:

```
Crack Spread = (2 x RBOB_bbl + 1 x HeatingOil_bbl - 3 x WTI) / 3
```

Fuel prices converted from $/gallon to $/barrel (x 42).

### Signal Backtest
Tests whether the inventory signal predicts forward Brent price returns over 1, 4, 8, or 13-week horizons. Measures hit rate and average return by signal direction. Uses a 1-week signal lag to avoid look-ahead bias.

**Key finding:** The signal outperformed buy-and-hold Brent from 2014-2020 by avoiding major drawdowns, but missed the post-COVID recovery as OPEC+ supply responses overrode inventory fundamentals - highlighting the limitations of single-factor inventory models.

### Market Regime
Combines inventory signal and crack spread into seven market states:

| Regime | Inventory | Crack Spread |
|--------|-----------|--------------|
| Demand-driven bull | Bullish | High |
| Tightening supply | Bullish | Normal |
| Supply shock | Bearish | High |
| Demand destruction | Bearish | Low |
| Cautious bull | Bullish | Low |
| Cautious bear | Bearish | Normal |
| Balanced | Neutral | Any |

---

## Tech Stack

```
Python 3.11      Data processing and analysis
Pandas           Data manipulation and time series
Matplotlib       Chart generation
Streamlit        Interactive dashboard
Requests         EIA API and Excel file fetching
python-dotenv    Environment variable management
```

---

## Author

**Saujas Purohit**
MSc Geo-Energy with Machine Learning & Data Science (Merit) - Imperial College London

MSci Earth Sciences (First Class) - Durham University

Data Analyst & Petroleum Geoscientist

[LinkedIn](https://linkedin.com/in/saujaspurohit) · [GitHub](https://github.com/SaujP)
