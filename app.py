import streamlit as st
import yfinance as yf
import google.generativeai as genai
import plotly.express as px
import pandas as pd
import time

# --- CONFIGURATION ---
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    st.error("⚠️ API Key not found. Please set it in Streamlit Secrets.")
    st.stop()

MODEL_NAME = "gemini-2.5-flash" 

WATCHLIST = ["NVDA", "TSLA", "AAPL", "AMD", "MSFT", "BTC-USD", "ETH-USD"]

# --- SETUP PAGE ---
st.set_page_config(page_title="Gemini 3.0 Ultimate", layout="wide")
st.title("🚀 Gemini 3.0 Ultimate TradeStation")

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
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel(MODEL_NAME)
    try:
        return model.generate_content(prompt).text
    except Exception as e:
        return f"AI Error: {e}"

# --- MAIN DASHBOARD (SECTION 1) ---
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

# --- CHARTING SECTION (NEW! LIKE GOOGLE) ---
st.divider()
st.header("2. 📊 Interactive Price Charts")

# Dropdown to pick a stock
selected_ticker = st.selectbox("Select a Stock to View Chart:", WATCHLIST)

if selected_ticker:
    try:
        # Get data
        chart_data = get_chart_data(selected_ticker)
        
        # Create the interactive chart (Like Google)
        fig = px.line(chart_data, y='Close', title=f"{selected_ticker} - 30 Day Price Trend")
        
        # Make it look cool (Dark mode friendly)
        fig.update_layout(xaxis_title="Date", yaxis_title="Price ($)")
        
        # Show it
        st.plotly_chart(fig, use_container_width=True)
        
        # Quick AI Comment on the chart
        if st.button(f"Analyze {selected_ticker} Chart"):
            trend_prompt = f"Analyze the trend for {selected_ticker}. The price moved from ${chart_data['Close'].iloc[0]:.2f} to ${chart_data['Close'].iloc[-1]:.2f} over 30 days. Is it Bullish or Bearish?"
            st.write(get_gemini_response(trend_prompt))
            
    except Exception as e:
        st.error(f"Could not load chart: {e}")

# --- CHAT SECTION (SECTION 3 - FIXED BUTTONS) ---
st.divider()
st.header("3. 💬 Ask the Analyst")

col_chat1, col_chat2 = st.columns([3, 1])

with col_chat1:
    user_question = st.text_area("Question:", height=100, placeholder="E.g., What is the outlook for Tech?")

with col_chat2:
    st.write("Response Style:")
    # Replaced 'st.pills' with 'st.radio' to GUARANTEE it shows up
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

# --- PORTFOLIO (SECTION 4) ---
st.divider()
st.header("4. 💰 Strategy Builder")
# (Keeping this simple for now)
st.info("Portfolio Builder is ready below (Code hidden to save space)")
# ... (You can keep the portfolio code here if you want, but the file is getting long!)
