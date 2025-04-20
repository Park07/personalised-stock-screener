import re
from collections import Counter
import hashlib
from datetime import datetime, timedelta
import os
from urllib.request import urlopen, Request
import traceback
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from textblob import TextBlob
import nltk
import numpy as np
from wordcloud import WordCloud
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from bs4 import BeautifulSoup

# Try to import NLTK's VADER for sentiment analysis
try:
    vader = SentimentIntensityAnalyzer()
except BaseException:
    nltk.download('vader_lexicon')
    vader = SentimentIntensityAnalyzer()

# Download stopwords if not already downloaded
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

# FinViz URL for news scraping
web_url = "https://finviz.com/quote.ashx?t="


def analyse_stock_news(stock_code, days=28, output_dir='reports'):
    """
    Analyse news for a given stock and generate visualisations.

    Args:
        stock_code: Stock symbol (e.g., 'TSLA')
        days: Number of days of historical data to analyse
        output_dir: Directory to save reports and visualisations
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")

    if not re.match(r'^[A-Z]{1,5}$', stock_code):
        return {"error": "Invalid stock code format"}

    try:
        # Get news from Yahoo Finance
        ticker = yf.Ticker(stock_code)
        news_data = ticker.news

        if not news_data:
            print(f"No news found from Yahoo Finance for {stock_code}")
            news_data = []

        # Get news from FinViz as backup
        finviz_articles = get_finviz_news(stock_code, days)

        # Combine news from different sources
        all_articles = news_data + finviz_articles

        if not all_articles:
            return {"error": f"No news found for {stock_code}"}

        # Process news data
        articles = process_news_data(all_articles, stock_code)

        # Get stock price data
        stock_data = get_stock_price_data(ticker, days)

        # Calculate sentiment scores
        textblob_sentiment = calculate_overall_sentiment(articles)
        vader_sentiment = calculate_vader_sentiment(articles)

        # Generate visualisations if output directory exists
        image_paths = {}
        if os.path.exists(output_dir):
            try:
                # Create wordcloud
                wc_path = os.path.join(
                    output_dir, f'{stock_code}_wordcloud.png')
                wc_fig = generate_word_cloud(articles, stock_code)
                wc_fig.savefig(wc_path, bbox_inches='tight')
                plt.close(wc_fig)
                image_paths['wordCloud'] = wc_path
                print(f"Saved wordcloud to {wc_path}")

                # Create advanced sentiment visualisations (both with and
                # without neutral)
                sentiment_paths = generate_sentiment_visualisations(
                    articles, stock_code, output_dir)
                image_paths.update(sentiment_paths)
                print(f"Saved sentiment visualisations: {sentiment_paths}")
            except Exception as e:
                print(f"Error generating visualisations: {e}")

        # Create response
        return {
            "news": articles,
            "count": len(articles),
            "stockData": stock_data,
            "sentiment": {
                "textblob": textblob_sentiment,
                "vader": vader_sentiment
            },
            "keyThemes": extract_key_themes([a.get('summary', '') for a in articles]),
            "imagePaths": image_paths,
            "lastUpdated": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

    except Exception as e:
        print(traceback.format_exc())
        return {"error": f"Error analysing stock news: {str(e)}"}


def get_finviz_news(stock_code, days=28):
    """Get news from FinViz."""
    try:
        url = web_url + stock_code
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
                text = row.a.get_text() if row and row.a else "No Description"

                # Extract the URL
                link = row.a['href'] if row and row.a and 'href' in row.a.attrs else '#'

                date_scrape = row.td.text.split() if row and row.td else []

                try:
                    source = (row.div.span.get_text()
                            if row and row.div and row.div.span
                            else "FinViz")
                except BaseException:
                    source = "FinViz"

                if len(date_scrape) == 1:
                    time = date_scrape[0]
                    date = current_date if current_date else datetime.now().strftime("%b-%d-%y")
                else:
                    if len(date_scrape) > 0:
                        if date_scrape[0] == "Today":
                            date = datetime.now().strftime("%b-%d-%y")
                        else:
                            date = date_scrape[0]
                        time = date_scrape[1] if len(
                            date_scrape) > 1 else "00:00"
                        current_date = date
                    else:
                        continue  # Skip if no date information

                # Convert date string to datetime
                try:
                    article_date = datetime.strptime(date, "%b-%d-%y")
                    # Only include articles within the specified days
                    if (datetime.now() - article_date).days <= days:
                        # Create structure similar to Yahoo Finance
                        news_item = {
                            'title': text,
                            'summary': text,
                            'publishDate': article_date.isoformat() + 'Z',
                            'provider': {'displayName': source},
                            'url': link
                        }
                        news_list.append(news_item)
                except Exception as e:
                    print(f"Error parsing date: {e}")

            except Exception as e:
                print(f"Error parsing news item: {e}")
                continue

        return news_list
    except Exception as e:
        print(f"Error fetching FinViz news: {e}")
        return []


def process_news_data(news_data, stock_code):
    """Process and enhance news data with sentiment analysis."""
    articles = []

    for i, article in enumerate(news_data):
        article_data = extract_article_data(article)

        if not article_data.get('title') and not article_data.get('summary'):
            continue

        if 'publishDate' in article_data:
            try:
                dt = datetime.fromisoformat(
                    article_data['publishDate'].replace(
                        'Z', '+00:00'))
                article_data['formattedDate'] = dt.strftime(
                    '%Y-%m-%d %H:%M:%S')
                article_data['publishTimestamp'] = dt.timestamp()
            except (ValueError, TypeError):
                article_data['formattedDate'] = article_data['publishDate']
                article_data['publishTimestamp'] = (
                    datetime.now() - timedelta(days=i)).timestamp()

        article_data['id'] = generate_article_id(article_data)

        # TextBlob sentiment analysis
        article_data['sentiment'] = analyse_sentiment(
            f"{article_data.get('title', '')} {article_data.get('summary', '')}"
        )

        # VADER sentiment analysis
        article_data['vader_sentiment'] = analyse_vader_sentiment(
            f"{article_data.get('title', '')} {article_data.get('summary', '')}"
        )

        article_data['mentionsStock'] = mentions_stock(
            f"{article_data.get('title', '')} {article_data.get('summary', '')}",
            stock_code
        )

        article_data['keywords'] = extract_keywords(
            f"{article_data.get('title', '')} {article_data.get('summary', '')}"
        )

        articles.append(article_data)

    # Sort articles by date (newest first)
    articles.sort(key=lambda x: x.get('publishTimestamp', 0), reverse=True)
    return articles


def extract_article_data(article):
    """Extract basic article data from various possible structures."""
    article_data = {}

    if isinstance(article, dict):
        if 'content' in article and isinstance(article['content'], dict):
            content = article['content']
            article_data['title'] = content.get('title', '')
            article_data['summary'] = (
                content.get('summary', '') or
                content.get('description', '')
            )

            if 'pubDate' in content:
                article_data['publishDate'] = content['pubDate']

            if 'canonicalUrl' in content and isinstance(
                    content['canonicalUrl'], dict):
                article_data['url'] = content['canonicalUrl'].get('url', '')
            elif 'clickThroughUrl' in content and isinstance(content['clickThroughUrl'], dict):
                article_data['url'] = content['clickThroughUrl'].get('url', '')

            if 'provider' in content and isinstance(content['provider'], dict):
                article_data['source'] = content['provider'].get(
                    'displayName', '')
        else:
            article_data['title'] = article.get('title', '')
            article_data['summary'] = article.get(
                'summary', '') or article.get(
                'description', '')

            if 'pubDate' in article:
                article_data['publishDate'] = article['pubDate']
            elif 'publishDate' in article:
                article_data['publishDate'] = article['publishDate']

            if 'link' in article:
                article_data['url'] = article['link']
            elif 'url' in article:
                article_data['url'] = article['url']

            if 'provider' in article:
                if isinstance(article['provider'], dict):
                    article_data['source'] = article['provider'].get(
                        'displayName', '')
                else:
                    article_data['source'] = str(article['provider'])
    else:
        if hasattr(article, 'title'):
            article_data['title'] = article.title

        if hasattr(article, 'summary'):
            article_data['summary'] = article.summary
        elif hasattr(article, 'description'):
            article_data['summary'] = article.description

        if hasattr(article, 'pubDate'):
            article_data['publishDate'] = article.pubDate
        elif hasattr(article, 'publishDate'):
            article_data['publishDate'] = article.publishDate

        if hasattr(article, 'link'):
            article_data['url'] = article.link
        elif hasattr(article, 'url'):
            article_data['url'] = article.url

        if hasattr(article, 'provider'):
            article_data['source'] = article.provider

    return article_data


def analyse_sentiment(text):
    """Perform sentiment analysis using TextBlob."""
    if not text:
        return {"score": 0, "label": "neutral", "confidence": 0}

    analysis = TextBlob(text)

    polarity = analysis.sentiment.polarity
    if polarity > 0.1:
        label = "positive"
    elif polarity < -0.1:
        label = "negative"
    else:
        label = "neutral"

    confidence = abs(polarity) + (analysis.sentiment.subjectivity * 0.5)
    confidence = min(confidence, 1.0)

    return {
        "score": round(polarity, 2),
        "label": label,
        "confidence": round(confidence, 2)
    }


def analyse_vader_sentiment(text):
    """Perform sentiment analysis using NLTK's VADER."""
    if not text:
        return {"score": 0, "label": "neutral", "pos": 0, "neg": 0, "neu": 0}

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
            "pos": round(sentiment['pos'], 2),
            "neg": round(sentiment['neg'], 2),
            "neu": round(sentiment['neu'], 2)
        }
    except Exception as e:
        print(f"Error in VADER sentiment analysis: {e}")
        # Fallback to basic sentiment
        if "great" in text.lower() or "good" in text.lower() or "positive" in text.lower():
            return {
                "score": 0.5,
                "label": "positive",
                "pos": 0.5,
                "neg": 0,
                "neu": 0.5}
        if "bad" in text.lower() or "negative" in text.lower() or "poor" in text.lower():
            return {
                "score": -0.5,
                "label": "negative",
                "pos": 0,
                "neg": 0.5,
                "neu": 0.5}

        return {
            "score": 0,
            "label": "neutral",
            "pos": 0,
            "neg": 0,
            "neu": 1.0}


