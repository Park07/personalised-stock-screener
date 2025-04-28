import pytest
from unittest.mock import patch, Mock # For mocking external calls
from datetime import datetime
import yfinance as yf 
from src.sentiment import ( 
    get_api_team_news,
    get_yahoo_news,
    get_finviz_news
)

# --- Tests for get_api_team_news ---

@patch('src.sentiment.requests.get') 
def test_api_team_news_success(mock_get):
    """Test get_api_team_news handles a successful API response."""
    # Configure the mock response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "news": [
            "API Article 1 text.",
            "API Article 2 about finance."
        ]
    }
    mock_get.return_value = mock_response

    ticker = "TESTAPI"
    result = get_api_team_news(ticker)

    # Assertions
    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0]['source'] == "API Team News"
    assert result[0]['title'] == "API Article 1 text." # Title is truncated or full text if short
    assert result[0]['summary'] == "API Article 1 text."
    assert result[1]['id'].startswith(f"api-{ticker}-")
    mock_get.assert_called_once() # Check if requests.get was called

@patch('src.sentiment.requests.get')
def test_api_team_news_api_error(mock_get):
    """Test get_api_team_news handles an API error status code."""
    mock_response = Mock()
    mock_response.status_code = 500 # Simulate server error
    mock_response.json.return_value = {"error": "Server down"} 
    mock_get.return_value = mock_response

    ticker = "TESTFAIL"
    result = get_api_team_news(ticker)

    # Assertions
    assert isinstance(result, list)
    assert len(result) == 0 # Should return empty list on error

@patch('src.sentiment.requests.get')
def test_api_team_news_empty_list(mock_get):
    """Test get_api_team_news handles an empty news list from the API."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"news": []} # API returns success but no news
    mock_get.return_value = mock_response

    ticker = "TESTEMPTY"
    result = get_api_team_news(ticker)

    # Assertions
    assert isinstance(result, list)
    assert len(result) == 0

# --- Tests for get_yahoo_news ---

@patch('src.sentiment.yf.Ticker') # Mock the Ticker class constructor
def test_yahoo_news_success(mock_ticker_constructor):
    """Test get_yahoo_news handles a successful response."""
    # Create mock news data similar to yfinance structure
    mock_news_list = [
        {
            'uuid': 'abc',
            'title': 'Yahoo Headline One',
            'publisher': 'Reuters',
            'link': 'http://yahoo.example.com/1',
            'providerPublishTime': int(datetime.now().timestamp()) - 3600, # 1 hour ago
            'type': 'STORY',
            # 'thumbnail': {...} # Can add if needed
            'summary': 'Summary for article one.' # Added summary field based on function usage
        },
         {
            'uuid': 'def',
            'title': 'Yahoo Headline Two',
            'publisher': 'AP',
            'link': 'http://yahoo.example.com/2',
            'providerPublishTime': int(datetime.now().timestamp()) - 7200, # 2 hours ago
            'type': 'STORY',
            'summary': 'Summary for article two.' # Added summary field
        }
    ]
    # Configure the mock Ticker instance returned by the constructor
    mock_ticker_instance = Mock()
    mock_ticker_instance.news = mock_news_list # Set the .news attribute
    mock_ticker_constructor.return_value = mock_ticker_instance # Make constructor return our mock

    ticker = "TESTYF"
    result = get_yahoo_news(ticker)

    # Assertions
    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0]['title'] == 'Yahoo Headline One'
    assert result[0]['source'] == 'Yahoo Finance'
    assert result[0]['url'] == 'http://yahoo.example.com/1'
    assert 'publishDate' in result[0]
    assert result[1]['summary'] == 'Summary for article two.'
    mock_ticker_constructor.assert_called_once_with(ticker) # Check Ticker was called with correct ticker

@patch('src.sentiment.yf.Ticker')
def test_yahoo_news_no_news(mock_ticker_constructor):
    """Test get_yahoo_news handles when the API returns no news."""
    mock_ticker_instance = Mock()
    mock_ticker_instance.news = [] # Simulate empty news list
    mock_ticker_constructor.return_value = mock_ticker_instance

    ticker = "TESTNOYF"
    result = get_yahoo_news(ticker)

    # Assertions
    assert isinstance(result, list)
    assert len(result) == 0

# --- Tests for get_finviz_news ---

# Mocking urlopen requires careful handling of the response object
@patch('src.sentiment.urlopen') # Mock urlopen function from urllib.request
def test_finviz_news_success(mock_urlopen):
    """Test get_finviz_news handles successful scraping."""
    # Sample HTML structure for the news table
    mock_html = """
    <html><body>
    <table id="news-table">
        <tr><td title="Today 10:00AM">Today 10:00AM</td><td><a href="http://example.com/1">Finviz News 1</a> <div><span>Source One</span></div></td></tr>
        <tr><td title="Apr-28-25 09:00AM">Apr-28-25 09:00AM</td><td><a href="http://example.com/2">Finviz News 2</a> <div><span>Source Two</span></div></td></tr>
        <tr><td title="Apr-27-25 08:00AM">Apr-27-25 08:00AM</td><td><a href="http://example.com/3">Finviz News 3 (older)</a></td></tr>
    </table>
    </body></html>
    """
    # Configure the mock urlopen response
    mock_response = Mock()
    # The read() method should return bytes
    mock_response.read.return_value = mock_html.encode('utf-8')
    # urlopen itself returns the response object
    mock_urlopen.return_value = mock_response

    ticker = "TESTFVZ"
    # Test fetching news within the last 2 days for simplicity
    result = get_finviz_news(ticker, days=2)

    # Assertions
    assert isinstance(result, list)
    assert len(result) == 3 # Should exclude the older article 
    assert result[0]['title'] == 'Finviz News 1'
    assert result[0]['source'] == 'Source One'
    assert result[0]['url'] == 'http://example.com/1'
    assert result[1]['title'] == 'Finviz News 2'
    assert result[1]['source'] == 'Source Two' # Handles source correctly
    assert result[1]['id'].startswith('finviz-')
    mock_urlopen.assert_called_once() # Check that urlopen was called

@patch('src.sentiment.urlopen')
def test_finviz_news_no_table(mock_urlopen):
    """Test get_finviz_news handles when the news table isn't found."""
    mock_html = "<html><body><p>No news table here</p></body></html>"
    mock_response = Mock()
    mock_response.read.return_value = mock_html.encode('utf-8')
    mock_urlopen.return_value = mock_response

    ticker = "TESTNOFVZ"
    result = get_finviz_news(ticker)

    # Assertions
    assert isinstance(result, list)
    assert len(result) == 0