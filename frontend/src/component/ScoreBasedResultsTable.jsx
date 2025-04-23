import { useState, useEffect } from "react";

// Score indicator that shows the score with appropriate color
const ScoreIndicator = ({ score }) => {
  if (!score && score !== 0) return <span className="text-gray-400">N/A</span>;
  
  const numScore = parseFloat(score);
  
  // Color coding based on score value
  const getColor = () => {
    if (numScore >= 4.5) return 'text-green-400';
    if (numScore >= 3.5) return 'text-green-600';
    if (numScore >= 2.5) return 'text-yellow-400';
    if (numScore >= 1.5) return 'text-red-600';
    return 'text-red-400';
  };
  
  return (
    <div className={`font-medium ${getColor()}`}>
      {numScore.toFixed(1)}
    </div>
  );
};

// Info tooltip component for explaining metrics
const InfoTooltip = ({ title, content }) => {
  const [isVisible, setIsVisible] = useState(false);
  
  return (
    <div className="relative inline-block">
      <button
        className="ml-1 text-gray-400 hover:text-gray-300 focus:outline-none"
        onMouseEnter={() => setIsVisible(true)}
        onMouseLeave={() => setIsVisible(false)}
        onClick={(e) => {
          e.stopPropagation();
          setIsVisible(!isVisible);
        }}
      >
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-4 h-4">
          <circle cx="12" cy="12" r="10"></circle>
          <line x1="12" y1="16" x2="12" y2="12"></line>
          <line x1="12" y1="8" x2="12.01" y2="8"></line>
        </svg>
      </button>
      
      {isVisible && (
        <div className="absolute z-10 w-64 p-4 mt-2 bg-gray-800 rounded-md shadow-lg -left-32 top-full">
          <h3 className="font-semibold text-white mb-1">{title}</h3>
          <p className="text-sm text-gray-300">{content}</p>
        </div>
      )}
    </div>
  );
};

// Mini chart component (would ideally use real data)
const MiniChart = ({ ticker }) => {
  // In a real implementation, this would fetch chart data for the ticker
  // Here we'll show a placeholder with a unique pattern based on the ticker
  
  const getPatternFromTicker = (ticker) => {
    let seed = 0;
    for (let i = 0; i < ticker.length; i++) {
      seed += ticker.charCodeAt(i);
    }
    
    // Generate a somewhat unique but consistent pattern based on ticker
    const points = [];
    const numPoints = 20;
    const height = 30;
    const width = 80;
    
    for (let i = 0; i < numPoints; i++) {
      const x = (i / (numPoints - 1)) * width;
      const seedValue = Math.sin(i * (seed % 10)) * 10;
      const y = height / 2 + seedValue;
      points.push(`${x},${y}`);
    }
    
    // Determine if chart should be positive or negative based on ticker
    const positive = seed % 3 !== 0;
    
    return {
      path: `M ${points.join(' L ')}`,
      positive
    };
  };
  
  const { path, positive } = getPatternFromTicker(ticker);
  
  return (
    <div className="w-20 h-12">
      <svg width="80" height="30" viewBox="0 0 80 30">
        <path
          d={path}
          fill="none"
          stroke={positive ? "#4ade80" : "#f87171"}
          strokeWidth="2"
        />
      </svg>
    </div>
  );
};

// Company logo placeholder component
const CompanyLogo = ({ ticker, name }) => {
  return (
    <div 
      className="w-10 h-10 rounded-full flex items-center justify-center text-white font-bold bg-gradient-to-br from-blue-500 to-purple-600"
    >
      {ticker.substring(0, 2)}
    </div>
  );
};