def extract_keywords(text, max_keywords=8):
    """Extract the most significant keywords from the text."""
    if not text:
        return []

    try:
        # Simple word splitting rather than using nltk.word_tokenize
        words = text.lower().split()

        # Clean up punctuation
        words = [word.strip('.,!?()[]{}":;') for word in words]

        # Filter out stopwords and short words
        try:
            stop_words = set(stopwords.words('english'))
        except BaseException:
            # Fallback stopwords if NLTK fails
            stop_words = {
                "the",
                "and",
                "a",
                "to",
                "of",
                "in",
                "is",
                "it",
                "that",
                "for",
                "on",
                "with",
                "as",
                "this",
                "by",
                "be",
                "are",
                "was",
                "were",
                "have",
                "has",
                "had",
                "an",
                "at",
                "but",
                "if",
                "or",
                "because"}

        words = [word for word in words if word.isalpha(
        ) and word not in stop_words and len(word) > 3]

        # Count word frequencies
        word_freq = Counter(words)

        # Return most common words
        return [word for word, _ in word_freq.most_common(max_keywords)]
    except Exception as e:
        print(f"Error extracting keywords: {e}")
        # Very simple fallback with hardcoded stopwords
        words = text.lower().split()
        common_words = {
            "the",
            "and",
            "a",
            "to",
            "of",
            "in",
            "is",
            "it",
            "that",
            "for"}
        words = [word for word in words if len(
            word) > 3 and word not in common_words]
        word_freq = Counter(words)
        return [word for word, _ in word_freq.most_common(max_keywords)]


