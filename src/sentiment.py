import re
import yfinance as yf
from typing import Dict, List, Any
from datetime import datetime
from textblob import TextBlob  # For sentiment analysis
import nltk
from nltk.corpus import stopwords
from collections import Counter
import hashlib

# Download necessary NLTK data (run once)
nltk.download('punkt')
nltk.download('stopwords')

def fetch_stock_news(stock_code: str, api_key: str) -> Dict[str, Any]:
    """
    Fetch and enhance news articles for a given stock code.
    """
    # Validate API key
    validate_api_key(api_key)
    
    # Validate stock code format
    validate_stock_code(stock_code)
    
    # Create a ticker object
    ticker = yf.Ticker(stock_code)
    
    # Get news data
    news_data = ticker.news
    
    print(f"DEBUG: Retrieved news data length: {len(news_data) if news_data else 0}")
    
    if not news_data:
        return {"news": [], "message": f"No news articles found for {stock_code}", "count": 0}
    
    # Process the news data with advanced features
    articles = process_news_data(news_data, stock_code)
    
    # Get stock price data for context
    stock_data = get_stock_price_data(ticker)
    
    # Extract key themes across all articles
    themes = extract_key_themes([article['summary'] for article in articles if article.get('summary')])
    
    # Calculate overall sentiment
    overall_sentiment = calculate_overall_sentiment(articles)
    
    return {
        "news": articles, 
        "count": len(articles),
        "stockData": stock_data,
        "keyThemes": themes,
        "overallSentiment": overall_sentiment,
        "lastUpdated": datetime.now().isoformat()
    }


def validate_api_key(api_key: str) -> None:
    """Validate the API key."""
    valid_api_keys = ["a1b2c3d4e5f6g7h8i9j0"]  # For demo purposes
    
    if api_key not in valid_api_keys:
        print(f"DEBUG: Invalid API key: {api_key}")
        raise PermissionError("Invalid API key")


def validate_stock_code(stock_code: str) -> None:
    """Validate the stock code format."""
    if not re.match(r'^[A-Z]{1,5}$', stock_code):
        print(f"DEBUG: Invalid StockCode format: {stock_code}")
        raise ValueError("Invalid StockCode format")


def process_news_data(news_data: List[Dict[str, Any]], stock_code: str) -> List[Dict[str, Any]]:
    """
    Process news data with advanced features including sentiment analysis.
    """
    articles = []
    
    for i, article in enumerate(news_data):
        print(f"DEBUG: Processing article {i}")
        article_data = {}
        
        # Extract basic article data
        article_data = extract_article_data(article)
        
        # Skip articles without enough content
        if not article_data.get('title') and not article_data.get('summary'):
            print(f"DEBUG: Skipping article {i} - insufficient content")
            continue
            
        # Format the date to be more readable
        if 'publishDate' in article_data:
            article_data['formattedDate'] = format_date(article_data['publishDate'])
        
        # Generate a unique ID for the article
        article_data['id'] = generate_article_id(article_data)
        
        # Perform sentiment analysis
        article_data['sentiment'] = analyze_sentiment(
            f"{article_data.get('title', '')} {article_data.get('summary', '')}"
        )
        
        # Check if article specifically mentions the stock code
        article_data['mentionsStock'] = mentions_stock(
            f"{article_data.get('title', '')} {article_data.get('summary', '')}", 
            stock_code
        )
        
        # Extract keywords
        article_data['keywords'] = extract_keywords(
            f"{article_data.get('title', '')} {article_data.get('summary', '')}"
        )
        
        # Calculate reading time
        article_data['readingTimeMinutes'] = calculate_reading_time(article_data.get('summary', ''))
        
        articles.append(article_data)
    
    # Sort articles by date (newest first)
    articles.sort(key=lambda x: x.get('publishDate', ''), reverse=True)
    
    print(f"DEBUG: Processed {len(articles)} articles with advanced features")
    return articles


def extract_article_data(article: Any) -> Dict[str, Any]:
    """Extract basic article data from various possible structures."""
    article_data = {}
    
    # Handle different data structures
    if isinstance(article, dict):
        # If it's the structure from the debug output with a 'content' key
        if 'content' in article and isinstance(article['content'], dict):
            content = article['content']
            
            # Extract fields from content
            article_data['title'] = content.get('title', '')
            
            # Try to get summary from different possible fields
            article_data['summary'] = (
                content.get('summary', '') or 
                content.get('description', '')
            )
            
            # Extract publish date if available
            if 'pubDate' in content:
                article_data['publishDate'] = content['pubDate']
            
            # Extract URL if available
            if 'canonicalUrl' in content and isinstance(content['canonicalUrl'], dict):
                article_data['url'] = content['canonicalUrl'].get('url', '')
            elif 'clickThroughUrl' in content and isinstance(content['clickThroughUrl'], dict):
                article_data['url'] = content['clickThroughUrl'].get('url', '')
                
            # Extract provider/source if available
            if 'provider' in content and isinstance(content['provider'], dict):
                article_data['source'] = content['provider'].get('displayName', '')
                
            # Extract thumbnail if available
            if 'thumbnail' in content and isinstance(content['thumbnail'], dict):
                if 'resolutions' in content['thumbnail'] and content['thumbnail']['resolutions']:
                    for resolution in content['thumbnail']['resolutions']:
                        if resolution.get('tag') == 'original':
                            article_data['imageUrl'] = resolution.get('url', '')
                            break
        else:
            # Direct dictionary structure
            article_data['title'] = article.get('title', '')
            article_data['summary'] = article.get('summary', '') or article.get('description', '')
            
            if 'pubDate' in article:
                article_data['publishDate'] = article['pubDate']
            
            if 'link' in article:
                article_data['url'] = article['link']
            elif 'url' in article:
                article_data['url'] = article['url']
    else:
        # Object with attributes
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


