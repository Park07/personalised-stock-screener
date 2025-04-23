import React from 'react';
import ScoreIndicator from './ScoreIndicator';
import CompanyLogo from './CompanyLogo';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const ScoreResultsView = ({ companies, onSelect, selectedCompanies, maxResults = 20 }) => {
  // Navigation hook
  const navigate = useNavigate();
  
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
  
  // Navigate to company detail page
  const goToCompanyDetail = (ticker) => {
    navigate(`/company/${ticker}`);
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
            onClick={() => goToCompanyDetail(company.ticker)}
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

export default ScoreResultsView;