import streamlit as st
import pandas as pd
import numpy as np
import calendar
from datetime import datetime, date

st.set_page_config(page_title="Trader Journal", layout="wide")

# -----------------------
# Styling (dark, TraderStats-ish)
# -----------------------
CSS = """
<style>
/* App background */
.stApp {
  background: radial-gradient(1200px 800px at 15% 0%, #121826 0%, #0B0F14 55%, #0B0F14 100%);
  color: #E6EDF3;
  font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, "Apple Color Emoji","Segoe UI Emoji";
}

/* Sidebar */
section[data-testid="stSidebar"] {
  background: #0D121A;
  border-right: 1px solid rgba(255,255,255,0.06);
}
section[data-testid="stSidebar"] .stButton button {
  width: 100%;
  border-radius: 10px;
  border: 1px solid rgba(255,255,255,0.10);
  background: linear-gradient(180deg, rgba(99,102,241,0.95), rgba(79,70,229,0.95));
  color: white;
  font-weight: 700;
}
section[data-testid="stSidebar"] .stButton button:hover {
  filter: brightness(1.05);
}

/* Containers / cards */
.card {
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 12px;
  padding: 14px 14px;
}
.card-title {
  color: rgba(230,237,243,0.72);
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 8px;
}
.card-value {
  font-size: 22px;
  font-weight: 800;
  color: #E6EDF3;
}
.subtle {
  color: rgba(230,237,243,0.72);
}

/* Page title */
.h1 {
  font-size: 28px;
  font-weight: 900;
  margin: 0;
}
.bigpnl {
  font-size: 28px;
  font-weight: 900;
  margin-top: 2px;
}

/* Calendar */
.cal-wrap {
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 14px;
  padding: 12px;
}
.cal-header {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 14px;
  margin-bottom: 10px;
  color: rgba(230,237,243,0.90);
  font-weight: 800;
}
.cal-dow {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 10px;
  margin-bottom: 10px;
}
.cal-dow div {
  text-align: center;
  color: rgba(230,237,243,0.65);
  font-size: 12px;
  font-weight: 700;
  padding: 6px 0;
  border-radius: 10px;
  background: rgba(255,255,255,0.02);
  border: 1px solid rgba(255,255,255,0.06);
}
.cal-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 10px;
}
.day {
  min-height: 78px;
  border-radius: 12px;
  background: rgba(255,255,255,0.02);
  border: 1px solid rgba(255,255,255,0.07);
  padding: 10px 10px;
}
.day.muted {
  opacity: 0.38;
}
.daynum {
  font-size: 12px;
  font-weight: 800;
  color: rgba(230,237,243,0.75);
}
.pnlpos {
  color: #34D399; /* green */
  font-weight: 900;
  margin-top: 10px;
  font-size: 14px;
}
.pnlneg {
  color: #FB7185; /* red */
  font-weight: 900;
  margin-top: 10px;
  font-size: 14px;
}
.tradescnt {
  margin-top: 2px;
  font-size: 11px;
  color: rgba(230,237,243,0.62);
  font-weight: 650;
}
.pill {
  display:inline-block;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 12px;
  border: 1px solid rgba(255,255,255,0.10);
  background: rgba(255,255,255,0.03);
}
.hr {
  height: 1px;
  background: rgba(255,255,255,0.07);
  margin: 10px 0 14px;
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# -----------------------
# Helpers
# -----------------------
def parse_tradingview_exports(uploaded_files) -> pd.DataFrame:
    """
    Parses TradingView xlsx exports (expects 'List of trades' sheet).
    Returns one row per completed trade (entry+exit paired by Trade # per file).
    """
    raw_frames = []
    for f in uploaded_files:
        try:
            df = pd.read_excel(f, sheet_name="List of trades")
        except Exception:
            # fall back: first sheet
            df = pd.read_excel(f)
        df["SourceFile"] = getattr(f, "name", "upload.xlsx")
        df["Date and time"] = pd.to_datetime(df["Date and time"], errors="coerce")
        raw_frames.append(df)

    if not raw_frames:
        return pd.DataFrame()

    raw = pd.concat(raw_frames, ignore_index=True)

    trades = []
    # Normalize column names that TradingView uses
    # Required: Trade #, Type, Date and time, Price USD, Net P&L USD
    for (sf, trade_no), g in raw.groupby(["SourceFile", "Trade #"], dropna=False):
        g = g.sort_values("Date and time")
        entry = g[g["Type"].astype(str).str.contains("Entry", case=False, na=False)]
        exit_ = g[g["Type"].astype(str).str.contains("Exit", case=False, na=False)]
        if entry.empty or exit_.empty:
            continue
        er = entry.iloc[0]
        xr = exit_.iloc[-1]

        direction = "Long" if "long" in str(er.get("Type", "")).lower() else "Short"
        trades.append({
            "TradeID": f"{sf}#{int(trade_no) if pd.notna(trade_no) else len(trades)+1}",
            "EntryTime": er["Date and time"],
            "ExitTime": xr["Date and time"],
            "Date": pd.to_datetime(xr["Date and time"]).normalize(),
            "Direction": direction,
            "Qty": er.get("Position size (qty)", np.nan),
            "EntryPrice": er.get("Price USD", np.nan),
            "ExitPrice": xr.get("Price USD", np.nan),
            "PnL_USD": float(xr.get("Net P&L USD", 0.0)),
        })

    out = pd.DataFrame(trades)
    if out.empty:
        return out
    return out.sort_values("ExitTime").reset_index(drop=True)

def fmt_money(x):
    sign = "-" if x < 0 else ""
    return f"{sign}${abs(x):,.2f}"

def longest_winning_streak_days(daily_pnl: pd.Series) -> int:
    """Longest consecutive days with pnl > 0 in the given daily series (indexed by date)."""
    if daily_pnl.empty:
        return 0
    vals = (daily_pnl > 0).astype(int).values
    best = cur = 0
    for v in vals:
        if v == 1:
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    return int(best)

# -----------------------
# Sidebar (matches screenshot structure)
# -----------------------
with st.sidebar:
    st.markdown("### 📊 **traderstats**")
    st.button("➕  Add Trades", type="primary")

    st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
    st.markdown("**App**")
    nav = st.radio(
        "", 
        ["Dashboard", "Calendar", "Trade Log", "Sharing", "Settings"], 
        index=1, 
        label_visibility="collapsed"
    )

    st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
    uploaded = st.file_uploader(
        "Upload TradingView .xlsx exports",
        type=["xlsx"],
        accept_multiple_files=True
    )

    st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
    st.markdown('<span class="pill">Dark Theme</span>', unsafe_allow_html=True)
    st.caption("Local app • Your files stay on your machine")

# -----------------------
# Main
# -----------------------
if not uploaded:
    st.markdown("## Monthly Performance")
    st.info("Upload one or more TradingView `.xlsx` files (exported trade list) using the sidebar to populate the dashboard.")
    st.stop()

trades = parse_tradingview_exports(uploaded)
if trades.empty:
    st.error("Could not find completed Entry/Exit trade pairs in your uploads. Make sure the export contains the 'List of trades' sheet.")
    st.stop()

# Month selector defaults to latest month in data
latest = trades["Date"].max()
all_months = sorted(trades["Date"].dt.to_period("M").unique())
default_idx = all_months.index(latest.to_period("M"))
sel_month = st.selectbox("Month", all_months, index=default_idx, format_func=lambda p: p.strftime("%B %Y"))

month_start = sel_month.to_timestamp()
month_end = (sel_month + 1).to_timestamp() - pd.Timedelta(seconds=1)

tm = trades[(trades["Date"] >= month_start) & (trades["Date"] <= month_end)].copy()

# Daily aggregation (selected month)
daily = tm.groupby(tm["Date"].dt.date).agg(
    PnL_USD=("PnL_USD", "sum"),
    Trades=("TradeID", "count")
).reset_index().rename(columns={"Date":"Day"})
daily["Day"] = pd.to_datetime(daily["Day"]).sort_values()

monthly_pnl = tm["PnL_USD"].sum()
wins = tm[tm["PnL_USD"] > 0]
losses = tm[tm["PnL_USD"] < 0]
win_rate = (len(wins) / len(tm)) if len(tm) else 0
avg_win = wins["PnL_USD"].mean() if len(wins) else 0.0
avg_loss = losses["PnL_USD"].mean() if len(losses) else 0.0

# Longest winning streak by day (within month)
daily_series = daily.sort_values("Day").set_index("Day")["PnL_USD"] if not daily.empty else pd.Series(dtype=float)
streak = longest_winning_streak_days(daily_series)

# -----------------------
# Header like screenshot
# -----------------------
colA, colB = st.columns([0.75, 0.25], gap="large")
with colA:
    st.markdown('<p class="h1">Monthly Performance</p>', unsafe_allow_html=True)
    pnl_class = "pnlpos" if monthly_pnl >= 0 else "pnlneg"
    st.markdown(f'<div class="bigpnl {pnl_class}">{fmt_money(monthly_pnl)}</div>', unsafe_allow_html=True)

    mcol1, mcol2, mcol3 = st.columns([0.18,0.64,0.18])
    with mcol2:
        st.caption("Not sharing month")
with colB:
    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
    st.markdown("<div style='text-align:right;'><span class='pill'>All accounts</span></div>", unsafe_allow_html=True)

st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

# -----------------------
# Performance cards row
# -----------------------
st.markdown("### Performance")
c1, c2, c3, c4 = st.columns(4, gap="large")

with c1:
    st.markdown(
        f"""
        <div class="card">
          <div class="card-title">Avg Win &amp; Loss</div>
          <div class="card-value"><span style="color:#34D399;">{fmt_money(avg_win)}</span> &nbsp; <span style="color:#FB7185;">{fmt_money(avg_loss)}</span></div>
        </div>
        """,
        unsafe_allow_html=True
    )
with c2:
    st.markdown(
        f"""
        <div class="card">
          <div class="card-title">Win Rate</div>
          <div class="card-value">{win_rate*100:.2f}%</div>
        </div>
        """,
        unsafe_allow_html=True
    )
with c3:
    st.markdown(
        f"""
        <div class="card">
          <div class="card-title">Longest Winning Streak</div>
          <div class="card-value">{streak} days</div>
        </div>
        """,
        unsafe_allow_html=True
    )
with c4:
    st.markdown(
        f"""
        <div class="card">
          <div class="card-title">Total Trades</div>
          <div class="card-value">{len(tm):,}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)

