import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from textblob import TextBlob
import re
import nltk
from nltk.corpus import stopwords
from collections import Counter
import hashlib
from datetime import datetime, timedelta
import os
import numpy as np
from wordcloud import WordCloud
nltk.download('punkt')
nltk.download('stopwords')

def analyse_stock_news(stock_code, output_dir='reports'):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    if not re.match(r'^[A-Z]{1,5}$', stock_code):
        return {"error": "Invalid stock code format"}
    
    try:
        ticker = yf.Ticker(stock_code)
        news_data = ticker.news
        
        if not news_data:
            return {"error": f"No news found for {stock_code}"}
        
        articles = process_news_data(news_data, stock_code)
        stock_data = get_stock_price_data(ticker)
        image_paths = generate_visualisations(articles, stock_data, stock_code, output_dir)
        report_path = generate_text_report(articles, stock_data, stock_code, output_dir)
        
        return {
            "articleCount": len(articles),
            "sentimentSummary": calculate_overall_sentiment(articles),
            "keyThemes": extract_key_themes([a.get('summary', '') for a in articles]),
            "reportPath": report_path,
            "imagePaths": image_paths,
            "lastUpdated": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return {"error": f"Error analysing stock news: {str(e)}"}


def process_news_data(news_data, stock_code):
    articles = []
    
    for i, article in enumerate(news_data):
        article_data = extract_article_data(article)
        
        if not article_data.get('title') and not article_data.get('summary'):
            continue
            
        if 'publishDate' in article_data:
            try:
                dt = datetime.fromisoformat(article_data['publishDate'].replace('Z', '+00:00'))
                article_data['formattedDate'] = dt.strftime('%Y-%m-%d %H:%M:%S')
                article_data['publishTimestamp'] = dt.timestamp()
            except (ValueError, TypeError):
                article_data['formattedDate'] = article_data['publishDate']
                article_data['publishTimestamp'] = (datetime.now() - timedelta(days=i)).timestamp()
        
        article_data['id'] = generate_article_id(article_data)
        article_data['sentiment'] = analyse_sentiment(
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
    
    articles.sort(key=lambda x: x.get('publishTimestamp', 0), reverse=True)
    return articles


def extract_article_data(article):
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
            
            if 'canonicalUrl' in content and isinstance(content['canonicalUrl'], dict):
                article_data['url'] = content['canonicalUrl'].get('url', '')
            elif 'clickThroughUrl' in content and isinstance(content['clickThroughUrl'], dict):
                article_data['url'] = content['clickThroughUrl'].get('url', '')
                
            if 'provider' in content and isinstance(content['provider'], dict):
                article_data['source'] = content['provider'].get('displayName', '')
        else:
            article_data['title'] = article.get('title', '')
            article_data['summary'] = article.get('summary', '') or article.get('description', '')
            
            if 'pubDate' in article:
                article_data['publishDate'] = article['pubDate']
            
            if 'link' in article:
                article_data['url'] = article['link']
            elif 'url' in article:
                article_data['url'] = article['url']
                
            if 'provider' in article:
                if isinstance(article['provider'], dict):
                    article_data['source'] = article['provider'].get('displayName', '')
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
        
        if hasattr(article, 'link'):
            article_data['url'] = article.link
    
    return article_data


def analyse_sentiment(text):
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


def extract_keywords(text, max_keywords=8):
    if not text:
        return []
    
    try:
        words = text.lower().split()
        words = [word.strip('.,!?()[]{}":;') for word in words]
        
        # Filter out stopwords and short words
        try:
            stop_words = set(stopwords.words('english'))
        except:
            # Fallback stopwords if NLTK fails
            stop_words = {"the", "and", "a", "to", "of", "in", "is", "it", "that", "for", 
                          "on", "with", "as", "this", "by", "be", "are", "was", "were", 
                          "have", "has", "had", "an", "at", "but", "if", "or", "because",
                          "from", "when", "where", "which", "who", "will", "would", "could",
                          "should", "what", "how", "all", "any", "both", "each", "more", 
                          "other", "some", "such", "no", "not", "only", "own", "same", 
                          "than", "too", "very"}
        
        words = [word for word in words if word.isalpha() and word not in stop_words and len(word) > 3]
        
        # Count word frequencies
        word_freq = Counter(words)
        
        # Return most common words
        return [word for word, _ in word_freq.most_common(max_keywords)]
    except Exception as e:
        print(f"Error extracting keywords: {e}")
        # Very simple fallback with hardcoded stopwords
        words = text.lower().split()
        common_words = {"the", "and", "a", "to", "of", "in", "is", "it", "that", "for"}
        words = [word for word in words if len(word) > 3 and word not in common_words]
        word_freq = Counter(words)
        return [word for word, _ in word_freq.most_common(max_keywords)]

def mentions_stock(text, stock_code):
    if not text or not stock_code:
        return False
    
    return (stock_code.upper() in text.upper() or 
            f"{stock_code.upper()} stock" in text.upper() or
            f"{stock_code.upper()}:" in text.upper())


def generate_article_id(article_data):
    if article_data.get('url'):
        source = article_data['url']
    else:
        source = f"{article_data.get('title', '')}{article_data.get('summary', '')}"
    
    return hashlib.md5(source.encode()).hexdigest()


def get_stock_price_data(ticker):
    try:
        hist = ticker.history(period="30d")
        
        if hist.empty:
            return {}
        
        latest = hist.iloc[-1]
        prev_day = hist.iloc[-2] if len(hist) > 1 else None
        
        price_change = 0
        price_change_percent = 0
        
        if prev_day is not None:
            price_change = latest['Close'] - prev_day['Close']
            price_change_percent = (price_change / prev_day['Close']) * 100
        
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
    if not articles:
        return {"score": 0, "label": "neutral", "distribution": {"positive": 0, "neutral": 0, "negative": 0}}
    
    scores = [a['sentiment']['score'] for a in articles if 'sentiment' in a]
    
    if not scores:
        return {"score": 0, "label": "neutral", "distribution": {"positive": 0, "neutral": 0, "negative": 0}}
    
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


def extract_key_themes(summaries, max_themes=5):
    if not summaries:
        return []
    
    all_text = ' '.join(summaries)
    keywords = extract_keywords(all_text, max_themes * 3)
    themes = keywords[:max_themes]
    
    return themes


def generate_visualisations(articles, stock_data, stock_code, output_dir):
    image_paths = {}
    
    sentiment_path = os.path.join(output_dir, f'{stock_code}_sentiment_timeline.png')
    sentiment_fig = plot_sentiment_timeline(articles)
    sentiment_fig.savefig(sentiment_path, bbox_inches='tight')
    plt.close(sentiment_fig)
    image_paths['sentimentTimeline'] = sentiment_path
    
    
    sentiment_dist_path = os.path.join(output_dir, f'{stock_code}_sentiment_distribution.png')
    sentiment_dist_fig = plot_sentiment_distribution(articles, stock_code)  # Passing stock_code now
    sentiment_dist_fig.savefig(sentiment_dist_path, bbox_inches='tight', dpi=120)  # Higher DPI for better quality
    plt.close(sentiment_dist_fig)
    image_paths['sentimentDistribution'] = sentiment_dist_path
    
    wordcloud_path = os.path.join(output_dir, f'{stock_code}_word_cloud.png')
    wc_fig = generate_word_cloud(articles, stock_code)
    wc_fig.savefig(wordcloud_path, bbox_inches='tight')
    plt.close(wc_fig)
    image_paths['wordCloud'] = wordcloud_path
    
    return image_paths


def plot_sentiment_timeline(articles):
    """
    Plot the sentiment timeline for articles.
    
    Args:
        articles (list): List of article dictionaries containing sentiment and date information
        
    Returns:
        matplotlib.figure.Figure: Figure object containing the visualization
    """
    # Sort articles by timestamp
    sorted_articles = sorted(articles, key=lambda x: x.get('publishTimestamp', 0))
    
    # Extract dates and scores
    dates = []
    scores = []
    
    for article in sorted_articles:
        if 'publishDate' in article and 'sentiment' in article:
            try:
                # Make sure we have timezone-aware dates
                if 'Z' in article['publishDate']:
                    # Convert to timezone-aware datetime
                    date = datetime.fromisoformat(article['publishDate'].replace('Z', '+00:00'))
                    # Convert to local timezone (naive datetime) for consistency
                    date = date.replace(tzinfo=None)
                else:
                    # If no timezone info, treat as naive datetime
                    date = datetime.fromisoformat(article['publishDate'])
                
                dates.append(date)
                scores.append(article['sentiment']['score'])
            except (ValueError, TypeError):
                # Use timestamp if available as fallback
                if 'publishTimestamp' in article:
                    try:
                        date = datetime.fromtimestamp(article['publishTimestamp'])
                        dates.append(date)
                        scores.append(article['sentiment']['score'])
                    except:
                        continue
                else:
                    continue
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    if dates and scores:
        # Set a date range that covers our data with a bit of padding
        if len(dates) > 1:
            min_date = min(dates) - timedelta(days=1)
            max_date = max(dates) + timedelta(days=1)
        else:
            # If we only have one date, show a 7-day window around it
            min_date = dates[0] - timedelta(days=3)
            max_date = dates[0] + timedelta(days=3)
        
        # Plot the data points with improved markers
        for i, (date, score) in enumerate(zip(dates, scores)):
            if score > 0.1:
                color = '#00C853'  # Positive - green
                marker = '^'       # Up triangle
            elif score < -0.1:
                color = '#D50000'  # Negative - red
                marker = 'v'       # Down triangle
            else:
                color = '#78909C'  # Neutral - gray
                marker = 'o'       # Circle
            
            ax.scatter(date, score, color=color, s=80, alpha=0.8, marker=marker, 
                       edgecolor='white', linewidth=1)
        
        # Connect points with a line if we have multiple dates
        if len(set(dates)) > 1:
            # Sort the data by date
            date_score_pairs = sorted(zip(dates, scores))
            sorted_dates, sorted_scores = zip(*date_score_pairs)
            
            # Plot the connecting line
            ax.plot(sorted_dates, sorted_scores, color='#2196F3', alpha=0.5, 
                    linestyle='--', linewidth=1.5)
        
        # Add horizontal line at zero
        ax.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        
        # Format x-axis to show dates nicely
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
        
        # Set the appropriate date interval based on date range
        date_range = (max_date - min_date).days
        if date_range <= 7:
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
        elif date_range <= 14:
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=2))
        else:
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=3))
        
        # Add subtle horizontal bands for sentiment zones
        ax.axhspan(0.1, 1.1, facecolor='#E8F5E9', alpha=0.2)  # Positive zone
        ax.axhspan(-0.1, 0.1, facecolor='#ECEFF1', alpha=0.2)  # Neutral zone
        ax.axhspan(-1.1, -0.1, facecolor='#FFEBEE', alpha=0.2)  # Negative zone
        
        # Add subtle text labels for the zones on the right side
        ax.text(max_date, 0.9, "Positive", ha='right', va='center', 
                color='#00C853', fontsize=10, alpha=0.7)
        ax.text(max_date, 0, "Neutral", ha='right', va='center', 
                color='#78909C', fontsize=10, alpha=0.7)
        ax.text(max_date, -0.9, "Negative", ha='right', va='center', 
                color='#D50000', fontsize=10, alpha=0.7)
        
        # Set labels and title
        ax.set_xlabel('Date')
        ax.set_ylabel('Sentiment Score (-1 to 1)')
        ax.set_title('News Sentiment Timeline')
        
        # Create a custom legend
        from matplotlib.lines import Line2D
        legend_elements = [
            Line2D([0], [0], marker='^', color='w', markerfacecolor='#00C853', markersize=10, label='Positive Article'),
            Line2D([0], [0], marker='o', color='w', markerfacecolor='#78909C', markersize=10, label='Neutral Article'),
            Line2D([0], [0], marker='v', color='w', markerfacecolor='#D50000', markersize=10, label='Negative Article')
        ]
        if len(set(dates)) > 1:
            legend_elements.append(Line2D([0], [0], color='#2196F3', linestyle='--', linewidth=1.5, label='Timeline'))
        
        ax.legend(handles=legend_elements, loc='upper left')
        
        # Set x and y axis limits
        ax.set_xlim(min_date, max_date)
        ax.set_ylim(-1.1, 1.1)
        
        # Rotate x-axis labels for better readability
        plt.xticks(rotation=45)
        
        # Add grid for readability
        ax.grid(True, alpha=0.3)
        
        # Add a note about the data
        if len(dates) > 1:
            min_date_str = min(dates).strftime('%b %d')
            max_date_str = max(dates).strftime('%b %d')
            note = f"Based on {len(dates)} articles from {min_date_str} to {max_date_str}"
        else:
            note = f"Based on {len(dates)} article from {dates[0].strftime('%b %d')}"
        
        fig.text(0.5, 0.01, note, ha='center', va='center', fontsize=10, style='italic')
        
    else:
        ax.text(0.5, 0.5, 'No sentiment data available', 
                horizontalalignment='center', verticalalignment='center', transform=ax.transAxes)
    
    plt.tight_layout()
    return fig

