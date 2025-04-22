import { useState, useEffect } from "react";

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

// Value indicator component - shows undervalued/overvalued with color coding
const ValueIndicator = ({ value }) => {
  if (!value && value !== 0) return <span className="text-gray-400">N/A</span>;
  
  // Assuming value is percentage difference between current price and fair value
  const percentage = parseFloat(value);
  const isUndervalued = percentage > 0;
  
  // Color coding based on value
  const getColor = () => {
    const absPercentage = Math.abs(percentage);
    if (isUndervalued) {
      if (absPercentage > 50) return 'text-green-400';
      if (absPercentage > 25) return 'text-green-500';
      return 'text-green-600';
    } else {
      if (absPercentage > 50) return 'text-red-400';
      if (absPercentage > 25) return 'text-red-500';
      return 'text-red-600';
    }
  };
  
  return (
    <div className={`font-medium ${getColor()}`}>
      {Math.abs(percentage).toFixed(1)}% {isUndervalued ? 'undervalued' : 'overvalued'}
    </div>
  );
};

// Return indicator component - shows percentage with color coding
const ReturnIndicator = ({ value, prefix }) => {
  if (!value && value !== 0) return <span className="text-gray-400">N/A</span>;
  
  const percentage = parseFloat(value);
  
  const getColor = () => {
    if (percentage > 10) return 'text-green-400';
    if (percentage > 0) return 'text-green-600';
    if (percentage < -10) return 'text-red-400';
    if (percentage < 0) return 'text-red-600';
    return 'text-gray-400';
  };
  
  return (
    <div className={`font-medium ${getColor()}`}>
      {percentage > 0 && '+'}
      {prefix || ''}{percentage.toFixed(1)}%
    </div>
  );
};

// Mini chart component
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

// Company logo component
const CompanyLogo = ({ ticker, name }) => {
  return (
    <div 
      className="w-10 h-10 rounded-full flex items-center justify-center text-white font-bold bg-gradient-to-br from-blue-500 to-purple-600"
    >
      {ticker.substring(0, 2)}
    </div>
  );
};

const ImprovedResultsTable = ({ companies, onSelect, selectedCompanies }) => {
  const [valuationData, setValuationData] = useState({});
  const [loading, setLoading] = useState(false);
  
  // Load DCF valuation data for all companies
  useEffect(() => {
    if (!companies || companies.length === 0) return;
    
    const fetchValuationData = async () => {
      setLoading(true);
      const newValuationData = {};
      
      // Process companies in batches to avoid overwhelming the server
      const batchSize = 5;
      const uniqueTickers = [...new Set(companies.map(c => c.ticker))];
      
      for (let i = 0; i < uniqueTickers.length; i += batchSize) {
        const batch = uniqueTickers.slice(i, i + batchSize);
        
        await Promise.all(batch.map(async (ticker) => {
          try {
            const response = await fetch(`http://192.168.64.2:5000/fundamentals/calculate_dcf?ticker=${ticker}`);
            if (response.ok) {
              const data = await response.json();
              newValuationData[ticker] = data;
            }
          } catch (error) {
            console.error(`Error fetching valuation for ${ticker}:`, error);
          }
        }));
        
        // Small delay to avoid overwhelming the server
        if (i + batchSize < uniqueTickers.length) {
          await new Promise(resolve => setTimeout(resolve, 500));
        }
      }
      
      setValuationData(newValuationData);
      setLoading(false);
    };
    
    fetchValuationData();
  }, [companies]);
  
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
      id: 'price_vs_value', 
      label: 'Price Vs Fair Value', 
      tooltip: 'Shows current price and percentage difference from calculated fair value. Green indicates undervalued, red indicates overvalued.'
    },
    { 
      id: 'return_7d', 
      label: '7D Return', 
      tooltip: 'Percentage return over the last 7 days and absolute value change'
    },
    { 
      id: 'total_return', 
      label: 'Total Return', 
      tooltip: 'Total percentage return since purchase or tracking, and absolute value change'
    },
    { 
      id: 'value_cost', 
      label: 'Value & Cost', 
      tooltip: 'Current total value of holdings and original cost basis'
    },
    { 
      id: 'chart_1y', 
      label: '1Y Chart', 
      tooltip: 'Price chart showing movement over the last year'
    }
  ];

  return (
    <div className="bg-[#1a1d26] rounded-lg shadow-xl overflow-hidden mb-6">
      {/* Table header */}
      <div className="grid grid-cols-7 text-gray-400 text-xs font-medium uppercase tracking-wider border-b border-gray-800">
        {columns.map(column => (
          <div key={column.id} className={`px-4 py-3 ${column.width || ''}`}>
            <div className="flex items-center">
              {column.label}
              <InfoTooltip title={column.label} content={column.tooltip} />
            </div>
          </div>
        ))}
      </div>
      
      {/* Loading overlay */}
      {loading && (
        <div className="flex justify-center items-center py-16">
          <svg className="animate-spin h-10 w-10 text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <span className="ml-2 text-gray-300">Loading valuations...</span>
        </div>
      )}
      
      {/* Table body */}
      {!loading && (
        <div className="divide-y divide-gray-800">
          {companies.map((company) => {
            const valuation = valuationData[company.ticker] || {};
            
            // Calculate valuation percentage if we have the data
            let valuationPercent = null;
            if (valuation.fair_value && valuation.current_price) {
              const fairValue = parseFloat(valuation.fair_value);
              const currentPrice = parseFloat(valuation.current_price);
              valuationPercent = ((fairValue - currentPrice) / currentPrice) * 100;
            }
            
            return (
              <div 
                key={company.ticker} 
                className={`grid grid-cols-7 hover:bg-gray-800 cursor-pointer transition ${
                  selectedCompanies.includes(company.ticker) ? 'bg-gray-800' : ''
                }`}
                onClick={() => onSelect(company.ticker)}
              >
                <div className="px-4 py-5 col-span-2">
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
                    US${valuation.current_price || 'N/A'}
                  </div>
                  <ValueIndicator value={valuationPercent} />
                </div>
                
                <div className="px-4 py-5 flex flex-col justify-center">
                  <ReturnIndicator value={Math.random() * 10 - 5} /> {/* Placeholder - would use real data */}
                  <div className="text-gray-400 text-sm">+US$--</div>
                </div>
                
                <div className="px-4 py-5 flex flex-col justify-center">
                  <ReturnIndicator value={Math.random() * 50 - 10} /> {/* Placeholder - would use real data */}
                  <div className="text-gray-400 text-sm">+US$--</div>
                </div>
                
                <div className="px-4 py-5 flex flex-col justify-center">
                  <div className="text-white">US$--</div>
                  <div className="text-gray-400">US$--</div>
                </div>
                
                <div className="px-4 py-5 flex items-center">
                  <MiniChart ticker={company.ticker} />
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default ImprovedResultsTable;