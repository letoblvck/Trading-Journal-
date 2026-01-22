import streamlit as st
import pandas as pd
import numpy as np
import calendar
from datetime import datetime

st.set_page_config(page_title="Trading Journal", layout="wide")

# -----------------------
# Professional dark theme + custom CSS
# -----------------------
CSS = """
<style>
/* Base */
.stApp {
  background: #0B0F14;
  color: #E6EDF3;
  font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial;
}
a { color: inherit; }

/* Hide Streamlit default header/footer */
header, footer {visibility: hidden;}
/* Reduce top padding */
.block-container { padding-top: 1.2rem; padding-bottom: 2rem; }

/* Sidebar */
section[data-testid="stSidebar"] {
  background: #0D121A;
  border-right: 1px solid rgba(255,255,255,0.06);
}
.sidebar-title {
  font-weight: 900;
  font-size: 18px;
  letter-spacing: 0.2px;
}
.sidebar-subtle {
  color: rgba(230,237,243,0.70);
  font-size: 12px;
}

/* Small dark upload button (styles the file uploader) */
section[data-testid="stSidebar"] [data-testid="stFileUploader"] {
  padding: 0 !important;
}
section[data-testid="stSidebar"] [data-testid="stFileUploader"] > label {
  display: none !important;
}
section[data-testid="stSidebar"] [data-testid="stFileUploader"] div[data-testid="stFileUploaderDropzone"]{
  background: transparent !important;
  border: none !important;
  padding: 0 !important;
}
section[data-testid="stSidebar"] [data-testid="stFileUploader"] div[data-testid="stFileUploaderDropzone"] div {
  padding: 0 !important;
}
section[data-testid="stSidebar"] [data-testid="stFileUploader"] button {
  width: 100% !important;
  border-radius: 10px !important;
  border: 1px solid rgba(255,255,255,0.10) !important;
  background: rgba(255,255,255,0.04) !important;
  color: #E6EDF3 !important;
  font-weight: 750 !important;
  padding: 0.55rem 0.75rem !important;
}
section[data-testid="stSidebar"] [data-testid="stFileUploader"] button:hover {
  border-color: rgba(255,255,255,0.18) !important;
  background: rgba(255,255,255,0.06) !important;
}

/* Nav buttons */
.navbtn button {
  width: 100%;
  text-align: left;
  border-radius: 10px;
  border: 1px solid rgba(255,255,255,0.06);
  background: transparent;
  color: rgba(230,237,243,0.85);
  padding: 0.55rem 0.75rem;
  font-weight: 650;
}
.navbtn button:hover {
  background: rgba(255,255,255,0.05);
  border-color: rgba(255,255,255,0.10);
}
.navbtn.active button {
  background: rgba(99,102,241,0.18);
  border-color: rgba(99,102,241,0.35);
  color: #E6EDF3;
}

/* Cards */
.card {
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 12px;
  padding: 14px 14px;
}
.card-title {
  color: rgba(230,237,243,0.70);
  font-size: 12px;
  font-weight: 700;
  margin-bottom: 8px;
}
.card-value {
  font-size: 20px;
  font-weight: 900;
  color: #E6EDF3;
}
.big-title {
  font-size: 28px;
  font-weight: 950;
  margin: 0;
}
.big-pnl {
  font-size: 30px;
  font-weight: 950;
  margin-top: 4px;
}
.pos { color: #34D399; }
.neg { color: #FB7185; }
.pill {
  display:inline-block;
  padding: 2px 10px;
  border-radius: 999px;
  font-size: 12px;
  border: 1px solid rgba(255,255,255,0.10);
  background: rgba(255,255,255,0.03);
  color: rgba(230,237,243,0.80);
}

/* Calendar (real grid) */
.cal-wrap {
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 14px;
  padding: 14px;
}
.cal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
.cal-title {
  font-weight: 900;
  font-size: 14px;
  color: rgba(230,237,243,0.88);
}
.cal-dow {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 10px;
  margin-bottom: 10px;
}
.cal-dow div {
  text-align: center;
  color: rgba(230,237,243,0.60);
  font-size: 11px;
  font-weight: 800;
  padding: 7px 0;
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
  border-radius: 12px;
  background: rgba(255,255,255,0.02);
  border: 1px solid rgba(255,255,255,0.07);
  padding: 10px;
  min-height: 92px;
}
.day.muted { opacity: 0.35; }
.daynum {
  font-size: 12px;
  font-weight: 900;
  color: rgba(230,237,243,0.70);
}
.daypnl {
  margin-top: 10px;
  font-weight: 950;
  font-size: 14px;
}
.daytrades {
  margin-top: 2px;
  font-size: 11px;
  color: rgba(230,237,243,0.60);
  font-weight: 650;
}
.hr {
  height: 1px;
  background: rgba(255,255,255,0.07);
  margin: 12px 0 12px;
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# -----------------------
# Helpers
# -----------------------
def parse_tradingview_exports(uploaded_files) -> pd.DataFrame:
    """Parse TradingView xlsx exports (expects 'List of trades' sheet). One row per completed trade."""
    raw_frames = []
    for f in uploaded_files:
        try:
            df = pd.read_excel(f, sheet_name="List of trades")
        except Exception:
            df = pd.read_excel(f)
        df["SourceFile"] = getattr(f, "name", "upload.xlsx")
        df["Date and time"] = pd.to_datetime(df["Date and time"], errors="coerce")
        raw_frames.append(df)

    if not raw_frames:
        return pd.DataFrame()

    raw = pd.concat(raw_frames, ignore_index=True)

    trades = []
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

def fmt_money(x: float) -> str:
    sign = "-" if x < 0 else ""
    return f"{sign}${abs(x):,.2f}"

def longest_winning_streak_days(daily_pnl: pd.Series) -> int:
    """Longest consecutive days where daily pnl > 0."""
    if daily_pnl is None or daily_pnl.empty:
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
# State
# -----------------------
if "nav" not in st.session_state:
    st.session_state.nav = "Calendar"

def nav_button(label: str, value: str):
    active = (st.session_state.nav == value)
    cls = "navbtn active" if active else "navbtn"
    st.markdown(f'<div class="{cls}">', unsafe_allow_html=True)
    if st.button(label, key=f"nav_{value}"):
        st.session_state.nav = value
    st.markdown("</div>", unsafe_allow_html=True)

# -----------------------
# Sidebar
# -----------------------
with st.sidebar:
    st.markdown('<div class="sidebar-title">traderstats</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-subtle">Your trading journal</div>', unsafe_allow_html=True)

    st.markdown('<div class="hr"></div>', unsafe_allow_html=True)

    uploaded = st.file_uploader(
        "Import trades",
        type=["xlsx"],
        accept_multiple_files=True,
        label_visibility="collapsed"
    )

    st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
    st.markdown("**App**")
    nav_button("Dashboard", "Dashboard")
    nav_button("Calendar", "Calendar")
    nav_button("Trade Log", "Trade Log")
    nav_button("Settings", "Settings")

    st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
    st.markdown('<span class="pill">Dark theme</span>', unsafe_allow_html=True)
    st.caption("Local/URL app • uploads processed in-session")

# -----------------------
# Load data
# -----------------------
if not uploaded:
    st.markdown("## Monthly Performance")
    st.info("Click **Import trades** in the sidebar to upload your TradingView `.xlsx` exports.")
    st.stop()

trades = parse_tradingview_exports(uploaded)
if trades.empty:
    st.error("I couldn't find completed Entry/Exit trade pairs. Make sure your export includes the **List of trades** sheet.")
    st.stop()

# -----------------------
# Filters: All-time OR selected month
# -----------------------
all_months = sorted(trades["Date"].dt.to_period("M").unique())
latest = trades["Date"].max().to_period("M")
default_idx = all_months.index(latest) if latest in all_months else 0

top_left, top_right = st.columns([0.78, 0.22])
with top_right:
    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    scope = st.selectbox("Scope", ["All time", "Single month"], index=0)
    if scope == "Single month":
        sel_month = st.selectbox("Month", all_months, index=default_idx, format_func=lambda p: p.strftime("%B %Y"))
    else:
        sel_month = None

if scope == "Single month":
    month_start = sel_month.to_timestamp()
    month_end = (sel_month + 1).to_timestamp() - pd.Timedelta(seconds=1)
    view = trades[(trades["Date"] >= month_start) & (trades["Date"] <= month_end)].copy()
    cal_year, cal_month = month_start.year, month_start.month
    header_range = f"{calendar.month_name[cal_month]} {cal_year}"
else:
    view = trades.copy()
    # calendar shows latest month, but stats are all-time
    month_start = trades["Date"].max().to_period("M").to_timestamp()
    cal_year, cal_month = month_start.year, month_start.month
    header_range = "All time"

# -----------------------
# Metrics
# -----------------------
monthly_pnl = float(view["PnL_USD"].sum())
wins = view[view["PnL_USD"] > 0]
losses = view[view["PnL_USD"] < 0]
win_rate = (len(wins) / len(view)) if len(view) else 0.0
avg_win = float(wins["PnL_USD"].mean()) if len(wins) else 0.0
avg_loss = float(losses["PnL_USD"].mean()) if len(losses) else 0.0

# Daily for streak + calendar (calendar only for selected month / latest month)
daily_view = view.groupby(view["Date"].dt.date).agg(PnL_USD=("PnL_USD", "sum"), Trades=("TradeID", "count")).reset_index()
daily_view["Day"] = pd.to_datetime(daily_view["Date"]).sort_values()

daily_for_streak = daily_view.sort_values("Day").set_index("Day")["PnL_USD"] if not daily_view.empty else pd.Series(dtype=float)
streak = longest_winning_streak_days(daily_for_streak)

# calendar uses month_start/cal_month
cal_start = datetime(cal_year, cal_month, 1)
cal_end = (pd.Timestamp(cal_start) + pd.offsets.MonthEnd(1)).to_pydatetime()
tr_m = trades[(trades["Date"] >= pd.Timestamp(cal_start)) & (trades["Date"] <= pd.Timestamp(cal_end))].copy()
daily_m = tr_m.groupby(tr_m["Date"].dt.date).agg(PnL_USD=("PnL_USD","sum"), Trades=("TradeID","count")).reset_index()
daily_m["Day"] = pd.to_datetime(daily_m["Date"])
pnl_map = {d.date(): float(p) for d, p in zip(daily_m["Day"], daily_m["PnL_USD"])}
tr_map = {d.date(): int(t) for d, t in zip(daily_m["Day"], daily_m["Trades"])}

# -----------------------
# Header (Monthly Performance)
# -----------------------
with top_left:
    st.markdown(f'<p class="big-title">Monthly Performance</p>', unsafe_allow_html=True)
    cls = "pos" if monthly_pnl >= 0 else "neg"
    st.markdown(f'<div class="big-pnl {cls}">{fmt_money(monthly_pnl)}</div>', unsafe_allow_html=True)
    st.caption(f"Scope: {header_range} • Trades shown: {len(view):,} • Data range: {trades['Date'].min().date()} → {trades['Date'].max().date()}")

st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

# -----------------------
# Performance cards
# -----------------------
st.markdown("### Performance")
c1, c2, c3, c4 = st.columns(4, gap="large")

with c1:
    st.markdown(
        f"""
        <div class="card">
          <div class="card-title">Avg Win &amp; Loss</div>
          <div class="card-value">
            <span class="pos">{fmt_money(avg_win)}</span>
            &nbsp; <span class="neg">{fmt_money(avg_loss)}</span>
          </div>
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
          <div class="card-value">{len(view):,}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