def mentions_stock(text, stock_code):
    """Check if the article explicitly mentions the stock code."""
    if not text or not stock_code:
        return False

    return (stock_code.upper() in text.upper() or
            f"{stock_code.upper()} stock" in text.upper() or
            f"{stock_code.upper()}:" in text.upper())


def generate_article_id(article_data):
    """Generate a unique ID for the article based on its content."""
    if article_data.get('url'):
        source = article_data['url']
    else:
        source = (
            f"{article_data.get('title', '')}"
            f"{article_data.get('summary', '')}"
        )

    return hashlib.md5(source.encode()).hexdigest()


def get_stock_price_data(ticker, days=28):
    """Get recent stock price data."""
    try:
        # Get historical data for the specified number of days
        hist = ticker.history(period=f"{days}d")

        if hist.empty:
            return {}

        # Get latest price data
        latest = hist.iloc[-1]
        prev_day = hist.iloc[-2] if len(hist) > 1 else None

        # Calculate price change
        price_change = 0
        price_change_percent = 0

        if prev_day is not None:
            price_change = latest['Close'] - prev_day['Close']
            price_change_percent = (price_change / prev_day['Close']) * 100

        # Prepare chart data
        chart_data = []
        for date, row in hist.iterrows():
            chart_data.append({
                "date": date.strftime('%Y-%m-%d'),
                "close": round(row['Close'], 2),
                "volume": int(row['Volume']),
                "high": round(row['High'], 2),
                "low": round(row['Low'], 2)
            })

        return {
            "currentPrice": round(latest['Close'], 2),
            "priceChange": round(price_change, 2),
            "priceChangePercent": round(price_change_percent, 2),
            "volume": int(latest['Volume']),
            "high": round(latest['High'], 2),
            "low": round(latest['Low'], 2),
            "chartData": chart_data
        }
    except Exception as e:
        print(f"Error getting stock data: {e}")
        return {}