def plot_stock_price(stock_data, stock_code):
    dates = []
    prices = []
    
    for point in stock_data['chartData']:
        try:
            date = datetime.strptime(point['date'], '%Y-%m-%d')
            dates.append(date)
            prices.append(point['close'])
        except (ValueError, KeyError):
            continue
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    if dates and prices:
        ax.plot(dates, prices, color='blue', linewidth=2)
        ax.scatter(dates[-1], prices[-1], color='blue', s=100, zorder=5)
        
        change_text = f"Change: {stock_data['priceChange']:.2f} ({stock_data['priceChangePercent']:.2f}%)"
        change_color = 'green' if stock_data['priceChange'] >= 0 else 'red'
        ax.annotate(change_text, xy=(dates[-1], prices[-1]), 
                    xytext=(10, 10), textcoords='offset points',
                    color=change_color, fontweight='bold')
        
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=2))
        ax.set_xlabel('Date')
        ax.set_ylabel('Price ($)')
        ax.set_title(f'{stock_code} Stock Price')
        
        ax.text(0.02, 0.95, f"Current: ${stock_data['currentPrice']}", 
                transform=ax.transAxes, fontsize=12, fontweight='bold',
                bbox=dict(facecolor='white', alpha=0.7))
        
        plt.xticks(rotation=45)
        ax.grid(True, alpha=0.3)
        
        min_price = min(prices)
        y_min = np.floor(min_price * 0.95)
        ax.set_ylim(bottom=y_min)
    else:
        ax.text(0.5, 0.5, 'No price data available', 
                horizontalalignment='center', verticalalignment='center', transform=ax.transAxes)
    
    plt.tight_layout()
    return fig