def analyze_sentiment(text: str) -> Dict[str, Any]:
    """
    Perform sentiment analysis on the article text.
    Returns sentiment polarity (-1 to 1) and subjectivity (0 to 1).
    """
    if not text:
        return {"score": 0, "label": "neutral", "confidence": 0}
    
    analysis = TextBlob(text)
    
    # Determine sentiment label
    polarity = analysis.sentiment.polarity
    if polarity > 0.1:
        label = "positive"
    elif polarity < -0.1:
        label = "negative"
    else:
        label = "neutral"
    
    # Calculate confidence (using subjectivity as a proxy)
    confidence = abs(polarity) + (analysis.sentiment.subjectivity * 0.5)
    confidence = min(confidence, 1.0)  # Cap at 1.0
    
    return {
        "score": round(polarity, 2),
        "label": label,
        "confidence": round(confidence, 2)
    }


def extract_keywords(text: str, max_keywords: int = 5) -> List[str]:
    """Extract the most significant keywords from the text."""
    if not text:
        return []
    
    # Tokenize and lowercase
    words = nltk.word_tokenize(text.lower())
    
    # Remove stopwords and non-alphabetic tokens
    stop_words = set(stopwords.words('english'))
    words = [word for word in words if word.isalpha() and word not in stop_words and len(word) > 3]
    
    # Count word frequencies
    word_freq = Counter(words)
    
    # Return the most common keywords
    return [word for word, _ in word_freq.most_common(max_keywords)]


def mentions_stock(text: str, stock_code: str) -> bool:
    """Check if the article explicitly mentions the stock code."""
    if not text or not stock_code:
        return False
    
    # Look for the stock code
    return stock_code.upper() in text.upper()


def format_date(date_str: str) -> str:
    """Format ISO date string to a more readable format."""
    try:
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.strftime('%B %d, %Y at %I:%M %p')
    except (ValueError, TypeError):
        return date_str


def calculate_reading_time(text: str) -> int:
    """Calculate approximate reading time in minutes."""
    if not text:
        return 1
    
    # Average reading speed is ~200-250 words per minute
    words = len(text.split())
    minutes = max(1, round(words / 200))
    
    return minutes


def generate_article_id(article_data: Dict[str, Any]) -> str:
    """Generate a unique ID for the article based on its content."""
    # Use URL if available, otherwise title + summary
    if article_data.get('url'):
        source = article_data['url']
    else:
        source = f"{article_data.get('title', '')}{article_data.get('summary', '')}"
    
    # Create hash
    return hashlib.md5(source.encode()).hexdigest()


def get_stock_price_data(ticker: Any) -> Dict[str, Any]:
    """Get recent stock price data for context."""
    try:
        # Get historical data for the last 5 days
        hist = ticker.history(period="5d")
        
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
        
        return {
            "currentPrice": round(latest['Close'], 2),
            "priceChange": round(price_change, 2),
            "priceChangePercent": round(price_change_percent, 2),
            "volume": int(latest['Volume']),
            "high": round(latest['High'], 2),
            "low": round(latest['Low'], 2),
            "chartData": [
                {
                    "date": date.strftime('%Y-%m-%d'),
                    "close": round(row['Close'], 2),
                    "volume": int(row['Volume'])
                }
                for date, row in hist.iterrows()
            ]
        }
    except Exception as e:
        print(f"Error getting stock data: {e}")
        return {}


def extract_key_themes(summaries: List[str], max_themes: int = 3) -> List[str]:
    """Extract key themes across all articles."""
    if not summaries:
        return []
    
    # Combine all summaries
    all_text = ' '.join(summaries)
    
    # Extract phrases (bigrams and trigrams would be better, but using keywords for simplicity)
    keywords = extract_keywords(all_text, max_themes * 3)
    
    # Group similar keywords (simplified approach)
    themes = []
    current_theme_words = set()
    
    for word in keywords:
        # Check if this word is similar to any in our current themes
        if len(themes) < max_themes:
            themes.append(word)
            current_theme_words.add(word)
    
    return themes


def calculate_overall_sentiment(articles: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate the overall sentiment across all articles."""
    if not articles:
        return {"score": 0, "label": "neutral", "distribution": {"positive": 0, "neutral": 0, "negative": 0}}
    
    # Extract sentiment scores
    scores = [a['sentiment']['score'] for a in articles if 'sentiment' in a]
    
    if not scores:
        return {"score": 0, "label": "neutral", "distribution": {"positive": 0, "neutral": 0, "negative": 0}}
    
    # Calculate average sentiment
    avg_score = sum(scores) / len(scores)
    
    # Determine overall sentiment label
    if avg_score > 0.1:
        label = "positive"
    elif avg_score < -0.1:
        label = "negative"
    else:
        label = "neutral"
    
    # Calculate sentiment distribution
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