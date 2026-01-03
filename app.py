import streamlit as st
import yfinance as yf
import google.generativeai as genai
import plotly.express as px
import pandas as pd

# --- CONFIGURATION ---
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    st.error("⚠️ API Key not found. Please set it in Streamlit Secrets.")
    st.stop()

# We stick to the standard model that works everywhere
MODEL_NAME = "gemini-1.5-flash"

WATCHLIST = ["NVDA", "TSLA", "AAPL", "AMD", "MSFT", "BTC-USD", "ETH-USD"]

# --- SETUP PAGE ---
st.set_page_config(page_title="Gemini 3.4 Stable", layout="wide")
st.title("✅ Gemini 3.4 Stable TradeStation")

# --- FUNCTIONS ---
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

def get_gemini_response(prompt):
    genai.configure(api_key=API_KEY)
    try:
        model = genai.GenerativeModel(MODEL_NAME)
        return model.generate_content(prompt).text
    except Exception as e:
        return f"AI Error: {str(e)}"

# --- DASHBOARD ---
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
        
        prompt = f"Analyze this market data in 2 sentences: {market_data}"
        st.success("Scan Complete")
        st.markdown(get_gemini_response(prompt))

# --- CHARTS ---
st.divider()
st.header("2. 📊 Charts")
selected_ticker = st.selectbox("Select Stock:", WATCHLIST)
if selected_ticker:
    st.plotly_chart(px.line(get_chart_data(selected_ticker), y='Close', title=f"{selected_ticker} Price"), use_container_width=True)

# --- CHAT ---
st.divider()
st.header("3. 💬 Ask the Analyst")
user_question = st.text_area("Question:", placeholder="Should I buy or sell?")

if st.button("Run Analysis"):
    context = st.session_state.get('market_data', 'No data yet.')
    prompt = f"Role: Financial Analyst. Context: {context}. User Question: {user_question}. Answer:"
    with st.spinner("Thinking..."):
        st.markdown(get_gemini_response(prompt))

# --- PORTFOLIO ---
st.divider()
st.header("4. 💰 Strategy")
investment = st.number_input("Investment ($)", value=1000)
risk = st.radio("Risk", ["Low", "High"])

if st.button("Generate Strategy"):
    allocations = {"Stocks": 60, "Bonds": 40} if risk == "Low" else {"Crypto": 50, "Stocks": 50}
    
    # Chart
    df = pd.DataFrame(list(allocations.items()), columns=['Asset', 'Percentage'])
    st.plotly_chart(px.pie(df, values='Percentage', names='Asset'), use_container_width=True)
    
    # Text Advice
    prompt = f"Advise on investing ${investment} with {risk} risk. Allocation: {allocations}. Be brief."
    with st.spinner("Calculating..."):
        st.markdown(get_gemini_response(prompt))
