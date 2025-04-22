import { useState, useEffect } from "react";

// Value indicator component - shows undervalued/overvalued with color coding
const ValueIndicator = ({ value }) => {
  // Handle both string format "60.7% undervalued" or number format
  let percentage = value;
  let isUndervalued = true;
  
  if (typeof value === 'string') {
    const match = value.match(/(\d+\.?\d*)%\s*(undervalued|overvalued)/);
    if (match) {
      percentage = parseFloat(match[1]);
      isUndervalued = match[2] === 'undervalued';
    }
  } else if (typeof value === 'number') {
    isUndervalued = value > 0;
  }
  
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
      {percentage}% {isUndervalued ? 'undervalued' : 'overvalued'}
    </div>
  );
};

// Return indicator component - shows percentage with color coding
const ReturnIndicator = ({ value, prefix }) => {
  const percentage = typeof value === 'string' ? parseFloat(value) : value;
  
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
      {prefix || ''}{percentage}%
    </div>
  );
};

// Mini chart component
const MiniChart = ({ data, positive = true }) => {
  // In a real implementation, this would use actual data
  // Here we're using a placeholder SVG
  
  return (
    <div className="w-24 h-12">
      <svg width="96" height="48" viewBox="0 0 96 48">
        <path
          d={positive ? 
            "M0,36 C8,28 16,38 24,30 C32,22 40,26 48,18 C56,10 64,16 72,8 C80,0 88,12 96,4" : 
            "M0,4 C8,12 16,2 24,10 C32,18 40,14 48,22 C56,30 64,24 72,32 C80,40 88,28 96,36"
          }
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
  const [logo, setLogo] = useState(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    // In a real app, fetch from your API or a service like Clearbit
    const fetchLogo = async () => {
      try {
        // For demo purposes - would use real API in production
        const logoUrl = `https://logo.clearbit.com/${ticker.toLowerCase()}.com`;
        const response = await fetch(logoUrl, { method: 'HEAD' });
        
        if (response.ok) {
          setLogo(logoUrl);
        } else {
          throw new Error('Logo not found');
        }
      } catch (err) {
        setError(true);
      }
    };
    
    fetchLogo();
  }, [ticker]);

  // Create fallback ticker logo with colored background
  const createColorFromString = (str) => {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      hash = str.charCodeAt(i) + ((hash << 5) - hash);
    }
    
    const colors = [
      '#3498db', '#2ecc71', '#e74c3c', '#f39c12', '#9b59b6',
      '#1abc9c', '#d35400', '#c0392b', '#8e44ad', '#16a085'
    ];
    
    return colors[Math.abs(hash) % colors.length];
  };

  if (error || !logo) {
    const bgColor = createColorFromString(ticker);
    return (
      <div 
        className="w-10 h-10 rounded-full flex items-center justify-center text-white font-bold"
        style={{ backgroundColor: bgColor }}
      >
        {ticker.substring(0, 2)}
      </div>
    );
  }

  return (
    <img 
      src={logo} 
      alt={`${name} logo`} 
      className="w-10 h-10 rounded-full object-contain bg-white p-1"
      onError={() => setError(true)}
    />
  );
};

const EnhancedResultsTable = ({ companies, onSelect, selectedCompanies }) => {
  if (!companies || companies.length === 0) {
    return (
      <div className="bg-nav rounded-lg shadow-xl p-6 text-center">
        <p className="text-gray-400">No companies match your criteria. Try adjusting your filters.</p>
      </div>
    );
  }

  // Add mock data for demo purpose to show the full UI
  // In a real implementation, this data would come from your API
  const enhancedCompanies = companies.map(company => ({
    ...company,
    price: Math.floor(Math.random() * 20000) / 100,
    valuation: `${(Math.random() * 70).toFixed(1)}% ${Math.random() > 0.5 ? 'undervalued' : 'overvalued'}`,
    sevenDayReturn: (Math.random() * 10 - 5).toFixed(1),
    totalReturn: (Math.random() * 100 - 20).toFixed(1),
    valueCost: `US$${Math.floor(Math.random() * 50000)}`,
    cost: `US$${Math.floor(Math.random() * 20000)}`,
    positive: Math.random() > 0.3
  }));

  return (
    <div className="bg-[#1a1d26] rounded-lg shadow-xl overflow-hidden mb-6">
      {/* Table header */}
      <div className="grid grid-cols-7 text-gray-400 text-xs font-medium uppercase tracking-wider border-b border-gray-800">
        <div className="px-6 py-3 col-span-2">Symbol</div>
        <div className="px-4 py-3">Price Vs Fair Value</div>
        <div className="px-4 py-3">7D Return</div>
        <div className="px-4 py-3">Total Return</div>
        <div className="px-4 py-3">Value & Cost</div>
        <div className="px-4 py-3">1Y Chart</div>
      </div>
      
      {/* Table body */}
      <div className="divide-y divide-gray-800">
        {enhancedCompanies.map((company) => (
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
              <div className="text-white">US${company.price}</div>
              <ValueIndicator value={company.valuation} />
            </div>
            
            <div className="px-4 py-5 flex flex-col justify-center">
              <ReturnIndicator value={company.sevenDayReturn} />
              <div className="text-gray-400 text-sm">+US${(Math.random() * 200).toFixed(0)}</div>
            </div>
            
            <div className="px-4 py-5 flex flex-col justify-center">
              <ReturnIndicator value={company.totalReturn} />
              <div className="text-gray-400 text-sm">+US${(Math.random() * 10000).toFixed(0)}</div>
            </div>
            
            <div className="px-4 py-5 flex flex-col justify-center">
              <div className="text-white">{company.valueCost}</div>
              <div className="text-gray-400">{company.cost}</div>
            </div>
            
            <div className="px-4 py-5 flex items-center">
              <MiniChart positive={company.positive} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default EnhancedResultsTable;