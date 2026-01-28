import streamlit as st
import yfinance as yf
import pandas as pd
from plotly.subplots import make_subplots
import plotly.graph_objects as go

# --- CONFIGURATION ---
st.set_page_config(page_title="Swing Scanner", layout="wide")

# --- SESSION STATE ---
if "scan_results" not in st.session_state:
    st.session_state.scan_results = []

# --- CSS STYLING ---
st.markdown("""
    <style>
    .card {
        border: 1px solid #ddd;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 15px;
        background-color: #ffffff;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        height: 100%;
    }
    .card-header {
        font-size: 16px;
        font-weight: bold;
        color: #333;
        margin-bottom: 10px;
        border-bottom: 1px solid #eee;
        padding-bottom: 5px;
    }
    .card-row {
        display: flex;
        justify-content: space-between;
        margin-bottom: 5px;
    }
    .label { color: #666; font-size: 14px; }
    .value { font-weight: bold; font-size: 16px; }
    .positive { color: green; }
    .negative { color: red; }
    .guide-header { font-size: 18px; font-weight: bold; margin-top: 20px; color: #262730; }
    </style>
""", unsafe_allow_html=True)

# --- F&O STOCK LIST ---
WATCHLIST = [

"IDEA.NS", "YESBANK.NS", "SUZLON.NS", "NHPC.NS", "NMDC.NS", "IDFCFIRSTB.NS",
"GMRAIRPORT.NS", "NBCC.NS", "INOXWIND.NS", "MOTHERSON.NS", "IRFC.NS", "PNB.NS",
"IREDA.NS", "IEX.NS", "SAMMAANCAP.NS", "BANDHANBNK.NS", "SAIL.NS", "PPLPHARMA.NS",
"CANBK.NS", "IOC.NS", "BANKINDIA.NS", "GAIL.NS", "UNIONBANK.NS", "TATASTEEL.NS",
"ASHOKLEY.NS", "HUDCO.NS", "CROMPTON.NS", "NYKAA.NS", "WIPRO.NS", "BHEL.NS",
"ONGC.NS", "JIOFIN.NS", "POWERGRID.NS", "ETERNAL.NS", "PETRONET.NS",
"FEDERALBNK.NS", "LTF.NS", "RBLBANK.NS", "BANKBARODA.NS", "MANAPPURAM.NS",
"SWIGGY.NS", "ITC.NS", "EXIDEIND.NS", "RVNL.NS", "TMPV.NS", "NTPC.NS",
"TATAPOWER.NS", "ABCAPITAL.NS", "BPCL.NS", "PFC.NS", "RECLTD.NS",
"BIOCON.NS", "KALYANKJIL.NS", "NATIONALUM.NS", "DELHIVERY.NS",
"KOTAKBANK.NS", "INDUSTOWER.NS", "BEL.NS", "HINDPETRO.NS",
"COALINDIA.NS", "OIL.NS", "SONACOMS.NS", "VBL.NS", "JSWENERGY.NS",
"CONCOR.NS", "JUBLFOOD.NS", "PATANJALI.NS", "LICHSGFIN.NS",
"PGEL.NS", "DABUR.NS", "AMBUJACEM.NS", "SYNGENE.NS", "CGPOWER.NS",
"DLF.NS", "IRCTC.NS", "ICICIPRULI.NS", "INDHOTEL.NS", "TATATECH.NS",
"PREMIERENE.NS", "CAMS.NS", "VEDL.NS", "UPL.NS", "HDFCLIFE.NS",
"HINDZINC.NS", "MARICO.NS", "SBICARD.NS", "ADANIGREEN.NS", "LICI.NS",
"PNBHOUSING.NS", "ADANIENSOL.NS", "FORTIS.NS", "INDUSINDBK.NS",
"INDIANB.NS", "ZYDUSLIFE.NS", "HDFCBANK.NS", "LODHA.NS", "BAJFINANCE.NS",
"AUBANK.NS", "HINDALCO.NS", "MAXHEALTH.NS", "SHRIRAMFIN.NS",
"KFINTECH.NS", "LAURUSLABS.NS", "SBIN.NS", "JINDALSTEL.NS",
"KPITTECH.NS", "360ONE.NS", "UNOMINDA.NS", "AUROPHARMA.NS",
"PAYTM.NS", "TATACONSUM.NS", "JSWSTEEL.NS", "GODREJCP.NS",
"DRREDDY.NS", "TORNTPOWER.NS", "AXISBANK.NS", "HAVELLS.NS"

]

# --- FUNCTIONS ---

@st.cache_data(ttl=300)
def get_data(symbol, period="6mo", interval="1d"):
    try:
        df = yf.download(symbol, period=period, interval=interval, progress=False, auto_adjust=False)
        if len(df) == 0:
            return None
        df = df.reset_index()
        df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
        return df
    except Exception as e:
        return None

