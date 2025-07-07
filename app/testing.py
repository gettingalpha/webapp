import yfinance as yf
from bselib.bse import BSE
from datetime import datetime, timedelta
import difflib
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings
import math
import json # Import json for pretty printing dictionary/list output

warnings.simplefilter(action='ignore', category=FutureWarning)

# ... (keep your existing COMPANY_TICKER_MAP and COMMODITY_TICKERS) ...

BSE_COMPANY_CODES = [544095, 543992] # Example codes - confirm these are valid and active for news

def fetch_news_for_code(code):
    b = BSE()
    try:
        print(f"\n--- Attempting to fetch news for BSE code: {code} ---")
        news_items = b.news(code)
        print(f"  Raw news response for {code}: {news_items}") # See what b.news(code) returns
        
        if isinstance(news_items, dict) and 'news' in news_items:
            print(f"  Found {len(news_items['news'])} news items in raw response for {code}.")
            return news_items['news']
        else:
            print(f"  No 'news' key or not a dict in response for {code}.")
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
        date_str = news.get('publisheddate')
        if date_str:
            try:
                news_date = datetime.strptime(date_str, '%d-%b-%Y %H:%M')
                if last_month_date <= news_date <= today:
                    filtered_news.append(news)
                else:
                    # Print if news is outside the date range
                    print(f"  Skipped news (too old/future): '{news.get('title', 'No Title')}' - Date: {date_str}")
            except ValueError as e:
                # Print parsing errors
                print(f"  Date parsing error for news '{news.get('title', 'No Title')}' on date '{date_str}': {e}")
        else:
            print(f"  Skipped news (no 'publisheddate'): '{news.get('title', 'No Title')}'")

    print(f"  {len(filtered_news)} news items remaining after date filtering.")

    unique_news = []
    seen_titles = set()

    for news in filtered_news:
        title = news['title']
        if title in seen_titles:
            print(f"  Skipped duplicate title (already seen): '{title}'")
            continue

        is_similar = False
        for unique_news_item in unique_news:
            existing_title = unique_news_item['title']
            similarity_ratio = difflib.SequenceMatcher(None, title, existing_title).ratio()
            if similarity_ratio > similarity_threshold:
                is_similar = True
                print(f"  Skipped similar title: '{title}' (similar to '{existing_title}' - {similarity_ratio:.2f})")
                break
        
        if not is_similar:
            unique_news.append(news)
            seen_titles.add(title)
            
    unique_news.sort(key=lambda x: datetime.strptime(x['publisheddate'], '%d-%b-%Y %H:%M'), reverse=True)
    print(f"  {len(unique_news)} unique news items after similarity filtering.")
    return unique_news

def get_latest_news():
    """Fetches and processes latest news."""
    all_news_data = []
    print("\n--- Starting get_latest_news ---")
    with ThreadPoolExecutor(max_workers=5) as executor: # Reduced max_workers for web
        futures = {executor.submit(fetch_news_for_code, code): code for code in BSE_COMPANY_CODES}
        for future in as_completed(futures):
            # Check if future.result() is not None or empty list
            result = future.result()
            if result:
                all_news_data.extend(result)
            else:
                print(f"  No news returned for code {futures[future]} from fetch_news_for_code.")
    
    print(f"  Total raw news items collected from all codes: {len(all_news_data)}")
    final_news = filter_and_deduplicate_news(all_news_data)
    print(f"--- Finished get_latest_news. Total news for display: {len(final_news)} ---")
    return final_news

# ... (rest of your code, including the if __name__ == "__main__": block) ...

# Ensure your __main__ block calls get_latest_news and prints its result:
if __name__ == "__main__":
    # ... (other sections) ...

    print("\n--- Fetching Latest News ---")
    news_items_result = get_latest_news()
    print("\nFinal Processed News Items (for display):")
    print(json.dumps(news_items_result, indent=2)) # Pretty print the final news list
    if not news_items_result:
        print("No news items available to display after processing.")