# -----------------------
# Calendar (normal boxes)
# -----------------------
st.markdown("### Calendar")

cal = calendar.Calendar(firstweekday=6)  # Sunday-first looks "normal" for most users
month_days = list(cal.itermonthdates(cal_year, cal_month))
weeks = [month_days[i:i+7] for i in range(0, len(month_days), 7)]

st.markdown(
    f"""
    <div class="cal-wrap">
      <div class="cal-header">
        <div class="cal-title">{calendar.month_name[cal_month]} {cal_year}</div>
        <div class="pill">Calendar view</div>
      </div>

      <div class="cal-dow">
        <div>SUN</div><div>MON</div><div>TUE</div><div>WED</div><div>THU</div><div>FRI</div><div>SAT</div>
      </div>

      <div class="cal-grid">
    """,
    unsafe_allow_html=True
)

for wk in weeks:
    for d in wk:
        muted = "muted" if d.month != cal_month else ""
        pnlv = pnl_map.get(d, 0.0) if d.month == cal_month else 0.0
        tradesn = tr_map.get(d, 0) if d.month == cal_month else 0

        pnl_html = ""
        if d.month == cal_month and (pnlv != 0 or tradesn != 0):
            cls = "pos" if pnlv >= 0 else "neg"
            pnl_html = f'<div class="daypnl {cls}">{fmt_money(pnlv)}</div><div class="daytrades">{tradesn} trades</div>'

        st.markdown(
            f"""
            <div class="day {muted}">
              <div class="daynum">{d.day}</div>
              {pnl_html}
            </div>
            """,
            unsafe_allow_html=True
        )

st.markdown("</div></div>", unsafe_allow_html=True)

# -----------------------
# Trade Log view
# -----------------------
if st.session_state.nav == "Trade Log":
    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
    st.markdown("### Trade Log")
    cols = ["ExitTime","Direction","Qty","EntryPrice","ExitPrice","PnL_USD"]
    show = view.copy()
    show["ExitTime"] = pd.to_datetime(show["ExitTime"]).dt.strftime("%Y-%m-%d %H:%M")
    st.dataframe(show[cols], use_container_width=True, hide_index=True)

# Settings placeholder
if st.session_state.nav == "Settings":
    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
    st.markdown("### Settings")
    st.write("Coming next: commissions, R-multiple, tags/notes persistence, symbol filters.")