def calculate_overall_sentiment(articles):
    """Calculate the overall sentiment across all articles using TextBlob scores."""
    if not articles:
        return {
            "score": 0,
            "label": "neutral",
            "distribution": {
                "positive": 0,
                "neutral": 0,
                "negative": 0}}

    scores = [a['sentiment']['score'] for a in articles if 'sentiment' in a]

    if not scores:
        return {
            "score": 0,
            "label": "neutral",
            "distribution": {
                "positive": 0,
                "neutral": 0,
                "negative": 0}}

    avg_score = sum(scores) / len(scores)

    if avg_score > 0.1:
        label = "positive"
    elif avg_score < -0.1:
        label = "negative"
    else:
        label = "neutral"

    distribution = {
        "positive": len([s for s in scores if s > 0.1]),
        "neutral": len([s for s in scores if -0.1 <= s <= 0.1]),
        "negative": len([s for s in scores if s < -0.1])
    }

    return {
        "score": round(avg_score, 2),
        "label": label,
        "distribution": distribution
    }


def calculate_vader_sentiment(articles):
    """Calculate the overall sentiment across all articles using VADER scores."""
    if not articles:
        return {
            "score": 0,
            "label": "neutral",
            "distribution": {
                "positive": 0,
                "neutral": 0,
                "negative": 0}}

    scores = [a['vader_sentiment']['score']
              for a in articles if 'vader_sentiment' in a]

    if not scores:
        return {
            "score": 0,
            "label": "neutral",
            "distribution": {
                "positive": 0,
                "neutral": 0,
                "negative": 0}}

    avg_score = sum(scores) / len(scores)

    if avg_score > 0.05:
        label = "positive"
    elif avg_score < -0.05:
        label = "negative"
    else:
        label = "neutral"

    distribution = {
        "positive": len([s for s in scores if s > 0.05]),
        "neutral": len([s for s in scores if -0.05 <= s <= 0.05]),
        "negative": len([s for s in scores if s < -0.05])
    }

    return {
        "score": round(avg_score, 2),
        "label": label,
        "distribution": distribution
    }