def calculate_indicators(df):
    df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
    df['MA_20'] = df['Close'].rolling(window=20).mean()
    df['STD_20'] = df['Close'].rolling(window=20).std()
    df['Upper_BB'] = df['MA_20'] + (df['STD_20'] * 2)
    df['Lower_BB'] = df['MA_20'] - (df['STD_20'] * 2)
    return df

def get_market_structure(df):
    latest_close = df['Close'].iloc[-1]
    latest_ema20 = df['EMA_20'].iloc[-1]
    latest_ema50 = df['EMA_50'].iloc[-1]
    
    if latest_ema20 > latest_ema50 and latest_close > latest_ema20:
        trend = "🟢 UPTREND"
        color = "green"
    elif latest_ema20 < latest_ema50 and latest_close < latest_ema20:
        trend = "🔴 DOWNTREND"
        color = "red"
    else:
        trend = "🟡 SIDEWAYS"
        color = "orange"
        
    recent_high = df['High'].tail(50).max()
    recent_low = df['Low'].tail(50).min()
    return trend, color, recent_high, recent_low

def check_strategies(df):
    latest_close = float(df['Close'].iloc[-1])
    latest_ema20 = float(df['EMA_20'].iloc[-1])
    latest_ema50 = float(df['EMA_50'].iloc[-1])
    latest_upper_bb = float(df['Upper_BB'].iloc[-1])
    latest_lower_bb = float(df['Lower_BB'].iloc[-1])
    latest_ma20 = float(df['MA_20'].iloc[-1])
    latest_low = float(df['Low'].iloc[-2]) 
    swing_high = float(df['High'].tail(30).max())

    signals = []

    # --- STRATEGY 1: GOLDEN RETRACTION ---
    is_trend_up = latest_ema50 < latest_ema20
    is_near_ema = abs(latest_close - latest_ema20) / latest_close < 0.02 

    if is_trend_up and is_near_ema:
        entry = round(latest_close, 2)
        sl = round(latest_low, 2)
        target = round(swing_high, 2)
        risk = entry - sl
        if risk > 0:
            signals.append({
                "Strategy": "Golden Retrace",
                "Entry": entry,
                "Stop Loss": sl,
                "Target": target,
                "RR Ratio": round((target - entry) / risk, 2)
            })

    # --- STRATEGY 2: BOLLINGER SQUEEZE ---
    current_bandwidth = (latest_upper_bb - latest_lower_bb) / latest_ma20
    bw_series = (df['Upper_BB'].tail(20) - df['Lower_BB'].tail(20)) / df['MA_20'].tail(20)
    avg_bandwidth = float(bw_series.mean())
    
    is_squeeze = current_bandwidth < avg_bandwidth
    is_breakout = latest_close > latest_upper_bb

    if is_breakout: 
        entry = round(latest_upper_bb, 2)
        sl = round(latest_ma20, 2)
        bb_width = latest_upper_bb - latest_lower_bb
        target = round(latest_close + bb_width, 2)
        risk = entry - sl
        if risk > 0:
            signals.append({
                "Strategy": "BB Breakout",
                "Entry": entry,
                "Stop Loss": sl,
                "Target": target,
                "RR Ratio": round((target - entry) / risk, 2)
            })

    return signals

# --- MAIN APP UI ---
st.title("📈 Swing Scanner")
st.caption("Version 16: Calculator & Guide Included")

# --- TABS ---
tab1, tab2, tab3, tab4 = st.tabs(["🔍 Market Scanner", "📊 Individual Analysis", "🧮 Position Calculator", "📘 How to Use"])

# --- TAB 1: MARKET SCANNER ---
with tab1:
    col_p, col_i = st.columns(2)
    with col_p:
        period = st.selectbox("Period", options=["1mo", "3mo", "6mo", "1y", "2y"], index=2)
    with col_i:
        interval = st.selectbox("Interval", options=["1d", "5d", "1wk"], index=0)
    
    st.button("⚡ SCAN NOW", type="primary", key="scan_btn")
    
    def run_scan(period, interval):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        all_results = []
        
        for i, stock in enumerate(WATCHLIST):
            status_text.text(f"Scanning {stock} ({i+1}/{len(WATCHLIST)})...")
            data = get_data(stock, period, interval)
            
            if data is not None:
                data = calculate_indicators(data)
                found_signals = check_strategies(data)
                for sig in found_signals:
                    sig["Stock"] = stock.replace(".NS", "") 
                    all_results.append(sig)
            
            progress_bar.progress((i + 1) / len(WATCHLIST))

        status_text.text("Scan Complete!")

        if all_results:
            st.success(f"✅ Found {len(all_results)} trades!")
            st.session_state.scan_results = all_results
        else:
            st.warning("⚠️ No trades found.")
            st.session_state.scan_results = []

    if "scan_btn" in st.session_state: 
        run_scan(period, interval)
        del st.session_state["scan_btn"]

    if st.session_state.scan_results:
        df_results = pd.DataFrame(st.session_state.scan_results)
        df_results = df_results[['Stock', 'Strategy', 'Entry', 'Stop Loss', 'Target', 'RR Ratio']]
        df_results = df_results.sort_values(by="RR Ratio", ascending=False)
        
        for col in ['Entry', 'Stop Loss', 'Target', 'RR Ratio']:
            df_results[col] = df_results[col].map(lambda x: f"{x:.2f}")
        
        st.dataframe(df_results, width='stretch', hide_index=True)

