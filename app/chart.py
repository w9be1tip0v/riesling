import streamlit as st
import plotly.graph_objects as go

# Plot a Candlestick Chart
def plot_candlestick_chart(df):
    fig = go.Figure(data=[go.Candlestick(x=df['Date'],
                open=df['Open'], high=df['High'],
                low=df['Low'], close=df['Close'])])

    fig.update_layout(title='Candlestick Chart', xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)
