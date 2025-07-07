from django.shortcuts import render, redirect
from django.http import JsonResponse
import os
from django.conf import settings
import yfinance as yf
import json
import pandas as pd # Added import for pandas to use pd.isna()

from .utils import (
    get_nifty_sensex_data,
    get_top_gainers_losers,
    fetch_commodity_data,
    get_latest_news,
    get_stock_chart_data
)

# A simple mapping for demonstration. In a real app, you might fetch this from a DB or a more robust source.
# Ensure these tickers are correct for Yahoo Finance (e.g., .NS for NSE)
company_ticker_map = {
    "Tata Motors": "TATAMOTORS.NS",
    "Reliance Industries": "RELIANCE.NS",
    "Infosys": "INFY.NS",
    "HDFC Bank": "HDFCBANK.NS",
    "ICICI Bank": "ICICIBANK.NS",
    "Bajaj Finance": "BAJFINANCE.NS",
    "Asian Paints": "ASIANPAINT.NS",
    "Maruti Suzuki": "MARUTI.NS",
    "TCS": "TCS.NS",
    "HUL": "HINDUNILVR.NS",
    "SBI": "SBIN.NS", # Added for testing
    "Axis Bank": "AXISBANK.NS", # Added for testing
    "Wipro": "WIPRO.NS", # Added for testing
    "L&T": "LT.NS", # Added for testing
}


def index_view(request):
    return render(request, 'app/index.html', {})

def alertx_view(request):
    return render(request, 'app/alertx.html', {})

def pricing_view(request):
    return render(request, 'app/pricing.html', {})

def dashboard_view(request):
    nifty_sensex_data = get_nifty_sensex_data()
    raw_top_gainers, raw_top_losers, gainer_name, top_gainer_ticker = get_top_gainers_losers()
    commodity_data = fetch_commodity_data()
    latest_news = get_latest_news()

    def get_logo_static_path(ticker_symbol):
        clean_ticker = ticker_symbol.split('.')[0].upper()
        logo_filename = f"{clean_ticker}.png"

        print(f"DEBUG: Processing ticker_symbol: {ticker_symbol}")
        print(f"DEBUG: Cleaned ticker: {clean_ticker}")
        print(f"DEBUG: Expected logo filename: {logo_filename}")

        logo_full_path = os.path.join(settings.BASE_DIR, 'app', 'static', 'images', logo_filename)
        print(f"DEBUG: Checking absolute path: {logo_full_path}")

        if os.path.exists(logo_full_path):
            print(f"DEBUG: Logo FOUND for {clean_ticker}! Returning: images/{logo_filename}")
            return f"images/{logo_filename}"
        else:
            print(f"DEBUG: Logo NOT FOUND for {clean_ticker}. Returning default.")
            return "images/default.png"

    top_gainers_with_logos = []
    for ticker, percent in raw_top_gainers:
        logo_path = get_logo_static_path(ticker)
        top_gainers_with_logos.append({
            'ticker': ticker,
            'percent': percent,
            'logo_path': logo_path
        })

    top_losers_with_logos = []
    for ticker, percent in raw_top_losers:
        logo_path = get_logo_static_path(ticker)
        top_losers_with_logos.append({
            'ticker': ticker,
            'percent': percent,
            'logo_path': logo_path
        })

    print(f"\n--- DEBUG: Dashboard View Context ---")
    print(f"   gainer_name: {gainer_name}")
    print(f"   gainer_ticker (passed to JS): {top_gainer_ticker}")
    print("-------------------------------")

    context = {
        'nifty_sensex': nifty_sensex_data,
        'top_gainers': top_gainers_with_logos,
        'top_losers': top_losers_with_logos,
        'gainer_name': gainer_name,
        'gainer_ticker': top_gainer_ticker,
        'commodities': commodity_data,
        'news_items': latest_news,
    }
    return render(request, 'app/dashboard.html', context)


def get_chart_data(request):
    ticker = request.GET.get('ticker')
    period = request.GET.get('period', '1y')

    print(f"\n--- DEBUG: get_chart_data View ---")
    print(f"   Received ticker: {ticker}, period: {period}")

    if not ticker:
        print("   Error: Ticker not provided to get_chart_data.")
        return JsonResponse({'error': 'Ticker not provided'}, status=400)

    data_points, last_price, percent_change = get_stock_chart_data(ticker, period)

    print(f"   Data from get_stock_chart_data:")
    print(f"     len(data_points): {len(data_points)}")
    print(f"     last_price: {last_price}")
    print(f"     percent_change: {percent_change}")

    response_data = {
        'data': data_points,
        'last_price': f"₹ {last_price:,.2f}",
        'percent_change': f"{percent_change:.2f}%",
        'is_negative': percent_change < 0
    }
    print(f"   Sending JSON response: {response_data}")
    print("---------------------------------")
    return JsonResponse(response_data)

from django.views.decorators.http import require_GET

# View to render the stock widget HTML page
def stocks_widget_view(request):
    """
    Renders the stock_data.html template which contains the stock widget.
    Passes the company_ticker_map to the template for client-side suggestions.
    """
    # Convert keys of company_ticker_map to a list for easy JavaScript consumption
    company_names = list(company_ticker_map.keys())
    context = {
        'company_names_json': json.dumps(company_names)
    }
    return render(request, 'app/stock_data.html', context)