def plot_sentiment_distribution(articles, stock_code=None):
    sentiment_counts = {"positive": 0, "neutral": 0, "negative": 0}

    for article in articles:
        if 'sentiment' in article and 'label' in article['sentiment']:
            label = article['sentiment']['label']
            if label in sentiment_counts:
                sentiment_counts[label] += 1
    
    # Convert to title case for display
    display_counts = {
        "Positive": sentiment_counts["positive"], 
        "Neutral": sentiment_counts["neutral"], 
        "Negative": sentiment_counts["negative"]
    }
    
    # Define colors with better contrast and visual appeal
    color_spectrum = {
        "Positive": "#00C853",  # Vibrant green
        "Neutral": "#78909C",   # Blue-grey
        "Negative": "#D50000"   # Deep red
    }
    
    # Calculate total and percentages
    total_count = sum(sentiment_counts.values())
    
    # Create figure with specific size for better proportions
    fig = plt.figure(figsize=(12, 7), facecolor='#F8F9FA')
    ax = fig.add_subplot(111, projection='polar')
    
    # Create the title with stock code if provided
    title = 'Distribution of News Sentiment'
    if stock_code:
        title = f'Sentiment Analysis for {stock_code}'
    
    # Include all three sentiment categories
    if total_count == 0:
        percentages = {"Positive": 33.3, "Neutral": 33.3, "Negative": 33.3}
    else:
        percentages = {s: round((display_counts[s] / total_count * 100), 1) for s in display_counts}
    
    # Calculate positions
    pos_end = np.pi * (percentages["Positive"] / 100)
    neu_end = pos_end + np.pi * (percentages["Neutral"] / 100)
    
    # Draw sections with refined appearance
    theta_pos = np.linspace(0, pos_end, 100)
    theta_neu = np.linspace(pos_end, neu_end, 100)
    theta_neg = np.linspace(neu_end, np.pi, 100)
    
    # Add gradient effects to each section
    for i, theta in enumerate(zip(theta_pos[:-1], theta_pos[1:])):
        alpha = 0.7 + (i/len(theta_pos)) * 0.3
        ax.fill_between(theta, 0.6, 1.0, color=color_spectrum["Positive"], alpha=alpha)
        
    for i, theta in enumerate(zip(theta_neu[:-1], theta_neu[1:])):
        alpha = 0.7 + (i/len(theta_neu)) * 0.3
        ax.fill_between(theta, 0.6, 1.0, color=color_spectrum["Neutral"], alpha=alpha)
        
    for i, theta in enumerate(zip(theta_neg[:-1], theta_neg[1:])):
        alpha = 0.7 + (i/len(theta_neg)) * 0.3
        ax.fill_between(theta, 0.6, 1.0, color=color_spectrum["Negative"], alpha=alpha)
    
    # Create labels
    positive_label = f"Positive: {percentages['Positive']}% ({display_counts['Positive']})"
    neutral_label = f"Neutral: {percentages['Neutral']}% ({display_counts['Neutral']})"
    negative_label = f"Negative: {percentages['Negative']}% ({display_counts['Negative']})"
    
    # Position labels with improved style
    ax.text(pos_end/2, 0.4, positive_label, ha='center', va='center', fontsize=12, fontweight='bold',
            bbox=dict(facecolor='white', alpha=0.8, boxstyle='round,pad=0.5', edgecolor=color_spectrum["Positive"]))
    ax.text((pos_end + neu_end)/2, 0.4, neutral_label, ha='center', va='center', fontsize=12, fontweight='bold',
            bbox=dict(facecolor='white', alpha=0.8, boxstyle='round,pad=0.5', edgecolor=color_spectrum["Neutral"]))
    ax.text((neu_end + np.pi)/2, 0.4, negative_label, ha='center', va='center', fontsize=12, fontweight='bold',
            bbox=dict(facecolor='white', alpha=0.8, boxstyle='round,pad=0.5', edgecolor=color_spectrum["Negative"]))
    
    # Clean up the polar chart
    ax.set_thetamin(0)
    ax.set_thetamax(180)
    ax.grid(False)
    ax.set_xticklabels([])
    ax.set_yticklabels([])
    
    # Remove spines
    ax.spines['polar'].set_visible(False)
    
    # Add a decorative gauge line
    ax.plot(np.linspace(0, np.pi, 100), [0.6] * 100, color='#424242', linewidth=2, alpha=0.7)
    
    # Add tick marks on the gauge
    for tick in np.linspace(0, np.pi, 11):
        ax.plot([tick, tick], [0.55, 0.65], color='#424242', linewidth=1.5, alpha=0.7)
    
    # Set title with improved styling
    ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
    
    # Add subtitle with total count
    fig.text(0.5, 0.06, f'Based on analysis of {total_count} news articles', 
            fontsize=12, ha='center', va='center', style='italic')
    
    # Add a small indicator showing the proportion visually
    indicator_x = np.pi/2
    indicator_y = 1.3
    indicator_radius = 0.05
    if total_count > 0:
        # Position indicator based on overall sentiment
        overall_score = (percentages["Positive"] - percentages["Negative"]) / 100
        indicator_x = np.pi/2 + (overall_score * np.pi/2)
        
        # Determine color based on position
        if overall_score > 0.1:
            indicator_color = color_spectrum["Positive"]
        elif overall_score < -0.1:
            indicator_color = color_spectrum["Negative"]
        else:
            indicator_color = color_spectrum["Neutral"]
        
        # Draw the indicator
        ax.scatter(indicator_x, indicator_y, s=150, color=indicator_color, 
                zorder=10, edgecolor='white', linewidth=1.5)
        
        # Add a small needle pointing to the position
        ax.plot([indicator_x, indicator_x], [0.6, indicator_y-indicator_radius], 
                color='#424242', linewidth=1.5, linestyle='-', alpha=0.7)
    
    plt.tight_layout()
    return fig