const ScoreBasedResultsTable = ({ companies, onSelect, selectedCompanies }) => {
  if (!companies || companies.length === 0) {
    return (
      <div className="bg-[#1a1d26] rounded-lg shadow-xl p-6 text-center">
        <p className="text-gray-400">No companies match your criteria. Try adjusting your filters.</p>
      </div>
    );
  }

  // Create column definitions with info tooltips
  const columns = [
    { 
      id: 'symbol', 
      label: 'Symbol', 
      width: 'col-span-2',
      tooltip: 'Stock ticker symbol and company name'
    },
    { 
      id: 'current_price', 
      label: 'Current Price', 
      tooltip: 'Current market price per share'
    },
    { 
      id: 'valuation_score', 
      label: 'Valuation', 
      tooltip: 'Score based on P/E Ratio, PEG Ratio, and EV/EBITDA metrics. Higher is better (undervalued).'
    },
    { 
      id: 'health_score', 
      label: 'Health', 
      tooltip: 'Score based on dividend yield, payout ratio, debt/equity ratio, and current ratio. Higher is better (financially healthier).'
    },
    { 
      id: 'growth_score', 
      label: 'Growth', 
      tooltip: 'Score based on revenue growth, earnings growth, and operating cash flow growth. Higher is better (stronger growth).'
    },
    { 
      id: 'overall_score', 
      label: 'Overall', 
      tooltip: 'Combined score from valuation, health, and growth factors. Higher is better (more attractive investment).'
    }
  ];

  return (
    <div className="bg-[#1a1d26] rounded-lg shadow-xl overflow-hidden mb-6">
      {/* Table header */}
      <div className="grid grid-cols-7 text-gray-400 text-xs font-medium uppercase tracking-wider border-b border-gray-800">
        <div className="px-6 py-3 col-span-2">Company</div>
        <div className="px-4 py-3">Price</div>
        <div className="px-4 py-3">
          <div className="flex items-center">
            Valuation
            <InfoTooltip 
              title="Valuation Score" 
              content="Based on P/E Ratio, PEG Ratio, and EV/EBITDA. Higher scores (green) indicate the stock is potentially undervalued." 
            />
          </div>
        </div>
        <div className="px-4 py-3">
          <div className="flex items-center">
            Health
            <InfoTooltip 
              title="Financial Health Score" 
              content="Based on dividend yield, payout ratio, debt/equity ratio, and current ratio. Higher scores indicate better financial stability." 
            />
          </div>
        </div>
        <div className="px-4 py-3">
          <div className="flex items-center">
            Growth
            <InfoTooltip 
              title="Growth Score" 
              content="Based on revenue growth, earnings growth, and cash flow growth rates. Higher scores indicate stronger future growth potential." 
            />
          </div>
        </div>
        <div className="px-4 py-3">
          <div className="flex items-center">
            Overall
            <InfoTooltip 
              title="Overall Score" 
              content="Combined score based on valuation, health, and growth metrics. A higher score means a better overall investment opportunity." 
            />
          </div>
        </div>
      </div>
      
      {/* Table body */}
      <div className="divide-y divide-gray-800">
        {companies.map((company) => (
          <div 
            key={company.ticker} 
            className={`grid grid-cols-7 hover:bg-gray-800 cursor-pointer transition ${
              selectedCompanies.includes(company.ticker) ? 'bg-gray-800' : ''
            }`}
            onClick={() => onSelect(company.ticker)}
          >
            <div className="px-6 py-5 col-span-2">
              <div className="flex items-center">
                <input
                  type="checkbox"
                  className="mr-4 h-5 w-5 rounded border-gray-600 text-blue-600 focus:ring-blue-500"
                  checked={selectedCompanies.includes(company.ticker)}
                  onChange={(e) => {
                    e.stopPropagation();
                    onSelect(company.ticker);
                  }}
                />
                
                <CompanyLogo ticker={company.ticker} name={company.name} />
                
                <div className="ml-4">
                  <div className="text-blue-400 font-medium">{company.ticker}</div>
                  <div className="text-gray-400">{company.name}</div>
                </div>
              </div>
            </div>
            
            <div className="px-4 py-5 flex flex-col justify-center">
              <div className="text-white">
                {company.current_price ? `$${company.current_price}` : 'N/A'}
              </div>
              <div className="text-gray-400 text-sm">
                {company.market_cap ? `$${company.market_cap}` : ''}
              </div>
            </div>
            
            <div className="px-4 py-5 flex items-center">
              <ScoreIndicator score={company.valuation_score} />
            </div>
            
            <div className="px-4 py-5 flex items-center">
              <ScoreIndicator score={company.health_score} />
            </div>
            
            <div className="px-4 py-5 flex items-center">
              <ScoreIndicator score={company.growth_score} />
            </div>
            
            <div className="px-4 py-5 flex items-center">
              <ScoreIndicator score={company.overall_score} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ScoreBasedResultsTable;