"""
src/data_loader.py
==================
All data fetching for the Oil Intelligence project.
Every notebook and the Streamlit app imports from here — one place to fix if anything breaks.

Sources:
  - EIA API v2     → crude inventory, refinery inputs
  - EIA Excel      → WTI, Brent, RBOB, Heating Oil spot prices
"""

import os
import requests
import pandas as pd
from io import BytesIO
from dotenv import load_dotenv
import urllib3

urllib3.disable_warnings()  # suppress SSL warnings
load_dotenv()

API_KEY   = os.getenv("EIA_API_KEY")
DATA_DIR  = os.path.join(os.path.dirname(__file__), "..", "data")
EIA_EXCEL = "https://www.eia.gov/dnav/pet/xls/PET_PRI_SPT_S1_W.xls"


# ── INTERNAL HELPERS ──────────────────────────────────────────────────────────

def _eia_excel() -> pd.ExcelFile:
    """Download EIA weekly spot prices Excel file (cached per session)."""
    r = requests.get(EIA_EXCEL, verify=False, timeout=30)
    r.raise_for_status()
    return pd.ExcelFile(BytesIO(r.content))


def _parse_sheet(xl: pd.ExcelFile, sheet: str, col_names: list) -> pd.DataFrame:
    """Parse one sheet from the EIA Excel file with clean column names."""
    df = xl.parse(sheet, skiprows=2)
    df = df.iloc[:, :len(col_names)]
    df.columns = col_names
    df["period"] = pd.to_datetime(df["period"], errors="coerce")
    for col in col_names[1:]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.dropna(subset=["period"]).sort_values("period").reset_index(drop=True)


def _eia_api(endpoint: str, extra_params: dict = {}) -> pd.DataFrame:
    """Generic EIA API v2 fetcher. Returns raw records as a DataFrame."""
    url = f"https://api.eia.gov/v2/{endpoint}"
    all_records = []
    offset = 0

    while True:
        params = {
            "api_key": API_KEY,
            "frequency": "weekly",
            "data[0]": "value",
            "sort[0][column]": "period",
            "sort[0][direction]": "asc",
            "offset": offset,
            "length": 5000,
            **extra_params
        }
        resp = requests.get(url, params=params, timeout=30)
        data = resp.json()

        if "response" not in data:
            raise ValueError(f"EIA API error: {data}")

        records = data["response"].get("data", [])
        if not records:
            break

        all_records.extend(records)
        total  = int(data["response"].get("total", 0))
        offset += 5000
        if offset >= total:
            break

    return pd.DataFrame(all_records)


# ── PUBLIC FUNCTIONS ──────────────────────────────────────────────────────────

def load_brent(start: str = "2010-01-01") -> pd.DataFrame:
    """
    Weekly Brent crude spot price ($/bbl).
    Pulls from EIA Excel — full history back to 1987.

    Returns: DataFrame with columns [period, brent_price]
    """
    xl  = _eia_excel()
    df  = _parse_sheet(xl, "Data 1", ["period", "wti", "brent_price"])
    df  = df[["period", "brent_price"]].dropna()
    df  = df[df["period"] >= start].reset_index(drop=True)
    return df


def load_wti(start: str = "2010-01-01") -> pd.DataFrame:
    """
    Weekly WTI crude spot price ($/bbl).
    Pulls from EIA Excel.

    Returns: DataFrame with columns [period, wti]
    """
    xl  = _eia_excel()
    df  = _parse_sheet(xl, "Data 1", ["period", "wti", "brent_price"])
    df  = df[["period", "wti"]].dropna()
    df  = df[df["period"] >= start].reset_index(drop=True)
    return df