def generate_word_cloud(articles, stock_code):
    all_text = ' '.join([article.get('summary', '') for article in articles if article.get('summary')])
    
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
        ax.text(0.5, 0.5, 'No text data available for word cloud', 
                horizontalalignment='center', verticalalignment='center', transform=ax.transAxes)
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


def generate_text_report(articles, stock_data, stock_code, output_dir):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_filename = f"{stock_code}_analysis_{timestamp}.txt"
    report_path = os.path.join(output_dir, report_filename)
    
    sentiment_summary = calculate_overall_sentiment(articles)
    
    with open(report_path, 'w') as f:
        f.write(f"=== {stock_code} NEWS ANALYSIS REPORT ===\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("=== STOCK PRICE SUMMARY ===\n")
        if stock_data:
            f.write(f"Current Price: ${stock_data.get('currentPrice', 'N/A')}\n")
            change = stock_data.get('priceChange', 0)
            change_pct = stock_data.get('priceChangePercent', 0)
            change_dir = "↑" if change >= 0 else "↓"
            f.write(f"Recent Change: {change_dir} ${abs(change):.2f} ({change_pct:.2f}%)\n")
            f.write(f"Daily Range: ${stock_data.get('low', 'N/A')} - ${stock_data.get('high', 'N/A')}\n")
            f.write(f"Volume: {stock_data.get('volume', 'N/A'):,}\n")
        else:
            f.write("Stock price data not available\n")
        
        f.write("\n=== SENTIMENT ANALYSIS ===\n")
        f.write(f"Overall Sentiment: {sentiment_summary['label'].capitalize()}\n")
        f.write(f"Sentiment Score: {sentiment_summary['score']}\n")
        f.write("Distribution:\n")
        for label, count in sentiment_summary['distribution'].items():
            f.write(f"  - {label.capitalize()}: {count}\n")
        
        f.write("\n=== KEY THEMES ===\n")
        themes = extract_key_themes([a.get('summary', '') for a in articles])
        if themes:
            for theme in themes:
                f.write(f"- {theme.capitalize()}\n")
        else:
            f.write("No significant themes identified\n")
        
        f.write(f"\n=== RECENT NEWS ARTICLES ({len(articles)}) ===\n")
        for i, article in enumerate(articles[:10], 1):
            f.write(f"\n--- ARTICLE {i} ---\n")
            f.write(f"Title: {article.get('title', 'No title')}\n")
            
            if 'formattedDate' in article:
                f.write(f"Date: {article['formattedDate']}\n")
            
            if 'source' in article:
                f.write(f"Source: {article['source']}\n")
            
            if 'sentiment' in article:
                sent = article['sentiment']
                f.write(f"Sentiment: {sent['label'].capitalize()} (Score: {sent['score']})\n")
            
            if 'keywords' in article:
                f.write(f"Keywords: {', '.join(article['keywords'])}\n")
            
            if 'summary' in article:
                summary = article['summary']
                if len(summary) > 200:
                    summary = summary[:197] + "..."
                f.write(f"Summary: {summary}\n")
            
            if 'url' in article:
                f.write(f"URL: {article['url']}\n")
    
    return report_path