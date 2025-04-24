"""
Sentiment analysis module for stock news from multiple sources.
"""
import io
import base64
import re
import requests
import traceback
import matplotlib.pyplot as plt
import numpy as np
import logging
from datetime import datetime, timedelta
import hashlib
from urllib.request import urlopen, Request
from collections import Counter
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk
import yfinance as yf
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    vader = SentimentIntensityAnalyzer()
except BaseException:
    nltk.download('vader_lexicon')
    vader = SentimentIntensityAnalyzer()

# External team's API
NEWS_API_URL = "http://api-financeprodlb-421072170.ap-southeast-2.elb.amazonaws.com/fetch/news"
TEAM_KEY = "cac095a75271701015134566cb2e312f8c211019e6f366f7242cd659a4adcae6"

FIXED_API_KEY = "a1b2c3d4e5f6g7h8i9j0"

# FinViz URL for news scraping
FINVIZ_URL = "https://finviz.com/quote.ashx?t="


def get_api_team_news(ticker):
    """Get news from the external team's API."""
    try:
        response = requests.get(
            NEWS_API_URL,
            params={"stockCode": ticker},
            headers={"api-key": FIXED_API_KEY}
        )

        if response.status_code != 200:
            logger.error(f"Error fetching news from API: {response.status_code}")
            return []

        data = response.json()
        news_articles = data.get("news", [])

        processed_articles = []
        for i, article_text in enumerate(news_articles):
            article = {
                "id": f"api-{ticker}-{i}",
                "title": article_text[:100] + "..." if len(article_text) > 100 else article_text,
                "summary": article_text,
                "url": "#",
                "publishDate": datetime.now().isoformat(),
                "source": "API Team News"
            }
            processed_articles.append(article)

        logger.info(f"Fetched {len(processed_articles)} articles from API")
        return processed_articles

    except Exception as e:
        logger.error(f"Error fetching API news: {str(e)}")
        return []


def get_yahoo_news(ticker):
    """Get news from Yahoo Finance."""
    try:
        ticker_obj = yf.Ticker(ticker)
        news_data = ticker_obj.news or []

        processed_articles = []
        for article in news_data:
            article_data = {}

            # Extract basic data
            article_data['title'] = article.get('title', '')
            article_data['summary'] = article.get('summary', '')
            article_data['url'] = article.get('link', '')
            article_data['source'] = "Yahoo Finance"

            # Parse date
            if 'providerPublishTime' in article:
                try:
                    dt = datetime.fromtimestamp(article['providerPublishTime'])
                    article_data['publishDate'] = dt.isoformat()
                except BaseException:
                    article_data['publishDate'] = datetime.now().isoformat()
            else:
                article_data['publishDate'] = datetime.now().isoformat()

            # Generate ID
            article_data['id'] = f"yahoo-{hashlib.md5(
                article_data['url'].encode()).hexdigest()}"

            processed_articles.append(article_data)

        logger.info(f"Fetched {len(processed_articles)} articles from Yahoo")
        return processed_articles

    except Exception as e:
        logger.error(f"Error fetching Yahoo news: {str(e)}")
        return []


def get_finviz_news(ticker, days=14):
    """Get news from FinViz."""
    try:
        url = FINVIZ_URL + ticker
        req = Request(url=url, headers={"User-Agent": "Mozilla/5.0"})
        response = urlopen(req)
        html = BeautifulSoup(response, "html.parser")
        news_table = html.find(id="news-table")

        if not news_table:
            return []

        news_list = []
        current_date = None

        for row in news_table.findAll("tr"):
            try:
                # Extract title and URL
                text = row.a.get_text() if row and row.a else "No Description"
                link = row.a['href'] if row and row.a and 'href' in row.a.attrs else '#'

                # Extract date and source
                date_scrape = row.td.text.split() if row and row.td else []

                try:
                    source = row.div.span.get_text() if row and row.div and row.div.span else "FinViz"
                except BaseException:
                    source = "FinViz"

                # Process date information
                if len(date_scrape) == 1:
                    time = date_scrape[0]
                    date = current_date or datetime.now().strftime("%b-%d-%y")
                else:
                    if date_scrape:
                        if date_scrape[0] == "Today":
                            date = datetime.now().strftime("%b-%d-%y")
                        else:
                            date = date_scrape[0]
                        time = date_scrape[1] if len(
                            date_scrape) > 1 else "00:00"
                        current_date = date
                    else:
                        continue

                # Convert to datetime
                try:
                    article_date = datetime.strptime(date, "%b-%d-%y")
                    if (datetime.now() - article_date).days <= days:
                        article_data = {
                            'id': f"finviz-{hashlib.md5(link.encode()).hexdigest()}",
                            'title': text,
                            'summary': text,
                            'url': link,
                            'publishDate': article_date.isoformat(),
                            'source': source
                        }
                        news_list.append(article_data)
                except Exception as e:
                    logger.error(f"Error parsing date: {e}")

            except Exception as e:
                logger.error(f"Error parsing news item: {e}")

        logger.info(f"Fetched {len(news_list)} articles from FinViz")
        return news_list

    except Exception as e:
        logger.error(f"Error fetching FinViz news: {str(e)}")
        return []


