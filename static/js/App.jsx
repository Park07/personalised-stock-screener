import { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Newspaper, TrendingUp, TrendingDown, AlertCircle, Clock, ArrowUpRight } from 'lucide-react';

const StockNewsDashboard = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [stockCode, setStockCode] = useState('TSLA');

  useEffect(() => {
    const fetchNews = async () => {
      setLoading(true);
      try {
        const response = await fetch(`/fetch/news?stockCode=${stockCode}&apiKey=a1b2c3d4e5f6g7h8i9j0`);
        if (!response.ok) {
          throw new Error(`Error: ${response.status}`);
        }
        const newsData = await response.json();
        setData(newsData);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchNews();
  }, [stockCode]);

  const handleStockChange = (e) => {
    setStockCode(e.target.value.toUpperCase());
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4">
        <div className="flex">
          <AlertCircle className="h-5 w-5 text-red-500 mr-2" />
          <p className="text-red-500">Error loading news: {error}</p>
        </div>
      </div>
    );
  }

  if (!data || !data.news || data.news.length === 0) {
    return (
      <div className="p-4">
        <div className="mb-4">
          <input
            type="text"
            value={stockCode}
            onChange={handleStockChange}
            className="border border-gray-300 rounded-md px-3 py-2 w-32"
            placeholder="Stock Symbol"
          />
          <button
            onClick={() => setStockCode(stockCode)}
            className="ml-2 bg-blue-500 text-white py-2 px-4 rounded-md hover:bg-blue-600"
          >
            Fetch
          </button>
        </div>
        <div className="bg-gray-50 border border-gray-200 rounded-md p-4">
          <p>No news articles found for {stockCode}</p>
        </div>
      </div>
    );
  }

  // Sample data - in real app, this would come from the API
  const stockData = data.stockData || {
    currentPrice: 421.45,
    priceChange: -23.78,
    priceChangePercent: -5.34,
    chartData: [
      { date: '2025-04-12', close: 445.23 },
      { date: '2025-04-13', close: 448.76 },
      { date: '2025-04-14', close: 455.12 },
      { date: '2025-04-15', close: 449.87 },
      { date: '2025-04-16', close: 421.45 }
    ]
  };

  const sentimentData = data.overallSentiment || {
    score: -0.18,
    label: "negative",
    distribution: { positive: 2, neutral: 3, negative: 5 }
  };

  // Get sentiment color
  const getSentimentColor = (label) => {
    switch (label) {
      case 'positive': return 'text-green-600';
      case 'negative': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  // Get sentiment icon
  const SentimentIcon = ({ label, className }) => {
    switch (label) {
      case 'positive':
        return <TrendingUp className={className} />;
      case 'negative':
        return <TrendingDown className={className} />;
      default:
        return <div className={`w-4 h-0.5 bg-current rounded ${className}`} />;
    }
  };

  return (
    <div className="p-4 max-w-6xl mx-auto">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold">{stockCode} News Analysis</h1>
          <p className="text-gray-500">Latest news and sentiment analysis</p>
        </div>
        <div className="mt-4 md:mt-0">
          <input
            type="text"
            value={stockCode}
            onChange={handleStockChange}
            className="border border-gray-300 rounded-md px-3 py-2 w-32"
            placeholder="Stock Symbol"
          />
          <button
            onClick={() => setStockCode(stockCode)}
            className="ml-2 bg-blue-500 text-white py-2 px-4 rounded-md hover:bg-blue-600"
          >
            Fetch
          </button>
        </div>
      </div>

      {/* Stock and Sentiment Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        {/* Stock Price Card */}
        <div className="bg-white p-4 rounded-lg shadow">
          <h2 className="text-lg font-semibold mb-2">Current Price</h2>
          <div className="flex items-end">
            <span className="text-3xl font-bold">${stockData.currentPrice}</span>
            <span className={`ml-2 flex items-center ${stockData.priceChange >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {stockData.priceChange >= 0 ? '+' : ''}{stockData.priceChange} ({stockData.priceChangePercent}%)
            </span>
          </div>
          <div className="h-32 mt-4">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={stockData.chartData}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                <XAxis dataKey="date" hide />
                <YAxis domain={['auto', 'auto']} hide />
                <Tooltip 
                  formatter={(value) => [`$${value}`, 'Price']}
                  labelFormatter={(label) => `Date: ${label}`}
                />
                <Line 
                  type="monotone" 
                  dataKey="close" 
                  stroke={stockData.priceChange >= 0 ? "#16a34a" : "#dc2626"} 
                  strokeWidth={2} 
                  dot={false} 
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Sentiment Overview Card */}
        <div className="bg-white p-4 rounded-lg shadow">
          <h2 className="text-lg font-semibold mb-2">Sentiment Analysis</h2>
          <div className="flex items-center">
            <SentimentIcon 
              label={sentimentData.label} 
              className={`w-6 h-6 ${getSentimentColor(sentimentData.label)}`} 
            />
            <span className={`ml-2 text-xl font-semibold capitalize ${getSentimentColor(sentimentData.label)}`}>
              {sentimentData.label}
            </span>
          </div>
          <p className="text-gray-600 mt-1">Score: {sentimentData.score}</p>
          
          <div className="mt-4">
            <h3 className="text-sm font-medium text-gray-500 mb-2">Sentiment Distribution</h3>
            <div className="flex items-center">
              <div className="w-full bg-gray-200 rounded-full h-2.5">
                <div 
                  className="bg-green-500 h-2.5 rounded-full" 
                  style={{ 
                    width: `${(sentimentData.distribution.positive / 
                            (sentimentData.distribution.positive + 
                             sentimentData.distribution.neutral + 
                             sentimentData.distribution.negative)) * 100}%` 
                  }}
                ></div>
              </div>
            </div>
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>Positive: {sentimentData.distribution.positive}</span>
              <span>Neutral: {sentimentData.distribution.neutral}</span>
              <span>Negative: {sentimentData.distribution.negative}</span>
            </div>
          </div>
        </div>

        {/* Key Themes Card */}
        <div className="bg-white p-4 rounded-lg shadow">
          <h2 className="text-lg font-semibold mb-2">Key Themes</h2>
          <ul className="space-y-2">
            {(data.keyThemes || ['Earnings', 'China market', 'Profitability']).map((theme, index) => (
              <li key={index} className="flex items-center bg-blue-50 p-2 rounded">
                <div className="w-1 h-6 bg-blue-500 rounded mr-2"></div>
                <span className="capitalize">{theme}</span>
              </li>
            ))}
          </ul>
          <div className="mt-4">
            <p className="text-gray-500 text-sm flex items-center">
              <Clock className="w-4 h-4 mr-1" />
              Based on {data.count} articles
            </p>
          </div>
        </div>
      </div>

      {/* News Articles */}
      <h2 className="text-xl font-semibold mb-4">Latest News</h2>
      <div className="space-y-4">
        {data.news.map((article, index) => (
          <div key={index} className="bg-white p-4 rounded-lg shadow border-l-4 border-blue-500">
            <div className="flex justify-between">
              <h3 className="font-semibold text-lg">{article.title}</h3>
              <div className={`flex items-center ${getSentimentColor(article.sentiment?.label || 'neutral')}`}>
                <SentimentIcon 
                  label={article.sentiment?.label || 'neutral'} 
                  className="w-5 h-5 mr-1" 
                />
                <span className="text-sm capitalize">{article.sentiment?.label || 'neutral'}</span>
              </div>
            </div>

            <p className="text-gray-500 text-sm mt-1">
              {article.source || 'Yahoo Finance'} · {article.formattedDate || '2025-04-16'}
              {article.readingTimeMinutes && (
                <span className="ml-2 inline-flex items-center">
                  <Clock className="w-3 h-3 mr-1" />
                  {article.readingTimeMinutes} min read
                </span>
              )}
            </p>

            <p className="mt-2 text-gray-700 line-clamp-3">{article.summary}</p>
            
            {article.keywords && article.keywords.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-1">
                {article.keywords.map((keyword, kidx) => (
                  <span key={kidx} className="bg-gray-100 text-gray-600 text-xs px-2 py-1 rounded">
                    {keyword}
                  </span>
                ))}
              </div>
            )}
            
            <div className="mt-3">
              <a 
                href={article.url} 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-blue-500 hover:text-blue-700 text-sm font-medium inline-flex items-center"
              >
                Read full article
                <ArrowUpRight className="w-3 h-3 ml-1" />
              </a>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default StockNewsDashboard;