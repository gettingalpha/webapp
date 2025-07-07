import yfinance as yf
from bselib.bse import BSE
from datetime import datetime, timedelta
import difflib
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings
import math # Import math module to check for NaN

warnings.simplefilter(action='ignore', category=FutureWarning)

COMPANY_TICKER_MAP = {
    'Aarvi Encon Limited': 'AARVI.NS',
    'Yatra Online Ltd': 'YATRA.NS',
    'WPIL LTD': 'WPIL.NS'
}

COMMODITY_TICKERS = {
    "Gold": "GC=F",
    "Silver": "SI=F",
    "Crude Oil": "CL=F",
    "Natural Gas": "NG=F",
    "Copper": "HG=F"
}

BSE_COMPANY_CODES = [544095, 543992, 590051, 538685, 500405, 532513, 543675, 505872, 522205, 500186, 532827,
            590051, 517544, 540704, 543280, 538685, 538734, 500117, 543252, 500186, 532612, 532612,
            535014, 543712, 513349, 523694, 500008, 539799, 540061, 500280, 538734, 500117, 543252,
            500214, 533320, 526668, 532937, 532967, 512455, 513269, 540704, 538836, 543280, 539678] # Example codes

def fetch_index_data(ticker_symbol):
    """Fetches index data and calculates percentage change."""
    data = yf.download(ticker_symbol, period="5d")
    if not data.empty and len(data) >= 2:
        close = data['Close'].iloc[-1].item()
        previous_close = data['Close'].iloc[-2].item()
        if previous_close != 0:
            percentage = ((close / previous_close) - 1) * 100
            return close, percentage
    return 0.0, 0.0

def get_nifty_sensex_data():
    """Fetches and processes Nifty and Sensex data."""
    nifty_close, nifty_percentage = fetch_index_data("^NSEI")
    sensex_close, sensex_percentage = fetch_index_data("^BSESN")

    return {
        'nifty_close': nifty_close,
        'nifty_percentage': nifty_percentage,
        'nifty_triangle_symbol': "▲" if nifty_percentage >= 0 else "▼",
        'nifty_percentage_color': "green" if nifty_percentage >= 0 else "red",
        'sensex_close': sensex_close,
        'sensex_percentage': sensex_percentage,
        'sensex_triangle_symbol': "▲" if sensex_percentage >= 0 else "▼",
        'sensex_percentage_color': "green" if sensex_percentage >= 0 else "red",
    }

def get_top_gainers_losers():
    """Fetches and processes top gainers and losers."""
    tickers = ["MATRIMONY.NS", "CENTUM.NS", "YATRA.NS", "QUICKHEAL.NS"]
    all_stocks_data = yf.download(tickers, period='5d')
    percentage_changes = {}

    for ticker in tickers:
        try:
            close_today = all_stocks_data['Close'][ticker].iloc[-1]
            close_yesterday = all_stocks_data['Close'][ticker].iloc[-2]
            if close_yesterday != 0:
                percentage_change = (close_today / close_yesterday - 1) * 100
                percentage_changes[ticker] = percentage_change
            else:
                percentage_changes[ticker] = 0.0 # Handle division by zero
        except (KeyError, IndexError):
            percentage_changes[ticker] = 0.0 # Handle missing data

    sorted_stocks = sorted(percentage_changes.items(), key=lambda x: x[1], reverse=True)
    top_5_gainers = sorted_stocks[:5]
    top_5_losers = sorted(sorted_stocks[-5:], key=lambda x: x[1])

    top_gainer_ticker = top_5_gainers[0][0] if top_5_gainers else None
    gainer_name = top_gainer_ticker.split('.')[0] if top_gainer_ticker else "N/A"

    return top_5_gainers, top_5_losers, gainer_name, top_gainer_ticker