def analyse_sentiment(text):
    """Analyse sentiment using VADER."""
    if not text:
        return {"score": 0, "label": "neutral", "confidence": 0}

    try:
        sentiment = vader.polarity_scores(text)
        compound = sentiment['compound']

        if compound > 0.05:
            label = "positive"
        elif compound < -0.05:
            label = "negative"
        else:
            label = "neutral"

        return {
            "score": round(compound, 2),
            "label": label,
            "distribution": {
                "positive": sentiment['pos'],
                "neutral": sentiment['neu'],
                "negative": sentiment['neg']
            }
        }
    except Exception as e:
        logger.error(f"Error analysing sentiment: {str(e)}")
        return {"score": 0, "label": "neutral", "confidence": 0}


def combine_and_process_news(ticker):
    """Combine news from all sources and process with sentiment analysis."""

    # 1. Get news from all three sources
    api_news = get_api_team_news(ticker)
    yahoo_news = get_yahoo_news(ticker)
    finviz_news = get_finviz_news(ticker)

    # 2. Combine all news
    all_news = api_news + yahoo_news + finviz_news

    # 3. Remove duplicates based on title similarity
    unique_news = []
    titles = set()

    for article in all_news:
        # Clean title for comparison
        clean_title = re.sub(
            r'[^a-zA-Z0-9\s]',
            '',
            article.get(
                'title',
                '')).lower()

        # Skip if very similar title exists
        if clean_title and clean_title not in titles:
            titles.add(clean_title)

            # Add sentiment analysis
            text = f"{article.get('title', '')} {article.get('summary', '')}"
            article['sentiment'] = analyse_sentiment(text)

            unique_news.append(article)

    # 4. Sort by date (newest first)
    try:
        unique_news.sort(key=lambda x: x.get('publishDate', ''), reverse=True)
    except BaseException:
        pass

    logger.info(
        f"Combined {
            len(unique_news)} unique articles from all sources")
    return unique_news


def calculate_overall_sentiment(articles):
    """Calculate overall sentiment across all articles."""
    if not articles:
        return {
            "score": 0,
            "label": "neutral",
            "distribution": {
                "positive": 0,
                "neutral": 0,
                "negative": 0
            }
        }

    sentiment_counts = {"positive": 0, "neutral": 0, "negative": 0}
    scores = []

    for article in articles:
        if "sentiment" in article and "label" in article["sentiment"]:
            label = article["sentiment"]["label"]
            sentiment_counts[label] += 1

        if "sentiment" in article and "score" in article["sentiment"]:
            scores.append(article["sentiment"]["score"])

    avg_score = sum(scores) / len(scores) if scores else 0

    if avg_score > 0.05:
        label = "positive"
    elif avg_score < -0.05:
        label = "negative"
    else:
        label = "neutral"

    return {
        "score": round(avg_score, 2),
        "label": label,
        "distribution": sentiment_counts
    }

    

