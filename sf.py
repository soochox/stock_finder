import yfinance as yf
import pandas as pd
import streamlit as st
import json
import os

FAV_FILE = "favorites.json"

def load_favorites():
    if os.path.exists(FAV_FILE):
        with open(FAV_FILE, "r") as f:
            return json.load(f)
    return []

def save_favorites(favs):
    with open(FAV_FILE, "w") as f:
        json.dump(favs, f)

def calculate_rsi(close_prices, period=14):
    delta = close_prices.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def get_stock_data(symbol):
    try:
        df = yf.Ticker(symbol).history(period="1y")
        # st.write(f"📦 {symbol} 데이터 샘플:", df.tail())

        if df.empty or "Close" not in df.columns or "Volume" not in df.columns:
            st.warning(f"⚠️ {symbol} 데이터프레임이 비어 있거나 필수 열이 없습니다.")
            return None

        close = df["Close"]
        volume = df["Volume"]

        if len(close) < 2 or len(volume) < 2:
            st.warning(f"⚠️ {symbol} 데이터가 부족합니다.")
            return None

        price = close.iloc[-1]
        prev = close.iloc[-2]        
        change_pct = (price - prev) / prev * 100

        rsi_series = calculate_rsi(close)
        rsi = rsi_series.iloc[-1]

        vol1, vol2 = volume.iloc[-1], volume.iloc[-2]
        if not pd.isna(vol1) and not pd.isna(vol2) and vol2 != 0:
            vol_change_pct = (vol1 - vol2) / vol2 * 100
        else:
            vol_change_pct = None

        ma20 = close.rolling(20).mean().iloc[-1]
        ma200 = close.rolling(200).mean().iloc[-1]
        dev20 = (price - ma20) / ma20 * 100
        dev200 = (price - ma200) / ma200 * 100

        return {
            "현재가": round(price,2),
            "등락률": round(change_pct,2),
            "RSI": round(rsi,2),
            "거래량변화%": round(vol_change_pct,2),
            "20일 이격도": round(dev20,2),
            "200일 이격도": round(dev200,2)
        }

    except Exception as e:
        st.error(f"❌ {symbol} 오류 발생: {e}")
        return None

# Streamlit 앱 시작
st.title("📈 심플 주식 대시보드")

favorites = load_favorites()

if favorites:
    st.subheader("🌟 즐겨찾기 종목 요약")

    data = {}
    col_names = []

    for sym in favorites:
        stock = get_stock_data(sym)
        if stock:
            
            label = f"{sym}"
            col_names.append(label)

            for key in ["현재가", "등락률", "RSI", "거래량변화%", "20일 이격도", "200일 이격도"]:
                val = stock.get(key)                
                # print(val, key, sym)  # Debugging line
                data.setdefault(key, []).append(val)
        else:
            label = f"{sym} (N/A)"
            col_names.append(label)
            for key in ["현재가", "등락", "RSI", "거래량변화%", "20일 이격도", "200일 이격도"]:
                data.setdefault(key, []).append("N/A")

    # print(data)  # Debugging line
    print(col_names)  # Debugging line
    
    # df = pd.DataFrame(data, index=["현재가", "등락률", "RSI", "거래량변화%", "20일 이격도", "200일 이격도"], columns=col_names).T
    df = pd.DataFrame(data).T
    df.columns = col_names
    df = df.T

    print(df.head(5))  # Display only the first 5 rows


    def highlight(val, row_name):
        if isinstance(val, (int, float)):
            if row_name == "RSI":
                if val > 70:
                    return 'color: red'
                elif val < 30:
                    return 'color: blue'
            elif row_name in ["거래량변화%", "20일 이격도", "200일 이격도"]:
                return 'color: red' if val > 0 else 'color: blue'
        return ''

    def style_func(df):
        styled = df.style
        for idx in df.index:
            styled = styled.applymap(lambda v: highlight(v, idx), subset=pd.IndexSlice[[idx], :])
        styled = styled.format(precision=2)
        return styled

    styled_df = style_func(df)
    st.write(styled_df)

else:
    st.info("현재 즐겨찾기 종목이 없습니다.")

symbol = st.text_input("🔍 검색할 종목 입력 (예: AAPL, TQQQ)").upper()

if st.button("🔍 종목 검색"):
    result = get_stock_data(symbol)
    if result:
        st.subheader(f"📊 {symbol} 개별 종목 정보")
        summary_df = pd.DataFrame(result, index=[symbol]).T
        summary_df.columns = [symbol]
        st.dataframe(summary_df)
    else:
        st.error("❌ 데이터를 불러올 수 없습니다.")

if st.button("📌 즐겨찾기에 추가"):
    if symbol and symbol not in favorites:
        favorites.append(symbol)
        save_favorites(favorites)
        st.success(f"{symbol}이(가) 즐겨찾기에 추가되었습니다.")

if st.button("🗑️ 즐겨찾기에서 제거"):
    if symbol in favorites:
        favorites.remove(symbol)
        save_favorites(favorites)
        st.warning(f"{symbol}이(가) 즐겨찾기에서 제거되었습니다.")