# --- TAB 2: INDIVIDUAL ANALYSIS ---
with tab2:
    ticker_input = st.text_input("Analyze Specific Stock", value="RELIANCE").upper()
    ticker = f"{ticker_input}.NS"
    df = get_data(ticker, period="6mo", interval="1d")
    
    if df is not None:
        df = calculate_indicators(df)
        trend, trend_color, resistance, support = get_market_structure(df)
        latest = df.iloc[-1]
        
        st.subheader(f"Chart: {ticker_input}")
        fig = make_subplots(rows=1, cols=1)
        
        fig.add_trace(go.Candlestick(
            x=df['Date'], 
            open=df['Open'], 
            high=df['High'], 
            low=df['Low'], 
            close=df['Close'], 
            name='Price',
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Open: %{open:.2f}<br>"
                "High: %{high:.2f}<br>"
                "Low: %{low:.2f}<br>"
                "Close: %{close:.2f}<br>"
                "<extra></extra>"
            )
        ))
        
        fig.add_trace(go.Scatter(
            x=df['Date'], 
            y=df['Upper_BB'], 
            line=dict(color='rgba(0, 100, 200, 0.4)', width=1), 
            name='Upper BB'
        ))
        fig.add_trace(go.Scatter(
            x=df['Date'], 
            y=df['Lower_BB'], 
            line=dict(color='rgba(0, 100, 200, 0.4)', width=1), 
            name='Lower BB', 
            fill='tonexty', 
            fillcolor='rgba(0, 100, 200, 0.05)'
        ))
        
        fig.add_hline(y=resistance, line_dash="dash", line_color="red", 
                     annotation_text=f"Resistance: {resistance}", annotation_position="top left")
        fig.add_hline(y=support, line_dash="dash", line_color="green", 
                     annotation_text=f"Support: {support}", annotation_position="bottom left")
        
        fig.add_trace(go.Scatter(x=df['Date'], y=df['EMA_20'], line=dict(color='orange', width=1), name='EMA 20'))
        fig.add_trace(go.Scatter(x=df['Date'], y=df['EMA_50'], line=dict(color='blue', width=1), name='EMA 50'))
        
        fig.update_layout(xaxis_rangeslider_visible=False, height=600, hovermode='x unified')
        st.plotly_chart(fig, width='stretch')
        
        st.divider()
        st.subheader("Dashboard Details")
        
        d1, d2, d3 = st.columns(3)
        
        with d1:
            st.markdown(f"""
            <div class="card">
                <div class="card-header">Market Trend</div>
                <h2 style='text-align: center; color: {trend_color};'>{trend}</h2>
                <hr style="border:0; border-top:1px solid #eee; margin:10px 0;">
                <div class="card-row"><span class="label">Open:</span> <span class="value">{latest['Open']:.2f}</span></div>
                <div class="card-row"><span class="label">High:</span> <span class="value">{latest['High']:.2f}</span></div>
                <div class="card-row"><span class="label">Low:</span> <span class="value">{latest['Low']:.2f}</span></div>
                <div class="card-row"><span class="label">Close:</span> <span class="value positive">{latest['Close']:.2f}</span></div>
            </div>
            """, unsafe_allow_html=True)
            
        with d2:
            st.markdown(f"""
            <div class="card">
                <div class="card-header">Key Levels</div>
                <div class="card-row"><span class="label">Resistance:</span> <span class="value negative">{resistance:.2f}</span></div>
                <div class="card-row"><span class="label">Support:</span> <span class="value positive">{support:.2f}</span></div>
                <div class="card-row"><span class="label">20 EMA:</span> <span class="value">{df['EMA_20'].iloc[-1]:.2f}</span></div>
                <div class="card-row"><span class="label">50 EMA:</span> <span class="value">{df['EMA_50'].iloc[-1]:.2f}</span></div>
            </div>
            """, unsafe_allow_html=True)
            
        with d3:
            signals = check_strategies(df)
            if signals:
                for s in signals:
                    border_color = "orange" if "Golden" in s['Strategy'] else "blue"
                    st.markdown(f"""
                    <div class="card" style="border-top: 4px solid {border_color}">
                        <div class="card-header">{s['Strategy']} Found</div>
                        <div class="card-row"><span class="label">Entry:</span> <span class="value positive">{s['Entry']:.2f}</span></div>
                        <div class="card-row"><span class="label">Target:</span> <span class="value positive">{s['Target']:.2f}</span></div>
                        <div class="card-row"><span class="label">Stop Loss:</span> <span class="value negative">{s['Stop Loss']:.2f}</span></div>
                        <hr style="border:0; border-top:1px solid #eee; margin:10px 0;">
                        <div class="card-row"><span class="label">R:R Ratio:</span> <span class="value" style="font-size:18px;">{s['RR Ratio']:.2f}</span></div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("⏸️ No active signals")

# --- TAB 3: POSITION SIZE CALCULATOR ---
with tab3:
    st.subheader("🧮 Risk Management Calculator")
    st.info("Use this before placing any trade to survive in the market.")
    
    col_cap, col_risk, col_space = st.columns([1, 1, 0.5])
    
    with col_cap:
        total_capital = st.number_input("Total Capital (₹)", min_value=1000, value=10000, step=500)
    
    with col_risk:
        risk_percent = st.slider("Risk Per Trade (%)", min_value=0.5, max_value=5.0, value=1.0, step=0.5)
        
    st.divider()
    
    col_entry, col_sl = st.columns(2)
    with col_entry:
        entry_price = st.number_input("Entry Price (₹)", min_value=1.0, value=100.0)
    with col_sl:
        sl_price = st.number_input("Stop Loss (₹)", min_value=1.0, value=95.0)
    
    # CALCULATION LOGIC
    risk_per_share = abs(entry_price - sl_price)
    max_risk_amount = total_capital * (risk_percent / 100)
    
    if risk_per_share > 0:
        quantity = int(max_risk_amount // risk_per_share)
        total_margin = quantity * entry_price
    else:
        quantity = 0
        total_margin = 0
    
    st.divider()
    
    c1, c2 = st.columns(2)
    
    with c1:
        st.metric("Max Shares to Buy", f"{quantity}", delta="Quantity")
        st.caption(f"Risking ₹{max_risk_amount:.2f} ({risk_percent}%)")
        
    with c2:
        st.metric("Total Margin Required", f"₹{total_margin:.2f}")
        
    if quantity == 0:
        st.error("Risk per share is 0 or capital too low. Adjust Entry/SL.")

# --- TAB 4: HOW TO USE ---
with tab4:
    st.header("📘 How to Use This Scanner")
    
    st.markdown("""
    <div class="guide-header">Step 1: Use the Market Scanner</div>
    <ul>
        <li>Go to <b>Tab 1</b>.</li>
        <li>Select Period <b>6mo</b> and Interval <b>1d</b>.</li>
        <li>Click <b>SCAN NOW</b>.</li>
        <li>Look for stocks with an <b>RR Ratio > 2.0</b>.</li>
        <li>Note down the Stock Name, Entry, and Stop Loss.</li>
    </ul>

    <div class="guide-header">Step 2: Verify the Trade</div>
    <ul>
        <li>Go to <b>Tab 2 (Individual Analysis)</b>.</li>
        <li>Type the stock name to see the chart.</li>
        <li><b>Check Trend:</b> Is it UPTREND (Green)? If yes, proceed. If Downtrend (Red), skip.</li>
        <li><b>Check Bollinger Bands:</b> Is the price squeezing (bands close) or breaking out?</li>
    </ul>

    <div class="guide-header">Step 3: Calculate Position Size</div>
    <ul>
        <li>Go to <b>Tab 3 (Position Calculator)</b>.</li>
        <li>Enter your Total Capital (e.g., ₹10,000).</li>
        <li>Enter Entry and Stop Loss from the scanner.</li>
        <li>Use the <b>Max Shares to Buy</b> quantity. <b>DO NOT</b> buy more than this.</li>
    </ul>

    <div class="guide-header">Strategy Explanations</div>
    <p><b>1. Golden Retrace:</b> Buy when a trending stock dips to the orange line (20 EMA).</p>
    <p><b>2. BB Breakout:</b> Buy when a quiet stock explodes out of the blue shaded area.</p>

    <div class="guide-header" style="color: red;">⚠️ Important Rules</div>
    <ul>
        <li>Never risk more than 1% of your capital on one trade.</li>
        <li>Always set the Stop Loss in your broker app.</li>
        <li>Don't panic if the trade doesn't move in 2 hours. Swing trades take time (2-5 days).</li>
    </ul>
    """, unsafe_allow_html=True)