@require_GET
def get_stock_data(request):
    """
    API endpoint to fetch detailed stock metrics for a given company name.
    Uses yfinance to get data.
    """
    company_name = request.GET.get('company_name')
    if not company_name:
        return JsonResponse({'error': 'Company name is required'}, status=400)

    ticker_symbol = company_ticker_map.get(company_name)
    if not ticker_symbol:
        return JsonResponse({'error': f'Ticker not found for "{company_name}". Please check the name.'}, status=404)

    try:
        stock = yf.Ticker(ticker_symbol)
        data = stock.info

        # Fetch historical data for current and previous close
        # Use a shorter period like '2d' to ensure we get at least two days if available
        # progress=False to suppress download messages
        historical_data = yf.download(ticker_symbol, period='2d', progress=False)

        print(f"DEBUG: Historical data for {ticker_symbol} (period='2d'):\n{historical_data}")

        current_price = None
        previous_close = None
        close_prices = pd.Series() # Initialize as empty Series

        if not historical_data.empty:
            # Check if columns are multi-indexed (common with yfinance for single ticker with auto_adjust)
            if isinstance(historical_data.columns, pd.MultiIndex):
                # Access the 'Close' column for the specific ticker
                # This will return a Series
                if ('Close', ticker_symbol) in historical_data.columns:
                    close_prices = historical_data[('Close', ticker_symbol)]
                else:
                    print(f"DEBUG: MultiIndex columns, but ('Close', {ticker_symbol}) not found. Columns: {historical_data.columns}")
                    raise ValueError(f"Could not find 'Close' column for {ticker_symbol} in MultiIndex DataFrame.")
            elif 'Close' in historical_data.columns:
                # Standard case: 'Close' column exists directly as a single level
                close_prices = historical_data['Close']
            else:
                print(f"DEBUG: 'Close' column not found in historical data for {ticker_symbol}. Available columns: {historical_data.columns}")
                raise ValueError(f"Could not find 'Close' column for {ticker_symbol}.")

            print(f"DEBUG: Extracted Close prices Series for {ticker_symbol}:\n{close_prices}")

            if not close_prices.empty:
                # Access the scalar value from the Series
                current_price_raw = close_prices.iloc[0]
                if pd.notna(current_price_raw):
                    current_price = float(current_price_raw) # It's already a scalar here

                if len(close_prices) > 1:
                    previous_close_raw = close_prices.iloc[1]
                    if pd.notna(previous_close_raw):
                        previous_close = float(previous_close_raw) # It's already a scalar here
                    else:
                        print(f"DEBUG: Previous close is NaN for {ticker_symbol}")
                else:
                    print(f"DEBUG: Not enough historical data for previous close for {ticker_symbol} (only {len(close_prices)} data points).")
            else:
                print(f"DEBUG: Close prices Series is empty after extraction for {ticker_symbol}")
        else:
            print(f"DEBUG: Historical data is empty for {ticker_symbol}")
            # If historical data is empty, current_price and previous_close will remain None
            # The metrics dictionary will then use "N/A" for these values.


        percentage_change = None
        # Only calculate percentage change if both current_price and previous_close are valid numbers and previous_close is not zero
        if current_price is not None and previous_close is not None and previous_close != 0:
            percentage_change = ((current_price / previous_close) - 1) * 100
        else:
            print(f"DEBUG: Skipping percentage change calculation for {ticker_symbol} due to missing/invalid prices (Current: {current_price}, Previous: {previous_close})")


        market_cap_in_crore = data.get("marketCap", 0) / 10**7 if data.get("marketCap") else 0
        dividend_yield = data.get("dividendYield", None)
        if dividend_yield is not None:
            dividend_yield *= 100 # Convert to percentage
        roce = data.get("returnOnAssets")
        pe = data.get("trailingPE")
        roe = data.get("returnOnEquity")
        book_value = data.get("bookValue")
        face_value = data.get("faceValue")
        high = data.get('fiftyTwoWeekHigh')
        low = data.get('fiftyTwoWeekLow')

        metrics = {
            "Company Name": data.get("longName", "N/A"),
            "Market Cap": f"{market_cap_in_crore:,.2f} Cr",
            "P/E": f"{pe:.2f}" if pe is not None else "N/A",
            "ROCE": f"{roce:.2f}%" if roce is not None else "N/A",
            "Current Price": current_price if current_price is not None else "N/A",
            "Percentage Change": f"{percentage_change:.2f}" if percentage_change is not None else "N/A",
            "Book Value": f"{book_value:.2f}" if book_value is not None else "N/A",
            "ROE": f"{roe:.2f}%" if roe is not None else "N/A",
            "High/Low": f"{high:.2f} / {low:.2f}" if high is not None and low is not None else "N/A",
            "Dividend Yield": f"{dividend_yield:.2f}%" if dividend_yield is not None else "N/A",
            "Face Value": f"{face_value:.0f}" if face_value is not None else "N/A",
            "Website": data.get("website", "#"),
            "Ticker": ticker_symbol # Pass the ticker for the TradingView widget
        }
        return JsonResponse(metrics)

    except Exception as e:
        print(f"Error fetching data for {ticker_symbol}: {e}")
        return JsonResponse({'error': f'Failed to fetch data for {company_name}: {e}'}, status=500)


def subscribe_index(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        if email:
            print(f"Subscription received from: {email}")
        else:
            print("No email received for subscription.")
    return redirect('app:home')
