import streamlit as st
import yfinance as yf
import requests # Direct web connection
import json
import plotly.express as px
import pandas as pd

# --- CONFIGURATION ---
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    st.error("⚠️ API Key not found. Please set it in Streamlit Secrets.")
    st.stop()

WATCHLIST = ["NVDA", "TSLA", "AAPL", "AMD", "MSFT", "BTC-USD", "ETH-USD"]

# --- SETUP PAGE ---
st.set_page_config(page_title="Gemini 4.1 EU Safe", layout="wide")
st.title("🚀 Gemini 4.1 TradeStation (EU Safe Mode)")

# --- FUNCTIONS ---
def get_safe_data(ticker):
    """Fetches data safely."""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1d")
        price = hist['Close'].iloc[-1] if not hist.empty else 0.0
        return f"{ticker}: ${price:,.2f}"
    except:
        return f"{ticker}: Data Unavailable"

def get_chart_data(ticker):
    """Fetches 1-month history for the chart."""
    stock = yf.Ticker(ticker)
    hist = stock.history(period="1mo")
    return hist

def get_gemini_response(prompt):
    """
    MANUAL MODE WITH FALLBACK
    1. Tries the new Flash model (Fastest).
    2. If that fails (Error 404 in EU), switches to Standard Pro model.
    """
    headers = {'Content-Type': 'application/json'}
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    
    # LIST OF MODELS TO TRY
    # We try them in order. If one works, we return the answer.
    models = [
        "gemini-1.5-flash", 
        "gemini-pro",        # <--- The "Old Faithful" that works everywhere
        "gemini-1.0-pro"
    ]
    
    last_error = ""
    
    for model_name in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={API_KEY}"
        
        try:
            response = requests.post(url, headers=headers, data=json.dumps(data))
            
            if response.status_code == 200:
                # Success! Return the answer immediately.
                return response.json()['candidates'][0]['content']['parts'][0]['text']
            else:
                # If failed, save error and loop to the next model
                last_error = f"Model {model_name} failed: {response.text}"
                continue
                
        except Exception as e:
            last_error = str(e)
            continue

    return f"AI Error: All models failed. Your API Key might be invalid or region-blocked. Last Error: {last_error}"

# --- SECTION 1: MARKET SCANNER ---
st.header("1. 📡 Live Market Scanner")

if st.button("🔄 Scan Markets Now", type="primary"):
    with st.spinner('Scanning...'):
        market_data = ""
        progress = st.progress(0)
        for i, ticker in enumerate(WATCHLIST):
            data = get_safe_data(ticker)
            market_data += data + "\n"
            progress.progress((i + 1) / len(WATCHLIST))
        
        st.session_state['market_data'] = market_data
        
        prompt = f"""
        Act as a Wall Street Analyst. Data: {market_data}
        1. Give a 1-sentence mood summary.
        2. Who is the winner today?
        """
        st.success("Scan Complete")
        st.markdown(get_gemini_response(prompt))

# --- SECTION 2: INTERACTIVE CHARTS ---
st.divider()
st.header("2. 📊 Interactive Price Charts")

selected_ticker = st.selectbox("Select a Stock to View Chart:", WATCHLIST)

if selected_ticker:
    try:
        chart_data = get_chart_data(selected_ticker)
        fig = px.line(chart_data, y='Close', title=f"{selected_ticker} - 30 Day Price Trend")
        fig.update_layout(xaxis_title="Date", yaxis_title="Price ($)")
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Could not load chart: {e}")

# --- SECTION 3: CHAT ANALYST ---
st.divider()
st.header("3. 💬 Ask the Analyst")

col_chat1, col_chat2 = st.columns([3, 1])

with col_chat1:
    user_question = st.text_area("Question:", height=100, placeholder="E.g., What is the outlook for Tech?")

with col_chat2:
    st.write("Response Style:")
    response_style = st.radio("Style", ["Short & Direct", "Detailed Analysis"])

if st.button("Run Analysis"):
    if 'market_data' in st.session_state:
        context = st.session_state['market_data']
    else:
        context = "No live data scanned yet."

    if response_style == "Short & Direct":
        style = "Keep it under 50 words. Be blunt."
    else:
        style = "Give a deep, professional breakdown."

    full_prompt = f"""
    ROLE: Hedge Fund Manager.
    CONTEXT: {context}
    USER: {user_question}
    STYLE: {style}
    """
    
    with st.spinner("Thinking..."):
        st.markdown(get_gemini_response(full_prompt))

# --- SECTION 4: PORTFOLIO BUILDER (ALL 5 LEVELS) ---
st.divider()
st.header("4. 💰 Strategy Builder")
st.error("⚠️ DISCLAIMER: This is for educational purposes only. NOT financial advice.")

col1, col2 = st.columns([1, 2])

with col1:
    investment = st.number_input("Investment Amount ($)", min_value=100, value=1000, step=100)
    risk_level = st.radio("Select Risk Tolerance", 
                          ["Very Low", "Low", "Moderate", "High", "Very High"])
    
    generate_btn = st.button("Generate Strategy")

risk_map = {
    "Very Low": {"Bonds": 70, "Cash": 20, "Index Funds": 10, "Stocks": 0, "Crypto": 0},
    "Low": {"Bonds": 50, "Index Funds": 30, "Cash": 10, "Stocks": 10, "Crypto": 0},
    "Moderate": {"Index Funds": 40, "Stocks": 30, "Bonds": 20, "Crypto": 5, "Cash": 5},
    "High": {"Stocks": 50, "Crypto": 30, "Index Funds": 10, "Bonds": 0, "Tech ETFs": 10},
    "Very High": {"Crypto": 60, "Tech Options": 20, "Stocks": 20, "Bonds": 0, "Cash": 0}
}

with col2:
    if generate_btn:
        # 1. Draw Pie Chart
        allocations = risk_map[risk_level]
        df = pd.DataFrame(list(allocations.items()), columns=['Asset', 'Percentage'])
        df = df[df['Percentage'] > 0]
        
        fig = px.pie(df, values='Percentage', names='Asset', 
                     title=f"Recommended Allocation for ${investment:,.0f}",
                     color_discrete_sequence=px.colors.sequential.RdBu)
        st.plotly_chart(fig, use_container_width=True)
        
        # 2. Get AI Advice
        st.subheader("📋 Detailed Buying Guide")
        
        ai_prompt = f"""
        Act as a professional financial advisor. 
        User has ${investment} and a '{risk_level}' risk tolerance.
        The recommended allocation is: {allocations}.
        
        Task:
        1. Break down exactly how much money to put in each category.
        2. Recommend SPECIFIC tickers/assets for 2026.
        3. Explain the risk warning.
        """
        
        with st.spinner("Calculating optimal assets..."):
            advice = get_gemini_response(ai_prompt)
            st.markdown(advice)
