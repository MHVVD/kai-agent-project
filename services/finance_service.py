# In: services/finance_service.py
import yfinance as yf

# This service will handle fetching and analyzing financial data.

async def get_market_data(ticker: str):
    """Fetches basic market data for a given stock ticker."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        price = info.get('currentPrice')
        recommendation = info.get('recommendationKey', 'N/A')
        print(f"Fetched data for {ticker}: Price={price}, Recommendation={recommendation}")
        # In a real app, you'd return a structured model
        return {"price": price, "recommendation": recommendation}
    except Exception as e:
        print(f"Could not fetch data for {ticker}: {e}")
        return None