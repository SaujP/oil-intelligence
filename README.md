# 🛢 Oil Market Intelligence

A live oil market analysis tool monitoring the balance between **crude supply, storage, demand, and pricing** using weekly EIA data.

> Built to replicate the kind of supply/demand signal analysis used by energy market analysts at firms like Wood Mackenzie, LSEG, Shell, and BP.

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

## Project Structure

```
OIL_INTELLIGENCE/
├── src/
│   ├── data_loader.py   # All EIA data fetching (one place to maintain)
│   ├── signals.py       # Signal calculations and backtest logic
│   └── charts.py        # All matplotlib chart functions
├── dashboard/
│   └── app.py           # Streamlit app
├── notebooks/
│   ├── 01_inventory_signal.ipynb
│   └── 02_crack_spread.ipynb
├── data/                # Local CSV cache (EIA data)
├── outputs/             # Saved chart PNGs
├── .env                 # EIA API key (not committed)
├── requirements.txt
└── README.md
```

---

## Quickstart

```bash
# 1. Clone and set up environment
git clone <your-repo-url>
cd OIL_INTELLIGENCE
python -m venv .project_env
source .project_env/bin/activate   # Mac/Linux
# .project_env\Scripts\activate   # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Add your EIA API key
echo "EIA_API_KEY=your_key_here" > .env
# Get a free key at: https://www.eia.gov/opendata/

# 4. Run the dashboard
streamlit run dashboard/app.py
```

---

## Data Sources

All data is sourced from the **US Energy Information Administration (EIA)** — the official US government energy statistics agency.

- **Crude inventory**: [EIA Weekly Petroleum Status Report](https://www.eia.gov/petroleum/supply/weekly/)
- **Spot prices** (WTI, Brent, RBOB, Heating Oil): [EIA Petroleum Spot Prices](https://www.eia.gov/dnav/pet/xls/PET_PRI_SPT_S1_W.xls)
- **Refinery inputs**: [EIA Refinery Operations](https://www.eia.gov/petroleum/refinerycapacity/)

No paid data subscriptions required.

---

## Methodology

### Inventory Signal
Weekly US crude stocks from EIA. A 4-week rolling average of the week-on-week change is used to smooth seasonal noise. Signal classification:
- **Bullish**: 4-week average draw > 1,000 kb/week
- **Bearish**: 4-week average build > 1,000 kb/week
- **Neutral**: within ±1,000 kb/week

### 3-2-1 Crack Spread
Approximates the gross refinery margin assuming 3 barrels of crude → 2 barrels of gasoline + 1 barrel of distillate:

```
Crack Spread = (2 × RBOB_bbl + 1 × HeatingOil_bbl − 3 × WTI) ÷ 3
```

Fuel prices converted from $/gallon to $/barrel (× 42).

### Signal Backtest
Tests whether the inventory signal predicts forward Brent price returns over 1, 4, 8, or 13-week horizons. Measures hit rate and average return by signal direction.

### Market Regime
Matrix of inventory signal × crack signal produces seven regime states, from *Demand-driven bull* to *Demand destruction*.

---

## Author

**Saujas Purohit**  
MSc Geo-Energy with ML & Data Science, Imperial College London  
Data Analyst & Petroleum Geoscientist

[LinkedIn](#) · [GitLab](#)
