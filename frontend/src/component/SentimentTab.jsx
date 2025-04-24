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

  // Helper to get color based on sentiment - using neon colors
  const getSentimentColor = (sentiment) => {
    if (!sentiment) return 'text-gray-400';
    
    // Use neon colors that match the chart
    if (sentiment === 'positive') return 'text-[#32FF6A]';  // Neon green
    if (sentiment === 'negative') return 'text-[#FF3251]';  // Neon red
    return 'text-[#3333B2]';  // Matching blue for neutral
  };

  // Helper to get icon based on sentiment
  const getSentimentIcon = (sentiment) => {
    if (sentiment === 'positive') return '▲';
    if (sentiment === 'negative') return '▼';
    return '•';
  };

  // Helper for handling image error
  const handleImageError = (e) => {
    console.warn(`Sentiment chart failed to load`);
    const parent = e.target.parentNode;
    if (parent) {
      e.target.style.display = 'none';
      if (!parent.querySelector('.chart-error-message')) {
        const errorMsg = document.createElement('p');
        errorMsg.className = 'text-red-500 text-xs chart-error-message';
        errorMsg.textContent = 'Chart unavailable';
        parent.appendChild(errorMsg);
      }
    }
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
          {/* Sentiment Chart - Sized to match other charts */}
          <div className="mb-12">
            <h3 className="text-lg font-medium mb-4">News Sentiment Distribution</h3>
            <div className="bg-gray-800 rounded-lg p-4 h-[560px] flex items-center justify-center">
              {sentimentData.chart ? (
                <img 
                  src={sentimentData.chart} 
                  alt="Sentiment Distribution" 
                  className="max-w-full max-h-full object-contain rounded"
                  onError={handleImageError}
                />
              ) : (
                <p className="text-gray-400">No sentiment chart available</p>
              )}
            </div>
          </div>
          
          {/* Overall Sentiment Summary */}
          <div className="bg-gray-800 rounded-lg p-6">
            <h3 className="text-lg font-medium mb-4">Overall Sentiment</h3>
            <div className="flex items-center">
              <div className={`text-3xl font-bold ${getSentimentColor(sentimentData.sentiment?.label)}`}>
                {getSentimentIcon(sentimentData.sentiment?.label)} {sentimentData.sentiment?.label?.charAt(0).toUpperCase() + sentimentData.sentiment?.label?.slice(1)}
              </div>
              <div className="ml-6 text-base text-gray-300">
                Score: {sentimentData.sentiment?.score.toFixed(2)}
              </div>
            </div>
          </div>
          
          {/* Source breakdown */}
          {sentimentData.sources && (
            <div className="bg-gray-800 rounded-lg p-6">
              <h3 className="text-lg font-medium mb-4">Data Sources</h3>
              <div className="grid grid-cols-1 gap-2">
                {Object.entries(sentimentData.sources).map(([source, count]) => (
                  <div key={source} className="flex justify-between py-2 border-b border-gray-700">
                    <span className="text-gray-300 font-medium">{source}</span>
                    <span className="text-gray-300">{count} articles</span>
                  </div>
                ))}
                <div className="flex justify-between py-2 mt-2 pt-2 bg-gray-700/20 rounded-md px-3">
                  <span className="text-white font-medium">Total Articles</span>
                  <span className="text-white font-medium">{sentimentData.articleCount}</span>
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
