import streamlit as st
import yfinance as yf

st.title("🍎 애플 주가 정보")

try:
    ticker = yf.Ticker("AAPL")
    data = ticker.history(period="1y")

    if data.empty or len(data) < 2:
        st.error("❌ AAPL 데이터가 비어 있습니다.")
        st.write("받은 데이터:", data)
    else:
        prev_close = data["Close"].iloc[-2]
        current_price = data["Close"].iloc[-1]
        change_pct = (current_price - prev_close) / prev_close * 100

        st.metric(
            label="현재가 (USD)",
            value=f"{current_price:.2f}",
            delta=f"{change_pct:.2f}%",
            delta_color="inverse"
        )
except Exception as e:
    st.error(f"데이터 로딩 중 오류 발생: {e}")