def fetch_commodity_data():
    """Fetches and processes commodity data."""
    commodity_data = {}
    for name, ticker in COMMODITY_TICKERS.items():
        try:
            print(f"\n--- Fetching data for {name} ({ticker}) ---")
            df = yf.download(ticker, period="5d", interval="1d")
            print(f"  Received {len(df)} rows for {name}.")

            if 'Close' in df.columns and not df['Close'].empty:
                if len(df) >= 2:
                    latest_close = df['Close'].iloc[-1].item()
                    previous_close = df['Close'].iloc[-2].item()
                    
                    print(f"  Latest Close: {latest_close}")
                    print(f"  Previous Close: {previous_close}")

                    if previous_close != 0:
                        percent_change = ((latest_close - previous_close) / previous_close) * 100
                        print(f"  Calculated percent_change: {percent_change}")

                        if math.isnan(percent_change) or math.isinf(percent_change):
                            print(f"  Warning: percent_change for {name} is NaN or Inf. Setting to N/A.")
                            commodity_data[name] = {"Price": f"$ {latest_close:,.2f}", "Change": "N/A", "Triangle": "", "Color": "gray"}
                        else:
                            commodity_data[name] = {
                                "Price": f"$ {latest_close:,.2f}",
                                "Change": round(percent_change, 2), # <--- CHANGED THIS KEY
                                "Triangle": "▲" if percent_change >= 0 else "▼",
                                "Color": "green" if percent_change >= 0 else "red"
                            }
                    else:
                        print(f"  Previous close for {name} was 0. Setting Change to N/A.")
                        commodity_data[name] = {"Price": f"$ {latest_close:,.2f}", "Change": "N/A", "Triangle": "", "Color": "gray"}
                elif len(df) == 1:
                    latest_close = df['Close'].iloc[-1].item()
                    print(f"  Only one day of data for {name}. Displaying price only.")
                    commodity_data[name] = {
                        "Price": f"$ {latest_close:,.2f}",
                        "Change": "N/A",
                        "Triangle": "",
                        "Color": "gray"
                    }
                else: # len(df) == 0
                    print(f"  No valid data (len=0 or 'Close' column missing/empty) for {name}.")
                    commodity_data[name] = {"Price": "N/A", "Change": "N/A", "Triangle": "", "Color": "gray"}
            else:
                print(f"  'Close' column not found or empty for {name}. Setting to N/A.")
                commodity_data[name] = {"Price": "N/A", "Change": "N/A", "Triangle": "", "Color": "gray"}
        except Exception as e:
            print(f"Error fetching {name} data: {e}")
            commodity_data[name] = {"Price": "N/A", "Change": "N/A", "Triangle": "", "Color": "gray"}
    return commodity_data

def fetch_news_for_code(code):
    b = BSE()
    try:
        news_items = b.news(code)
        if isinstance(news_items, dict) and 'news' in news_items:
            return news_items['news']
    except Exception as e:
        print(f"Error fetching news for company code {code}: {e}")
    return []

def filter_and_deduplicate_news(news_items, similarity_threshold=0.8):
    """Filters news for the last month and removes duplicates."""
    today = datetime.now()
    last_month_date = today - timedelta(days=30)
    
    filtered_news = []
    print(f"\n--- Starting news filtering and deduplication ({len(news_items)} total items received) ---")
    
    for news in news_items:
        # --- CHANGE STARTS HERE ---
        # Change 'publisheddate' to 'post_date' as observed in the raw data
        date_str = news.get('post_date') 
        if date_str:
            try:
                # Change the format string to match 'YYYY-MM-DD HH:MM:SS'
                news_date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S') 
                # --- CHANGE ENDS HERE ---

                if last_month_date <= news_date <= today:
                    filtered_news.append(news)
                else:
                    print(f"  Skipped news (too old/future): '{news.get('post_title', 'No Title')}' - Date: {date_str}")
            except ValueError as e:
                print(f"  Date parsing error for news '{news.get('post_title', 'No Title')}' on date '{date_str}': {e}")
        else:
            print(f"  Skipped news (no 'post_date' or 'publisheddate'): '{news.get('post_title', 'No Title')}'") # Updated message

    print(f"  {len(filtered_news)} news items remaining after date filtering.")

    unique_news = []
    seen_titles = set()

    for news in filtered_news:
        title = news['post_title'] # Using 'post_title' as it's consistent in your raw data
        if title in seen_titles:
            print(f"  Skipped duplicate title (already seen): '{title}'")
            continue

        is_similar = False
        for unique_news_item in unique_news:
            existing_title = unique_news_item['post_title'] # Using 'post_title'
            similarity_ratio = difflib.SequenceMatcher(None, title, existing_title).ratio()
            if similarity_ratio > similarity_threshold:
                is_similar = True
                print(f"  Skipped similar title: '{title}' (similar to '{existing_title}' - {similarity_ratio:.2f})")
                break
        
        if not is_similar:
            unique_news.append(news)
            seen_titles.add(title)
            
    # --- CHANGE STARTS HERE ---
    # Also update the sort key to use 'post_date' and the new format
    unique_news.sort(key=lambda x: datetime.strptime(x['post_date'], '%Y-%m-%d %H:%M:%S'), reverse=True) 
    # --- CHANGE ENDS HERE ---
    
    print(f"  {len(unique_news)} unique news items after similarity filtering.")
    return unique_news


def get_latest_news():
    """Fetches and processes latest news."""
    all_news_data = []
    with ThreadPoolExecutor(max_workers=5) as executor: # Reduced max_workers for web
        futures = {executor.submit(fetch_news_for_code, code): code for code in BSE_COMPANY_CODES}
        for future in as_completed(futures):
            all_news_data.extend(future.result())
    
    return filter_and_deduplicate_news(all_news_data)

