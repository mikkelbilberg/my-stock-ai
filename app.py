import streamlit as st
import yfinance as yf
import google.generativeai as genai
import plotly.express as px
import pandas as pd
import time

# --- CONFIGURATION ---
# Your Working Key
API_KEY = st.secrets["GEMINI_API_KEY"]
# The model that worked for you in the scan
MODEL_NAME = "gemini-2.5-flash" 

WATCHLIST = ["NVDA", "TSLA", "AAPL", "AMD", "MSFT", "BTC-USD", "ETH-USD"]

# --- SETUP PAGE ---
st.set_page_config(page_title="Gemini 2.5 TradeStation", layout="wide")
st.title("📈 Gemini 2.5 TradeStation")

# --- FUNCTIONS ---
def get_safe_data(ticker):
    """Fetches data safely."""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1d")
        price = hist['Close'].iloc[-1] if not hist.empty else 0.0
        
        # Get News
        news_text = ""
        if stock.news:
            headlines = [n.get('title', 'No Title') for n in stock.news[:2]]
            news_text = " | ".join(headlines)
        
        return f"{ticker}: ${price:,.2f} ({news_text})"
    except:
        return f"{ticker}: Data Unavailable"

def get_gemini_response(prompt):
    """Helper to talk to AI"""
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel(MODEL_NAME)
    try:
        return model.generate_content(prompt).text
    except Exception as e:
        return f"AI Error: {e}"

# --- MAIN DASHBOARD (SECTION 1) ---
st.header("📡 Live Market Scanner")

if st.button("🔄 Scan Markets Now"):
    with st.spinner('Scanning...'):
        market_data = ""
        progress = st.progress(0)
        for i, ticker in enumerate(WATCHLIST):
            data = get_safe_data(ticker)
            market_data += data + "\n"
            progress.progress((i + 1) / len(WATCHLIST))
        
        # Save data to session state so other parts of app can see it
        st.session_state['market_data'] = market_data
        
        prompt = f"""
        Act as a Hedge Fund Manager in 2026.
        Data: {market_data}
        
        1. Give a very short summary of the market mood.
        2. Name the single biggest mover.
        """
        st.success("Scan Complete")
        st.markdown(get_gemini_response(prompt))

# --- CHAT SECTION (SECTION 2) ---
st.divider()
st.header("💬 Ask the Analyst")
st.caption("Ask deep questions about the current market data.")

user_question = st.text_area("What do you want to know?", height=100, placeholder="E.g., Why is Bitcoin up today? Should I sell NVDA?")

if st.button("Ask Analyst"):
    if 'market_data' in st.session_state:
        context = st.session_state['market_data']
    else:
        context = "No live data scanned yet. Using general knowledge."

    full_prompt = f"""
    Context: {context}
    User Question: {user_question}
    
    Provide a detailed, in-depth answer. Use paragraphs and bullet points. 
    Explain the 'Why' behind the moves.
    """
    
    with st.spinner("Thinking deep..."):
        answer = get_gemini_response(full_prompt)
        st.markdown(answer)

# --- PORTFOLIO BUILDER (SECTION 3) ---
st.divider()
st.header("💰 AI Portfolio Builder")
st.error("⚠️ DISCLAIMER: This is for educational purposes only. NOT financial advice.")

col1, col2 = st.columns([1, 2])

with col1:
    investment = st.number_input("Investment Amount ($)", min_value=100, value=1000, step=100)
    risk_level = st.radio("Select Risk Tolerance", 
                          ["Very Low", "Low", "Moderate", "High", "Very High"])
    
    generate_btn = st.button("Generate Strategy")

# Logic to map Risk -> Pie Chart Percentages (Hardcoded for stability)
risk_map = {
    "Very Low": {"Bonds": 70, "Cash": 20, "Index Funds": 10, "Stocks": 0, "Crypto": 0},
    "Low": {"Bonds": 50, "Index Funds": 30, "Cash": 10, "Stocks": 10, "Crypto": 0},
    "Moderate": {"Index Funds": 40, "Stocks": 30, "Bonds": 20, "Crypto": 5, "Cash": 5},
    "High": {"Stocks": 50, "Crypto": 30, "Index Funds": 10, "Bonds": 0, "Tech ETFs": 10},
    "Very High": {"Crypto": 60, "Tech Options": 20, "Stocks": 20, "Bonds": 0, "Cash": 0}
}

with col2:
    if generate_btn:
        # 1. Draw the Pie Chart
        allocations = risk_map[risk_level]
        df = pd.DataFrame(list(allocations.items()), columns=['Asset', 'Percentage'])
        # Filter out 0% assets
        df = df[df['Percentage'] > 0]
        
        fig = px.pie(df, values='Percentage', names='Asset', 
                     title=f"Recommended Allocation for ${investment:,.0f}",
                     color_discrete_sequence=px.colors.sequential.RdBu)
        st.plotly_chart(fig, use_container_width=True)
        
        # 2. Get AI Advice on WHAT to buy inside those categories
        st.subheader("📋 Detailed Buying Guide")
        
        ai_prompt = f"""
        Act as a professional financial advisor. 
        User has ${investment} and a '{risk_level}' risk tolerance.
        The recommended allocation is: {allocations}.
        
        Task:
        1. Break down exactly how much money to put in each category (calculate the dollars).
        2. Recommend SPECIFIC tickers/assets for 2026 (e.g., if Crypto, suggest BTC/ETH. If Bonds, suggest SHY/TLT).
        3. Explain the risk warning for this specific portfolio.
        """
        
        with st.spinner("Calculating optimal assets..."):
            advice = get_gemini_response(ai_prompt)
            st.markdown(advice)