def extract_key_themes(summaries, max_themes=5):
    """Extract key themes across all articles."""
    if not summaries:
        return []

    all_text = ' '.join(summaries)
    keywords = extract_keywords(all_text, max_themes * 3)
    themes = keywords[:max_themes]

    return themes


def plot_sentiment_distribution(articles, stock_code, exclude_neutral=False):
    # Create an advanced semi-circular sentiment visualisation

    # Count articles by sentiment (using VADER for better sentiment accuracy)
    sentiment_counts = {"Positive": 0, "Neutral": 0, "Negative": 0}

    for article in articles:
        if 'vader_sentiment' in article and 'label' in article['vader_sentiment']:
            label = article['vader_sentiment']['label'].lower()

            if label == 'positive':
                sentiment_counts["Positive"] += 1
            elif label == 'neutral':
                sentiment_counts["Neutral"] += 1
            elif label == 'negative':
                sentiment_counts["Negative"] += 1

    # Create figure
    total_count = sum(sentiment_counts.values())
    fig = Figure(figsize=(10, 6))
    ax = fig.add_subplot(111, projection='polar')

    # Define color spectrum
    colour_spectrum = {
        "Positive": "#4CAF50",
        "Neutral": "#9E9E9E",
        "Negative": "#F44336"}

    if exclude_neutral:
        # Calculate without neutral sentiment
        non_neutral_count = sentiment_counts["Positive"] + \
            sentiment_counts["Negative"]

        if non_neutral_count == 0:  # Handle case with no non-neutral data
            positive = 50  # Default to 50-50 split if no data
            negative = 50
        else:
            positive = round(
                (sentiment_counts["Positive"] / non_neutral_count * 100), 1)
            negative = round(
                (sentiment_counts["Negative"] / non_neutral_count * 100), 1)

        # Create semicircle
        pos_end = np.pi * (positive / 100)

        # Fill sections
        ax.fill_between(
            np.linspace(
                0,
                pos_end,
                50),
            0.7,
            0.9,
            color=colour_spectrum["Positive"],
            alpha=0.8)
        ax.fill_between(
            np.linspace(
                pos_end,
                np.pi,
                50),
            0.7,
            0.9,
            color=colour_spectrum["Negative"],
            alpha=0.8)

        p_label = f"Positive: {positive}% ({sentiment_counts['Positive']})"
        n_label = f"Negative: {negative}% ({sentiment_counts['Negative']})"

        ax.text(pos_end / 2, 1.0, p_label, ha='center', va='center',
                bbox={"facecolor": '#E8F5E9', "alpha": 0.8, "boxstyle": 'round'})

        ax.text((pos_end + np.pi) / 2, 1.0, n_label, ha='center', va='center',
                bbox={"facecolor": '#FFEBEE', "alpha": 0.8, "boxstyle": 'round'})
    else:
        # Include neutral sentiment
        if total_count == 0:
            percentages = {
                "Positive": 33.3,
                "Neutral": 33.3,
                "Negative": 33.3}  # Default even split
        else:
            percentages = {s: round((c / total_count * 100), 1)
                           for s, c in sentiment_counts.items()}

        pos_end = np.pi * (percentages["Positive"] / 100)
        neu_end = pos_end + np.pi * (percentages["Neutral"] / 100)

        # Draw sections
        ax.fill_between(
            np.linspace(
                0,
                pos_end,
                50),
            0.7,
            0.9,
            color=colour_spectrum["Positive"],
            alpha=0.8)
        ax.fill_between(
            np.linspace(
                pos_end,
                neu_end,
                50),
            0.7,
            0.9,
            color=colour_spectrum["Neutral"],
            alpha=0.8)
        ax.fill_between(
            np.linspace(
                neu_end,
                np.pi,
                50),
            0.7,
            0.9,
            color=colour_spectrum["Negative"],
            alpha=0.8)

        positive_label = f"Positive: {
            percentages['Positive']}% ({
            sentiment_counts['Positive']})"
        neutral_label = f"Neutral: {
            percentages['Neutral']}% ({
            sentiment_counts['Neutral']})"
        negative_label = f"Negative: {
            percentages['Negative']}% ({
            sentiment_counts['Negative']})"

        ax.text(pos_end / 2, 1.0, positive_label, ha='center', va='center',
            bbox={"facecolor": '#E8F5E9', "alpha": 0.8, "boxstyle": 'round'})
        ax.text(
            (pos_end + neu_end) / 2,
            1.0,
            neutral_label,
            ha='center',
            va='center',
            bbox={"facecolor": '#F5F5F5', "alpha": 0.8, "boxstyle": 'round'}
            )
        ax.text(
            (neu_end + np.pi) / 2,
            1.0,
            negative_label,
            ha='center',
            va='center',
            bbox={"facecolor": '#FFEBEE', "alpha": 0.8, "boxstyle": 'round'}
            )


    # Configure the plot
    ax.set_thetamin(0)
    ax.set_thetamax(180)
    ax.grid(False)
    ax.set_xticklabels([])
    ax.set_yticklabels([])

    # Set title with company name
    ax.set_title(
        f'Sentiment Distribution for {stock_code}',
        fontsize=18,
        pad=20)

    # Add toggle indicator text
    toggle_status = "Exclude neutral: ON" if exclude_neutral else "Include neutral: ON"
    fig.text(0.15, 0.15, toggle_status, fontsize=12)

    # Add a note about which sentiment analyser is used
    fig.text(
        0.15,
        0.10,
        "Using VADER Sentiment Analysis",
        fontsize=10,
        style='italic')

    plt.tight_layout()
    return fig


