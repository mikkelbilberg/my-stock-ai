import streamlit as st
import yfinance as yf
import requests
import json
import plotly.express as px
import pandas as pd
import time

# --- CONFIGURATION ---
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    st.error("⚠️ API Key not found. Please set it in Streamlit Secrets.")
    st.stop()

WATCHLIST = ["NVDA", "TSLA", "AAPL", "AMD", "MSFT", "BTC-USD", "ETH-USD"]

# --- SETUP PAGE ---
st.set_page_config(page_title="Gemini 5.1 Rotator", layout="wide")
st.title("🚀 Gemini 5.1 TradeStation (Quota Safe Mode)")

# --- FUNCTIONS ---

def get_gemini_response(prompt):
    """
    THE ROTATOR:
    Tries multiple models in order. 
    If one gives '429 Quota Exceeded' or '404 Not Found', it moves to the next.
    """
    # Priority list: Newest -> Fastest -> Oldest (Reliable)
    models_to_try = [
        "gemini-2.0-flash-exp", 
        "gemini-1.5-flash", 
        "gemini-1.5-flash-8b",
        "gemini-1.5-pro",
        "gemini-1.0-pro"
    ]
    
    headers = {'Content-Type': 'application/json'}
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    
    last_error = ""
    
    for model in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={API_KEY}"
        try:
            # Send Request
            response = requests.post(url, headers=headers, data=json.dumps(data))
            
            # 200 = Success
            if response.status_code == 200:
                return response.json()['candidates'][0]['content']['parts'][0]['text']
            
            # If 429 (Quota Full) or 404 (Not Found), we just continue to the next model
            else:
                last_error = f"Model {model} Error: {response.status_code}"
                continue 
                
        except Exception as e:
            last_error = str(e)
            continue
            
    return f"AI System Overload: All models are busy or quota exceeded. Please wait 1 minute. ({last_error})"

def get_safe_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1d")
        price = hist['Close'].iloc[-1] if not hist.empty else 0.0
        return f"{ticker}: ${price:,.2f}"
    except:
        return f"{ticker}: Data Unavailable"

def get_chart_data(ticker):
    stock = yf.Ticker(ticker)
    hist = stock.history(period="1mo")
    return hist

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
        prompt = f"Act as a Wall Street Analyst. Data: {market_data}. 1. Market mood summary. 2. Biggest winner."
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
    context = st.session_state.get('market_data', "No live data scanned yet.")
    style = "Keep it under 50 words." if response_style == "Short & Direct" else "Deep professional breakdown."
    full_prompt = f"ROLE: Hedge Fund Manager. CONTEXT: {context}. USER: {user_question}. STYLE: {style}"
    
    with st.spinner("Thinking..."):
        st.markdown(get_gemini_response(full_prompt))

# --- SECTION 4: PORTFOLIO BUILDER ---
st.divider()
st.header("4. 💰 Strategy Builder")
st.error("⚠️ DISCLAIMER: Educational purposes only.")

col1, col2 = st.columns([1, 2])
with col1:
    investment = st.number_input("Investment Amount ($)", min_value=100, value=1000, step=100)
    risk_level = st.radio("Select Risk Tolerance", ["Very Low", "Low", "Moderate", "High", "Very High"])
    generate_btn = st.button("Generate Strategy")

risk_map = {
    "Very Low": {"Bonds": 70, "Cash": 20, "Index Funds": 10},
    "Low": {"Bonds": 50, "Index Funds": 30, "Cash": 10, "Stocks": 10},
    "Moderate": {"Index Funds": 40, "Stocks": 30, "Bonds": 20, "Cash": 10},
    "High": {"Stocks": 50, "Crypto": 30, "Index Funds": 10, "Tech ETFs": 10},
    "Very High": {"Crypto": 60, "Tech Options": 20, "Stocks": 20}
}

with col2:
    if generate_btn:
        allocations = risk_map[risk_level]
        df = pd.DataFrame(list(allocations.items()), columns=['Asset', 'Percentage'])
        fig = px.pie(df, values='Percentage', names='Asset', title=f"Allocation for ${investment:,.0f}")
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("📋 Detailed Buying Guide")
        ai_prompt = f"Advisor role. Budget: ${investment}. Risk: {risk_level}. Allocation: {allocations}. Give specific ticker recommendations."
        with st.spinner("Finding a free AI model..."):
            st.markdown(get_gemini_response(ai_prompt))
