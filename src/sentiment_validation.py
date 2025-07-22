"""
Tests sentiment against price movements immediately following a specific news event.
"""

import yfinance as yf
from datetime import datetime, timedelta
import sys
import os

# Add the parent directory to the path to find the 'src' module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# --- Import sentiment analysis function ---
# This will attempt to import your actual sentiment module.
# If it fails, it uses a placeholder for demonstration purposes.
try:
    from src.sentiment import get_stock_sentiment
except ImportError:
    print("WARNING: Could not import 'get_stock_sentiment'. Using a placeholder function.")
    # Placeholder function in case the real one isn't found
    def get_stock_sentiment(ticker):
        # Return a generic positive sentiment for the example
        return {"sentiment": {"label": "positive", "score": 0.25}, "articleCount": 99}

def get_price_change_for_event(ticker, event_date_str, analysis_days=2):
    """
    Get stock price change for a number of days following a specific event date.

    This function finds the closing price on the event day (or the next trading day if it's a holiday/weekend)
    and compares it to the closing price 'analysis_days' trading days later.
    """
    try:
        event_date = datetime.strptime(event_date_str, "%Y-%m-%d")

        # Fetch data for a window starting from the event date
        # yfinance `end` is exclusive, so add one day to include the target end date
        # Fetch a bit more data to handle weekends/holidays gracefully
        data_window_start = event_date
        data_window_end = event_date + timedelta(days=analysis_days + 7)

        stock_data = yf.Ticker(ticker).history(
            start=data_window_start,
            end=data_window_end
        )

        if stock_data.empty:
            print(f"No data found for {ticker} around {event_date_str}")
            return None

        # The first available data point on or after the event date is our start price
        start_price_row = stock_data.iloc[0]
        actual_start_date = start_price_row.name.strftime('%Y-%m-%d')
        start_price = start_price_row['Close']

        # The data point 'analysis_days' after our actual start is the end price
        if len(stock_data) <= analysis_days:
            print(f"Not enough trading days of data after {actual_start_date} to perform analysis.")
            return None

        end_price_row = stock_data.iloc[analysis_days]
        actual_end_date = end_price_row.name.strftime('%Y-%m-%d')
        end_price = end_price_row['Close']

        price_change = ((end_price - start_price) / start_price) * 100

        print(f"Price analysis for {ticker}:")
        print(f"  Start Date: {actual_start_date}, Price: ${start_price:.2f}")
        print(f"  End Date:   {actual_end_date}, Price: ${end_price:.2f}")

        return {
            "start_price": start_price,
            "end_price": end_price,
            "change_percent": price_change
        }
    except Exception as e:
        print(f"An error occurred getting price data for {ticker}: {e}")
        return None

def validate_news_event(ticker, event_description, event_date):
    """
    Validates sentiment against price movement immediately following a specific news event.
    """
    print(f"\n▶️  Validating Event: '{event_description}' for {ticker}")
    print("-" * 70)

    # 1. Get sentiment from news around that period.
    #    Your get_stock_sentiment function looks back 14 days, which is perfect.
    sentiment_data = get_stock_sentiment(ticker)
    if "error" in sentiment_data:
        print(f"Error getting sentiment: {sentiment_data['error']}")
        return None

    sentiment_score = sentiment_data.get("sentiment", {}).get("score", 0)
    article_count = sentiment_data.get("articleCount", 0)

    # 2. Get price change for the 2 trading days immediately FOLLOWING the event.
    price_data = get_price_change_for_event(ticker, event_date, analysis_days=2)
    if not price_data:
        return None

    price_change = price_data["change_percent"]

    # 3. Check for correlation with realistic thresholds.
    sentiment_positive = sentiment_score > 0.1
    sentiment_negative = sentiment_score < -0.1
    price_positive = price_change > 1.0  # A >1% move in 2 days is a reasonable signal
    price_negative = price_change < -1.0

    correlation = "none"
    if (sentiment_positive and price_positive) or (sentiment_negative and price_negative):
        correlation = "strong"
    elif (sentiment_positive and price_negative) or (sentiment_negative and price_positive):
        correlation = "inverse"

    # 4. Print results for this event.
    print(f"\nAnalysis Results for {ticker}:")
    print(f"  Sentiment Score: {sentiment_score:.2f} (from {article_count} articles)")
    print(f"  Price Change (+2 trading days): {price_change:.2f}%")
    print(f"  Correlation: {correlation.upper()}")

    result = {
        "ticker": ticker,
        "correlation": correlation
    }

    if correlation == "strong":
        print("  Result: VALIDATED - Sentiment direction matches post-event price movement.")
    elif correlation == "inverse":
        print(" Result: INVERSE - Sentiment is opposite to price movement.")
    else:
        print("  ➖ Result: NEUTRAL - No clear correlation observed.")

    return result


def run_full_validation():
    """
    Runs the event-driven validation for a list of predefined test cases.
    """
    print("\n==================================================")
    print("  Event-Driven Sentiment Analysis Validation")
    print("==================================================")
    print("Testing if market reaction aligns with news sentiment after key events.")

    # Define the specific news events and their dates to test
    test_cases = [
        {
            "ticker": "NVDA",
            "description": "NVIDIA - Export ban lifted, allowed to resume H20 chip sales",
            "date": "2025-07-15"
        },
        {
            "ticker": "MP",
            "description": "MP Materials - $500M partnership with Apple for recycled rare earths",
            "date": "2025-07-15"
        }
    ]

    results = []
    for event in test_cases:
        result = validate_news_event(event["ticker"], event["description"], event["date"])
        if result:
            results.append(result)

    # --- Final Summary ---
    validated_count = sum(1 for r in results if r.get("correlation") == "strong")
    total_tests = len(results)

    print("\n\n===================================")
    print("  Validation Summary")
    print("-----------------------------------")
    print(f"Total tests run: {total_tests}")
    print(f"Strong correlations found: {validated_count}")

    if total_tests > 0:
        accuracy = (validated_count / total_tests) * 100
        print(f"Success Rate: {accuracy:.0f}%")
        if accuracy >= 50:
            print("Status: GOOD CORRELATION")
        else:
            print("Status: NEEDS IMPROVEMENT")
    print("===================================")


if __name__ == "__main__":
    run_full_validation()