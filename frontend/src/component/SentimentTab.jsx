import React, { useState, useEffect } from 'react';

const SentimentTab = ({ ticker, API_BASE_URL }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [sentimentData, setSentimentData] = useState(null);

  useEffect(() => {
    const fetchSentimentData = async () => {
      if (!ticker) return;

      setLoading(true);
      setError(null);

      try {
        console.log(`Fetching sentiment data for: ${ticker}`);
        const response = await fetch(`${API_BASE_URL}/api/company/sentiment?ticker=${ticker}`);
        
        if (!response.ok) {
          let errorMsg = `Failed to fetch sentiment: ${response.status}`;
          try {
            const errData = await response.json();
            errorMsg = errData.error || errorMsg;
          } catch (e) {/* ignore */}
          throw new Error(errorMsg);
        }
        
        const data = await response.json();
        console.log("Sentiment data:", data);
        setSentimentData(data);
      } catch (error) {
        console.error("Error fetching sentiment data:", error);
        setError(error.message);
      } finally {
        setLoading(false);
      }
    };

    fetchSentimentData();
  }, [ticker, API_BASE_URL]);

  // Helper to get color based on sentiment
  const getSentimentColor = (sentiment) => {
    if (!sentiment) return 'text-gray-400';
    
    if (sentiment === 'positive') return 'text-green-500';
    if (sentiment === 'negative') return 'text-red-500';
    return 'text-gray-400';
  };

  // Helper to get icon based on sentiment
  const getSentimentIcon = (sentiment) => {
    if (sentiment === 'positive') return '▲';
    if (sentiment === 'negative') return '▼';
    return '•';
  };

  return (
    <div className="bg-nav rounded-lg shadow-xl p-6 mb-6">
      <h2 className="text-xl font-semibold mb-6">Sentiment Analysis</h2>
      
      {loading && (
        <div className="flex justify-center items-center h-48">
          <div className="animate-spin h-10 w-10 border-t-2 border-b-2 border-blue-500 rounded-full"></div>
        </div>
      )}
      
      {error && (
        <div className="bg-red-900/30 text-white p-4 rounded-lg mb-6">
          <p>{error}</p>
        </div>
      )}
      
      {!loading && !error && sentimentData && (
        <div className="space-y-6">
          {/* Sentiment Chart */}
          <div className="bg-gray-800 rounded-lg p-4">
            <h3 className="text-lg font-medium mb-4 text-center">News Sentiment Distribution</h3>
            <div className="flex items-center justify-center">
              {sentimentData.chart ? (
                <img 
                  src={sentimentData.chart} 
                  alt="Sentiment Distribution" 
                  className="max-w-full rounded-lg"
                />
              ) : (
                <p className="text-gray-400">No sentiment chart available</p>
              )}
            </div>
          </div>
          
          {/* Overall Sentiment Summary */}
          <div className="bg-gray-800 rounded-lg p-4">
            <h3 className="text-lg font-medium mb-2">Overall Sentiment</h3>
            <div className="flex items-center">
              <div className={`text-2xl font-bold ${getSentimentColor(sentimentData.sentiment?.label)}`}>
                {getSentimentIcon(sentimentData.sentiment?.label)} {sentimentData.sentiment?.label?.charAt(0).toUpperCase() + sentimentData.sentiment?.label?.slice(1)}
              </div>
              <div className="ml-4 text-sm text-gray-400">
                Score: {sentimentData.sentiment?.score.toFixed(2)}
              </div>
            </div>
          </div>
          
          {/* Source breakdown */}
          {sentimentData.sources && (
            <div className="bg-gray-800 rounded-lg p-4">
              <h3 className="text-lg font-medium mb-2">Data Sources</h3>
              <div className="text-sm">
                {Object.entries(sentimentData.sources).map(([source, count]) => (
                  <div key={source} className="flex justify-between py-1">
                    <span className="text-gray-300">{source}</span>
                    <span className="text-gray-400">{count} articles</span>
                  </div>
                ))}
                <div className="flex justify-between py-1 border-t border-gray-700 mt-2 pt-2">
                  <span className="text-gray-300 font-medium">Total Articles</span>
                  <span className="text-gray-400">{sentimentData.articleCount}</span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
      
      {!loading && !error && !sentimentData && (
        <div className="text-center text-gray-400 py-10">
          <p>No sentiment data available for {ticker}</p>
        </div>
      )}
    </div>
  );
};

export default SentimentTab;