def generate_sentiment_visualisations(articles, stock_code, output_dir):
    # Generate both versions of the sentiment visualisation (with and without
    # neutral)

    image_paths = {}

    # Generate visualisation with neutral sentiment
    with_neutral_path = os.path.join(
        output_dir, f'{stock_code}_sentiment_with_neutral.png')
    with_neutral_fig = plot_sentiment_distribution(
        articles, stock_code, exclude_neutral=False)
    with_neutral_fig.savefig(with_neutral_path, bbox_inches='tight')
    plt.close(with_neutral_fig)
    image_paths['sentimentWithNeutral'] = with_neutral_path

    # Generate visualisation without neutral sentiment
    without_neutral_path = os.path.join(
        output_dir, f'{stock_code}_sentiment_without_neutral.png')
    without_neutral_fig = plot_sentiment_distribution(
        articles, stock_code, exclude_neutral=True)
    without_neutral_fig.savefig(without_neutral_path, bbox_inches='tight')
    plt.close(without_neutral_fig)
    image_paths['sentimentWithoutNeutral'] = without_neutral_path

    return image_paths


def generate_word_cloud(articles, stock_code):
    """Generate a word cloud from article keywords and summaries."""
    all_text = ' '.join([article.get('summary', '')
                        for article in articles if article.get('summary')])

    keywords = []
    for article in articles:
        if 'keywords' in article:
            keywords.extend(article['keywords'])

    if stock_code:
        keywords.extend([stock_code] * 5)

    keyword_text = ' '.join(keywords)
    combined_text = f"{all_text} {keyword_text} {keyword_text}"

    if not combined_text.strip():
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(
            0.5,
            0.5,
            'No text data available for word cloud',
            horizontalalignment='center',
            verticalalignment='center',
            transform=ax.transAxes)
        return fig

    wordcloud = WordCloud(
        width=800,
        height=400,
        background_color='white',
        max_words=100,
        colormap='viridis',
        contour_width=1,
        contour_color='steelblue'
    ).generate(combined_text)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.set_title(f'Key Topics in {stock_code} News')
    ax.axis('off')

    plt.tight_layout()
    return fig
