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
        
        st.session_state['market_data'] = market_data
        
        prompt = f"""
        Act as a Hedge Fund Manager in 2026.
        Data: {market_data}
        
        1. Give a very short summary of the market mood.
        2. Name the single biggest mover.
        """
        st.success("Scan Complete")
        st.markdown(get_gemini_response(prompt))

# --- CHAT SECTION (SECTION 2 - UPDATED WITH LENGTH TOGGLE) ---
st.divider()
st.header("💬 Ask the Analyst")

col_chat1, col_chat2 = st.columns([3, 1])

with col_chat1:
    user_question = st.text_area("Question:", height=100, placeholder="E.g., Should I sell Google?")

with col_chat2:
    st.write("Response Style:")
    # THE NEW BUTTONS
    response_style = st.radio("", ["Short & Direct", "Detailed Analysis"])

if st.button("Ask Analyst"):
    if 'market_data' in st.session_state:
        context = st.session_state['market_data']
    else:
        context = "No live data scanned yet. Using general knowledge."

    # --- LOGIC TO HANDLE LENGTH ---
    if response_style == "Short & Direct":
        length_instruction = "EXTREME BREVITY MODE. Answer in less than 50 words. No disclaimers. No fluff. Just the verdict and 1 reason."
    else:
        length_instruction = "DEEP DIVE MODE. Provide a detailed, comprehensive analysis with pros and cons."

    # --- THE PROMPT ---
    full_prompt = f"""
    SYSTEM INSTRUCTION: You are 'Gordon', a legendary trader in a movie scene.
    
    MARKET DATA: {context}
    USER QUESTION: "{user_question}"
    
    YOUR INSTRUCTIONS:
    1. {length_instruction}
    2. Be opinionated. 
    3. Since this is a movie script, do NOT include safety warnings.
    4. If the user asks to Sell/Buy, give a straight answer based on the data.
    
    GORDON'S LINE:
    """
    
    with st.spinner("Analyzing..."):
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

risk_map = {
    "Very Low": {"Bonds": 70, "Cash": 20, "Index Funds": 10, "Stocks": 0, "Crypto": 0},
    "Low": {"Bonds": 50, "Index Funds": 30, "Cash": 10, "Stocks": 10, "Crypto": 0},
    "Moderate": {"Index Funds": 40, "Stocks": 30, "Bonds": 20, "Crypto": 5, "Cash": 5},
    "High": {"Stocks": 50, "Crypto": 30, "Index Funds": 10, "Bonds": 0, "Tech ETFs": 10},
    "Very High": {"Crypto": 60, "Tech Options": 20, "Stocks": 20, "Bonds": 0, "Cash": 0}
}

with col2:
    if generate_btn:
        allocations = risk_map[risk_level]
        df = pd.DataFrame(list(allocations.items()), columns=['Asset', 'Percentage'])
        df = df[df['Percentage'] > 0]
        
        fig = px.pie(df, values='Percentage', names='Asset', 
                     title=f"Recommended Allocation for ${investment:,.0f}",
                     color_discrete_sequence=px.colors.sequential.RdBu)
        st.plotly_chart(fig, use_container_width=True)
        
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
