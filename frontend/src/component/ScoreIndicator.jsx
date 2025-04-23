import { useState, useEffect, useRef } from "react";

// Score indicator that shows the score with appropriate color
// going to create some filled bars 
const ScoreIndicator = ({ score, label, className }) => {
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
    <div className={`p-3 rounded-lg ${className || 'bg-gray-800 bg-opacity-30'}`}>
      <div className="text-sm text-gray-400 mb-1">{label}</div>
      <div className={`text-xl font-medium ${getColor()}`}>
        {numScore.toFixed(1)}
      </div>
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

// Score-based results table (enhanced with sorting)
const ScoreResultsView = ({ companies, onSelect, selectedCompanies, maxResults = 20 }) => {
  // State for sorting
  const [sortBy, setSortBy] = useState('overall_score');
  const [sortDirection, setSortDirection] = useState('desc');
  
  if (!companies || companies.length === 0) {
    return (
      <div className="bg-[#1a1d26] rounded-lg shadow-xl p-6 text-center">
        <p className="text-gray-400">No companies match your criteria. Try adjusting your filters.</p>
      </div>
    );
  }
  
  // Sort companies based on current sort criteria
  const sortedCompanies = [...companies].sort((a, b) => {
    const valueA = parseFloat(a[sortBy]) || 0;
    const valueB = parseFloat(b[sortBy]) || 0;
    
    if (sortDirection === 'asc') {
      return valueA - valueB;
    } else {
      return valueB - valueA;
    }
  });
  
  // Take top results based on maxResults
  const displayCompanies = sortedCompanies.slice(0, maxResults);
  
  // Function to handle sort change
  const handleSort = (column) => {
    if (sortBy === column) {
      // If same column, toggle direction
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      // If new column, set it and default to descending (higher scores first)
      setSortBy(column);
      setSortDirection('desc');
    }
  };
  
  return (
    <div className="bg-[#1a1d26] rounded-lg shadow-xl overflow-hidden">
      {/* Sorting controls */}
      <div className="p-4 border-b border-gray-800">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div className="flex flex-wrap space-x-2 text-sm">
            <span className="text-gray-400">Sort by:</span>
            {[
              { id: 'valuation_score', label: 'Valuation' },
              { id: 'health_score', label: 'Health' },
              { id: 'growth_score', label: 'Growth' },
              { id: 'overall_score', label: 'Overall' }
            ].map(option => (
              <button
                key={option.id}
                className={`px-3 py-1 rounded ${
                  sortBy === option.id
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
                onClick={() => handleSort(option.id)}
              >
                {option.label}
                {sortBy === option.id && (
                  <span className="ml-1">
                    {sortDirection === 'asc' ? '↑' : '↓'}
                  </span>
                )}
              </button>
            ))}
          </div>
          
          <div className="text-sm text-gray-400">
            Showing top {displayCompanies.length} of {companies.length} companies
          </div>
        </div>
      </div>
      
      {/* Company list with scores */}
      <div className="divide-y divide-gray-800">
        {displayCompanies.map((company) => (
          <div 
            key={company.ticker} 
            className={`p-4 ${
              selectedCompanies.includes(company.ticker) ? 'bg-gray-800' : 'hover:bg-gray-800'
            } transition-colors cursor-pointer`}
            onClick={() => onSelect(company.ticker)}
          >
            <div className="flex items-start">
              {/* Checkbox */}
              <div className="mr-3 mt-2">
                <input
                  type="checkbox"
                  className="h-5 w-5 rounded border-gray-600 text-blue-600 focus:ring-blue-500"
                  checked={selectedCompanies.includes(company.ticker)}
                  onChange={(e) => {
                    e.stopPropagation();
                    onSelect(company.ticker);
                  }}
                />
              </div>
              
              {/* Company info and logo */}
              <div className="mr-4">
                <CompanyLogo ticker={company.ticker} name={company.name} />
              </div>
              
              <div className="flex-grow">
                <div className="flex flex-col mb-4">
                  <span className="text-lg font-medium text-white">{company.name}</span>
                  <div className="flex flex-wrap space-x-4 text-sm text-gray-400">
                    <span>{company.ticker}</span>
                    <span>{company.sector}</span>
                    <span>{company.market_cap}</span>
                  </div>
                </div>
                
                {/* Score indicators */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  <ScoreIndicator 
                    score={company.valuation_score} 
                    label="Valuation" 
                  />
                  <ScoreIndicator 
                    score={company.health_score} 
                    label="Health" 
                  />
                  <ScoreIndicator 
                    score={company.growth_score} 
                    label="Growth" 
                  />
                  <ScoreIndicator 
                    score={company.overall_score} 
                    label="Overall" 
                    className="bg-blue-900 bg-opacity-20"
                  />
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ScoreIndicator;