# -----------------------
# Calendar section (very close to screenshot)
# -----------------------
st.markdown("### Calendar")

# Build full month calendar (Mon-Sun like screenshot)
year = month_start.year
month = month_start.month
cal = calendar.Calendar(firstweekday=0)  # Monday

month_days = list(cal.itermonthdates(year, month))
weeks = [month_days[i:i+7] for i in range(0, len(month_days), 7)]
# Map pnl and trade count
pnl_map = {d.date(): float(p) for d, p in zip(daily["Day"], daily["PnL_USD"])} if not daily.empty else {}
tr_map = {d.date(): int(t) for d, t in zip(daily["Day"], daily["Trades"])} if not daily.empty else {}

# Calendar header (arrows handled by month selectbox; keep centered title)
st.markdown(
    f"""
    <div class="cal-wrap">
      <div class="cal-header">{calendar.month_name[month]} {year}</div>
      <div class="cal-dow">
        <div>MON</div><div>TUE</div><div>WED</div><div>THU</div><div>FRI</div><div>SAT</div><div>SUN</div>
      </div>
      <div class="cal-grid">
    """,
    unsafe_allow_html=True
)

# Day cells
for wk in weeks:
    for d in wk:
        muted = "muted" if d.month != month else ""
        daynum = d.day
        pnlv = pnl_map.get(d, 0.0) if d.month == month else 0.0
        tradesn = tr_map.get(d, 0) if d.month == month else 0
        pnl_html = ""
        if d.month == month and (pnlv != 0 or tradesn != 0):
            cls = "pnlpos" if pnlv >= 0 else "pnlneg"
            pnl_html = f'<div class="{cls}">{fmt_money(pnlv)}</div><div class="tradescnt">{tradesn} trades</div>'
        st.markdown(
            f"""
            <div class="day {muted}">
              <div class="daynum">{daynum}</div>
              {pnl_html}
            </div>
            """,
            unsafe_allow_html=True
        )

st.markdown("</div></div>", unsafe_allow_html=True)

# -----------------------
# Trade log (optional view toggle)
# -----------------------
if nav == "Trade Log":
    st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)
    st.markdown("### Trade Log")
    cols = ["ExitTime","Direction","Qty","EntryPrice","ExitPrice","PnL_USD"]
    show = tm.copy()
    show["ExitTime"] = pd.to_datetime(show["ExitTime"]).dt.strftime("%Y-%m-%d %H:%M")
    st.dataframe(show[cols], use_container_width=True, hide_index=True)