def generate_sentiment_chart(sentiment_data, ticker):
    """Generate chart visualizing sentiment distribution as a semi-circular gauge."""
    try:
        distribution = sentiment_data.get("distribution", {})
        sentiment_counts = {
            "Positive": distribution.get("positive", 0),
            "Neutral": distribution.get("neutral", 0),
            "Negative": distribution.get("negative", 0)
        }

        total = sum(sentiment_counts.values())
        if total == 0:
            percentages = {"Positive": 33.3, "Neutral": 33.3, "Negative": 29.1}
        else:
            percentages = {k: (v / total * 100)
                           for k, v in sentiment_counts.items()}

        # Create figure with polar projection for semi-circle
        fig, ax = plt.subplots(
            figsize=(
                10, 6), subplot_kw=dict(
                projection='polar'))

        # Define colors
        colors = {
            "Positive": "#4CAF50",
            "Neutral": "#9E9E9E",
            "Negative": "#F44336"}

        # Calculate angles for each sentiment section
        pos_pct = percentages["Positive"] / 100
        neu_pct = percentages["Neutral"] / 100
        neg_pct = percentages["Negative"] / 100

        pos_end = np.pi * pos_pct
        neu_end = pos_end + (np.pi * neu_pct)
        # neg_end will be pi (end of semi-circle)

        # Draw the sections
        ax.fill_between(
            np.linspace(
                0,
                pos_end,
                50),
            0.7,
            0.9,
            color=colors["Positive"],
            alpha=0.8)
        ax.fill_between(
            np.linspace(
                pos_end,
                neu_end,
                50),
            0.7,
            0.9,
            color=colors["Neutral"],
            alpha=0.8)
        ax.fill_between(
            np.linspace(
                neu_end,
                np.pi,
                50),
            0.7,
            0.9,
            color=colors["Negative"],
            alpha=0.8)

        # Add labels
        pos_label = f"Positive: {
            percentages['Positive']:.1f}% ({
            sentiment_counts['Positive']})"
        neu_label = f"Neutral: {
            percentages['Neutral']:.1f}% ({
            sentiment_counts['Neutral']})"
        neg_label = f"Negative: {
            percentages['Negative']:.1f}% ({
            sentiment_counts['Negative']})"

        ax.text(
            pos_end / 2,
            1.0,
            pos_label,
            ha='center',
            va='center',
            bbox={
                "facecolor": '#E8F5E9',
                "alpha": 0.8,
                "boxstyle": 'round'})
        ax.text(
            (pos_end + neu_end) / 2,
            1.0,
            neu_label,
            ha='center',
            va='center',
            bbox={
                "facecolor": '#F5F5F5',
                "alpha": 0.8,
                "boxstyle": 'round'})
        ax.text(
            (neu_end + np.pi) / 2,
            1.0,
            neg_label,
            ha='center',
            va='center',
            bbox={
                "facecolor": '#FFEBEE',
                "alpha": 0.8,
                "boxstyle": 'round'})

        # Configure the plot
        ax.set_thetamin(0)
        ax.set_thetamax(180)
        ax.grid(False)
        ax.set_xticklabels([])
        ax.set_yticklabels([])

        # Set title with company name
        ax.set_title(f'Sentiment Distribution for {
                     ticker}', fontsize=18, pad=20)

        # Convert to base64 image
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight', dpi=100)
        buffer.seek(0)

        image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        plt.close(fig)

        return f"data:image/png;base64,{image_base64}"

    except Exception as e:
        logger.error(f"Error generating sentiment chart: {str(e)}")
        logger.error(traceback.format_exc())
        return ""

        return f"data:image/png;base64,{image_base64}"

def get_stock_sentiment(ticker):
    """Get sentiment analysis for a stock from multiple news sources."""
    try:
        # Get and process news from all sources
        articles = combine_and_process_news(ticker)

        if not articles:
            return {"error": f"No news found for {ticker}"}

        # Get sentiment analysis
        overall_sentiment = calculate_overall_sentiment(articles)
        chart_image = generate_sentiment_chart(overall_sentiment, ticker)

        # For display, limit to top 20 articles
        display_articles = articles[:20]

        # Count articles by source
        sources = Counter([a.get('source', 'Unknown') for a in articles])
        source_breakdown = {source: count for source, count in sources.items()}

        return {
            "ticker": ticker,
            "articles": display_articles,
            "articleCount": len(articles),
            "sentiment": overall_sentiment,
            "chart": chart_image,
            "sources": source_breakdown,
            "lastUpdated": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting stock sentiment: {str(e)}")
        logger.error(traceback.format_exc())
        return {"error": f"Error analysing sentiment: {str(e)}"}
