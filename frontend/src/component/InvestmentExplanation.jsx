import { useState } from 'react';

export const GoalExplanation = () => {
  const [expanded, setExpanded] = useState(false);
  
  return (
    <div className="mt-2 bg-gray-800 rounded-lg p-4 text-sm">
      <button 
        className="flex items-center justify-between w-full text-left"
        onClick={() => setExpanded(!expanded)}
      >
        <span className="font-medium text-white">What do these investment goals mean?</span>
        <svg 
          xmlns="http://www.w3.org/2000/svg" 
          className={`h-5 w-5 transition-transform ${expanded ? 'transform rotate-180' : ''}`} 
          fill="none" 
          viewBox="0 0 24 24" 
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      
      {expanded && (
        <div className="mt-3 space-y-3">
          <div>
            <h3 className="text-blue-400 font-medium">Value</h3>
            <p className="text-gray-300">Focuses on finding stocks trading below their intrinsic value. Value investors look for companies with strong fundamentals that appear underpriced by the market, often with lower P/E ratios and higher dividend yields.</p>
          </div>
          
          <div>
            <h3 className="text-green-400 font-medium">Income</h3>
            <p className="text-gray-300">Prioritises generating regular cash flow through dividends and interest. Income investors typically seek companies with stable earnings and a history of consistent dividend payments.</p>
          </div>
          
          <div>
            <h3 className="text-purple-400 font-medium">Growth</h3>
            <p className="text-gray-300">Aims for capital appreciation through companies with above-average growth potential. Growth investors look for businesses expanding earnings, revenue, and market share faster than industry peers, often accepting higher valuations.</p>
          </div>
        </div>
      )}
    </div>
  );
};

export const RiskExplanation = () => {
  const [expanded, setExpanded] = useState(false);
  
  return (
    <div className="mt-2 bg-gray-800 rounded-lg p-4 text-sm">
      <button 
        className="flex items-center justify-between w-full text-left"
        onClick={() => setExpanded(!expanded)}
      >
        <span className="font-medium text-white">Understanding risk tolerance levels</span>
        <svg 
          xmlns="http://www.w3.org/2000/svg" 
          className={`h-5 w-5 transition-transform ${expanded ? 'transform rotate-180' : ''}`} 
          fill="none" 
          viewBox="0 0 24 24" 
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      
      {expanded && (
        <div className="mt-3 space-y-3">
          <div>
            <h3 className="text-green-400 font-medium">Conservative</h3>
            <p className="text-gray-300">Prioritises capital preservation over growth. Conservative investors prefer stable, established companies with strong balance sheets, consistent dividends, and lower volatility. Typically includes more defensive sectors like utilities and consumer staples.</p>
          </div>
          
          <div>
            <h3 className="text-yellow-400 font-medium">Moderate</h3>
            <p className="text-gray-300">Seeks a balance between growth and capital preservation. Moderate investors accept some volatility for the potential of higher returns, often creating diversified portfolios across growth and value stocks in various sectors.</p>
          </div>
          
          <div>
            <h3 className="text-red-400 font-medium">Aggressive</h3>
            <p className="text-gray-300">Focuses on maximising growth potential and accepts higher volatility. Aggressive investors target companies with substantial growth prospects, including smaller companies, emerging technologies, and cyclical sectors that may experience larger price swings.</p>
          </div>
        </div>
      )}
    </div>
  );
};