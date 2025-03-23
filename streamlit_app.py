import streamlit as st
import pandas as pd
import numpy as np
import talib as ta
import plotly.graph_objs as go
import time
from binance.client import Client

# Binance API Credentials (Replace with your keys)
API_KEY = "your_api_key"
API_SECRET = "your_api_secret"
client = Client(API_KEY, API_SECRET)

def fetch_data_binance(symbol, interval='5m', limit=100):
    try:
        klines = client.get_klines(symbol=symbol, interval=interval, limit=limit)
        data = pd.DataFrame(klines, columns=[
            'Time', 'Open', 'High', 'Low', 'Close', 'Volume', 
            'CloseTime', 'QuoteAssetVolume', 'NumberOfTrades', 
            'TakerBuyBase', 'TakerBuyQuote', 'Ignore'
        ])
        data['Time'] = pd.to_datetime(data['Time'], unit='ms')
        data.set_index('Time', inplace=True)
        data = data[['Open', 'High', 'Low', 'Close', 'Volume']].astype(float)
        return data
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()

def add_technical_indicators(data, indicators):
    close_prices = data['Close'].astype(float).to_numpy()
    if len(close_prices) < 20:
        st.error("Not enough data points for indicators.")
        return data
    
    if "SMA" in indicators:
        data['SMA_20'] = ta.SMA(close_prices, timeperiod=20)
    if "EMA" in indicators:
        data['EMA_20'] = ta.EMA(close_prices, timeperiod=20)
    if "RSI" in indicators:
        data['RSI'] = ta.RSI(close_prices, timeperiod=14)
    if "MACD" in indicators:
        macd, macd_signal, _ = ta.MACD(close_prices, fastperiod=12, slowperiod=26, signalperiod=9)
        data['MACD'] = macd
        data['MACD_signal'] = macd_signal
    return data

def generate_trade_signals(data, signals):
    trade_signals = []
    if "RSI Buy/Sell" in signals and 'RSI' in data.columns:
        latest_rsi = data['RSI'].iloc[-1]
        if latest_rsi < 30:
            trade_signals.append("Buy Signal (RSI below 30)")
        elif latest_rsi > 70:
            trade_signals.append("Sell Signal (RSI above 70)")
    if "MACD Crossover" in signals and 'MACD' in data.columns and 'MACD_signal' in data.columns:
        if data['MACD'].iloc[-1] > data['MACD_signal'].iloc[-1] and data['MACD'].iloc[-2] <= data['MACD_signal'].iloc[-2]:
            trade_signals.append("Buy Signal (MACD crossover)")
        elif data['MACD'].iloc[-1] < data['MACD_signal'].iloc[-1] and data['MACD'].iloc[-2] >= data['MACD_signal'].iloc[-2]:
            trade_signals.append("Sell Signal (MACD crossover)")
    return trade_signals

def place_order(symbol, side, quantity):
    try:
        order = client.order_market(symbol=symbol, side=side, quantity=quantity)
        return order
    except Exception as e:
        st.error(f"Order failed: {e}")
        return None

def main():
    st.title("Real-Time Trading Bot Dashboard")
    forex_pairs = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT"]
    
    ticker = st.selectbox("Select Cryptocurrency Pair:", forex_pairs)
    indicators = st.multiselect("Select Indicators:", ["SMA", "EMA", "RSI", "MACD"], default=["SMA", "RSI"])
    signals = st.multiselect("Select Trade Signals:", ["RSI Buy/Sell", "MACD Crossover"], default=["RSI Buy/Sell"])
    quantity = st.number_input("Enter Trade Quantity:", min_value=0.01, value=1.0, step=0.01)
    auto_trade = st.checkbox("Enable Auto Trading")
    
    if st.button("Start Live Trading Chart"):
        placeholder = st.empty()
        signal_placeholder = st.empty()
        while True:
            data = fetch_data_binance(ticker)
            if not data.empty:
                data = add_technical_indicators(data, indicators)
                trade_signals = generate_trade_signals(data, signals)
                placeholder.empty()
                st.dataframe(data.tail())
                signal_placeholder.empty()
                signal_placeholder.write("**Trade Signals:**")
                for signal in trade_signals:
                    signal_placeholder.write(f"- {signal}")
                    if auto_trade and "Buy" in signal:
                        place_order(ticker, "BUY", quantity)
                    elif auto_trade and "Sell" in signal:
                        place_order(ticker, "SELL", quantity)
            else:
                st.error("No data found. Check the ticker.")
            time.sleep(60)

if __name__ == "__main__":
    main()