def get_stock_chart_data(ticker, period="1y"):
    """Fetches historical data for charting."""
    print(f"\n--- DEBUG: get_stock_chart_data Utility Function ---")
    print(f"  Fetching data for ticker: {ticker}, period: {period}")

    yf_period = ""
    yf_interval = ""

    if period == "1 Day":
        yf_period = "1d"
        yf_interval = "5m"

        # Try to fetch today's intraday data
        data = yf.download(ticker, period=yf_period, interval=yf_interval)
        
        if data.empty:
            print("  Today's intraday data is empty. Trying last market day...")

            # Fetch last 5 days of intraday data
            data_5d = yf.download(ticker, period="5d", interval="5m")

            if not data_5d.empty:
                # Normalize index to dates safely
                data_5d['date_only'] = pd.to_datetime(data_5d.index).date
                last_date = data_5d['date_only'][-1]
                print(f"  Last available intraday data date: {last_date}")

                # Filter only for the last available trading day
                data = data_5d[data_5d['date_only'] == last_date]

                if data.empty:
                    print("  Warning: No data found after filtering for last market day.")
            else:
                print("  No intraday data available for the last 5 days.")

    elif period == "1 Month":
        yf_period = "1mo"
        yf_interval = "1d"
        data = yf.download(ticker, period=yf_period, interval=yf_interval)
    elif period == "1 Year":
        yf_period = "1y"
        yf_interval = "1d"
        data = yf.download(ticker, period=yf_period, interval=yf_interval)
    else:
        yf_period = "1y"
        yf_interval = "1d"
        data = yf.download(ticker, period=yf_period, interval=yf_interval)

    print(f"  yfinance.download returned data.empty: {data.empty}")
    print(f"  Number of rows from yfinance: {len(data)}")

    if not data.empty:
        data_points = [
            [int(ts.timestamp() * 1000), float(row['Close'])]
            for ts, row in data.iterrows()
        ]
        
        last_price = data['Close'].iloc[-1].item()
        percent_change = 0.0

        if period == "1 Day":
            prev_day_data = yf.download(ticker, period="5d", interval="1d")
            if len(prev_day_data) >= 2:
                previous_close = prev_day_data['Close'].iloc[-2].item()
                if previous_close != 0:
                    percent_change = ((last_price - previous_close) / previous_close) * 100
                else:
                    print(f"  Warning: Previous close for {ticker} (1 Day) was 0. Percent change set to 0.")
            else:
                print(f"  Warning: Not enough data for {ticker} (1 Day) to calculate daily percent change.")
        else:
            if len(data) > 0 and 'Open' in data.columns:
                first_price = data['Open'].iloc[0].item()
                if first_price != 0:
                    percent_change = ((last_price - first_price) / first_price) * 100
                else:
                    print(f"  Warning: First price for {ticker} ({period}) was 0. Percent change set to 0.")
            else:
                print(f"  Warning: 'Open' column not found or not enough data for {ticker} ({period}). Percent change set to 0.")

        print(f"  Returning from get_stock_chart_data: len(data_points)={len(data_points)}, last_price={last_price:.2f}, percent_change={percent_change:.2f}")
        print("------------------------------------------")
        return data_points, last_price, percent_change

    print(f"  No data fetched from yfinance for {ticker}, {period}. Returning empty.")
    print("------------------------------------------")
    return [], 0.0, 0.0




# Example usage (if running as a script)
if __name__ == "__main__":
    print("--- Fetching Nifty and Sensex Data ---")
    index_data = get_nifty_sensex_data()
    print(index_data)

    print("\n--- Fetching Top Gainers and Losers ---")
    gainers, losers, gainer_name, gainer_ticker = get_top_gainers_losers()
    print(f"Top Gainers: {gainers}")
    print(f"Top Losers: {losers}")
    print(f"Gainer Name: {gainer_name}, Gainer Ticker: {gainer_ticker}")

    print("\n--- Fetching Commodity Data ---")
    commodity_results = fetch_commodity_data()
    # Print the raw data to confirm the 'Change (%)' values are numbers
    import json
    print("\nRaw Commodity Data:")
    print(json.dumps(commodity_results, indent=4))

    print("\n--- Simulating Display Output for Commodities ---")
    for name, data in commodity_results.items():
        price = data.get("Price", "N/A")
        change_percent = data.get("Change (%)", "N/A")
        triangle = data.get("Triangle", "")

        # This is how you'd format it for display in your application
        if isinstance(change_percent, (int, float)):
            formatted_change = f"{change_percent:.2f}%"
        else:
            formatted_change = f"{change_percent}" # Will be "N/A"

        print(f"{name}:")
        print(f"  {price}")
        print(f"  {triangle} {formatted_change}")