def load_crack_spread(start: str = "2014-01-01") -> pd.DataFrame:
    """
    3-2-1 crack spread ($/bbl) — proxy for refinery profit margin.
    Formula: (2 × RBOB + 1 × Heating Oil - 3 × WTI) / 3

    Returns: DataFrame with columns [period, wti, rbob_bbl, ho_bbl, crack_321, crack_ma4]
    """
    xl   = _eia_excel()
    wti  = _parse_sheet(xl, "Data 1", ["period", "wti", "brent_price"])[["period", "wti"]]
    rbob = _parse_sheet(xl, "Data 3", ["period", "rbob_gal"])
    ho   = _parse_sheet(xl, "Data 4", ["period", "ho_gal"])

    df = wti.merge(rbob, on="period").merge(ho, on="period").dropna()
    df = df[df["period"] >= start].reset_index(drop=True)

    df["rbob_bbl"]  = df["rbob_gal"] * 42   # $/gal → $/bbl
    df["ho_bbl"]    = df["ho_gal"]   * 42
    df["crack_321"] = (2 * df["rbob_bbl"] + 1 * df["ho_bbl"] - 3 * df["wti"]) / 3
    df["crack_ma4"] = df["crack_321"].rolling(4).mean()

    return df[["period", "wti", "rbob_bbl", "ho_bbl", "crack_321", "crack_ma4"]]


def load_inventory(start: str = "2010-01-01") -> pd.DataFrame:
    """
    US weekly crude oil stocks (thousand barrels).
    Uses local CSV if available, otherwise fetches from EIA API.
    Takes the max value per date = US total (not regional breakdown).

    Returns: DataFrame with columns [period, inventory_kb]
    """
    csv_path = os.path.join(DATA_DIR, "inventory.csv")

    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        df["period"] = pd.to_datetime(df["period"], errors="coerce")
        df = df.dropna(subset=["period"])
        # Multiple rows per date — take max (US total)
        df = df.groupby("period")["value"].max().reset_index()
        df.columns = ["period", "inventory_kb"]
    else:
        raw = _eia_api("petroleum/stoc/wstk/data/")
        df  = raw[["period", "value"]].copy()
        df.columns = ["period", "inventory_kb"]
        df["period"]       = pd.to_datetime(df["period"], errors="coerce")
        df["inventory_kb"] = pd.to_numeric(df["inventory_kb"], errors="coerce")
        df = df.dropna().groupby("period")["inventory_kb"].max().reset_index()

    df = df.sort_values("period")
    df = df[df["period"] >= start].reset_index(drop=True)
    return df


def load_refinery_inputs(start: str = "2010-01-01") -> pd.DataFrame:
    """
    US weekly refinery crude inputs (thousand barrels/day).
    Uses local CSV if available.

    Returns: DataFrame with columns [period, refinery_inputs]
    """
    csv_path = os.path.join(DATA_DIR, "refinery_inputs.csv")

    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        df["period"]          = pd.to_datetime(df["period"], errors="coerce")
        df["refinery_inputs"] = pd.to_numeric(df["refinery_inputs"], errors="coerce")
        df = df.dropna()
        # Sum regional rows per date to get US total
        df = df.groupby("period")["refinery_inputs"].sum().reset_index()
    else:
        raw = _eia_api("petroleum/pnp/wiup/data/")
        df  = raw[["period", "value"]].copy()
        df.columns = ["period", "refinery_inputs"]
        df["period"]          = pd.to_datetime(df["period"], errors="coerce")
        df["refinery_inputs"] = pd.to_numeric(df["refinery_inputs"], errors="coerce")
        df = df.dropna().groupby("period")["refinery_inputs"].sum().reset_index()

    df = df.sort_values("period")
    df = df[df["period"] >= start].reset_index(drop=True)
    return df


def load_all(start: str = "2010-01-01") -> pd.DataFrame:
    """
    Master dataset — merges inventory, Brent, WTI, crack spread, refinery inputs
    into one weekly DataFrame.

    Returns: merged DataFrame aligned on weekly period
    """
    print("Loading inventory...")
    inv = load_inventory(start)

    print("Loading prices (Brent + WTI)...")
    brent = load_brent(start)
    wti   = load_wti(start)

    print("Loading crack spread...")
    crack = load_crack_spread(start)

    print("Loading refinery inputs...")
    ref = load_refinery_inputs(start)

    # Merge everything on period
    df = inv.merge(brent, on="period", how="left")
    df = df.merge(wti[["period", "wti"]], on="period", how="left")
    df = df.merge(crack[["period", "crack_321", "crack_ma4"]], on="period", how="left")
    df = df.merge(ref, on="period", how="left")

    df = df.sort_values("period").reset_index(drop=True)
    print(f"✓ Master dataset ready: {len(df)} rows, {df['period'].min().date()} → {df['period'].max().date()}")
    return df


if __name__ == "__main__":
    df = load_all()
    print(df.tail(5).to_string())
