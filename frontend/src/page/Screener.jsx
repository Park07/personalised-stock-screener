import { useState, useRef } from "react";
import AuthButton from "../component/AuthButton";

const Screener = () => {
  // State management - Initialize with values that match backend enums
  const [investmentGoal, setInvestmentGoal] = useState("value");
  const [riskTolerance, setRiskTolerance] = useState("moderate");
  const [selectedSector, setSelectedSector] = useState("Technology");
  const [companies, setCompanies] = useState([]);
  const [hasSearched, setHasSearched] = useState(false);
  const [loading, setLoading] = useState(false);
  const [selectedCompanies, setSelectedCompanies] = useState([]);
  const [comparisonData, setComparisonData] = useState([]);
  const [showComparison, setShowComparison] = useState(false);
  const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' });
  const [apiError, setApiError] = useState(null);
  const [debugInfo, setDebugInfo] = useState(null);

  // Ref to maintain scroll position
  const resultsRef = useRef(null);

  // Investment goals options - Updated to match backend enum values
  const investmentGoals = [
    { id: "value", label: "Value" },
    { id: "income", label: "Income" },
    { id: "growth", label: "Growth" }
  ];

  // Risk tolerance options 
  const riskTolerances = [
    { id: "conservative", label: "Conservative" },
    { id: "moderate", label: "Moderate" },
    { id: "aggressive", label: "Aggressive" }
  ];

  // Sectors with SVG icons
  const sectors = [
    { 
      id: "Basic Materials", 
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-6 h-6">
          <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path>
        </svg>
      )
    },
    { 
      id: "Communication Services", 
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-6 h-6">
          <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path>
        </svg>
      )
    },
    { 
      id: "Consumer Cyclical", 
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-6 h-6">
          <circle cx="9" cy="21" r="1"></circle>
          <circle cx="20" cy="21" r="1"></circle>
          <path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"></path>
        </svg>
      )
    },
    { 
      id: "Consumer Defensive", 
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-6 h-6">
          <path d="M20 9v11a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V9"></path>
          <path d="M9 22V12h6v10M2 10.6L12 2l10 8.6"></path>
        </svg>
      )
    },
    { 
      id: "Energy", 
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-6 h-6">
          <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"></path>
        </svg>
      )
    },
    { 
      id: "Financial Services", 
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-6 h-6">
          <rect x="2" y="5" width="20" height="14" rx="2"></rect>
          <line x1="2" y1="10" x2="22" y2="10"></line>
        </svg>
      )
    },
    { 
      id: "Healthcare", 
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-6 h-6">
          <path d="M22 12h-4l-3 9L9 3l-3 9H2"></path>
        </svg>
      )
    },
    { 
      id: "Industrials", 
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-6 h-6">
          <rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect>
          <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path>
        </svg>
      )
    },
    { 
      id: "Real Estate", 
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-6 h-6">
          <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
          <polyline points="9 22 9 12 15 12 15 22"></polyline>
        </svg>
      )
    },
    { 
      id: "Technology", 
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-6 h-6">
          <rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect>
          <line x1="8" y1="21" x2="16" y2="21"></line>
          <line x1="12" y1="17" x2="12" y2="21"></line>
        </svg>
      )
    },
    { 
      id: "Utilities", 
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-6 h-6">
          <path d="M18 16.08c-.76 0-1.44.3-1.96.77L8.91 12.7c.05-.23.09-.46.09-.7s-.04-.47-.09-.7l7.05-4.11c.54.5 1.25.81 2.04.81 1.66 0 3-1.34 3-3s-1.34-3-3-3-3 1.34-3 3c0 .24.04.47.09.7L8.04 9.81C7.5 9.31 6.79 9 6 9c-1.66 0-3 1.34-3 3s1.34 3 3 3c.79 0 1.5-.31 2.04-.81l7.12 4.16c-.05.21-.08.43-.08.65 0 1.61 1.31 2.92 2.92 2.92 1.61 0 2.92-1.31 2.92-2.92s-1.31-2.92-2.92-2.92z"></path>
        </svg>
      )
    }
  ];

  // Handle sector selection
  const handleSectorSelect = (sector) => {
    setSelectedSector(sector);
  };

  // Handle checkbox selection for companies
  const handleCompanySelect = (ticker) => {
    setSelectedCompanies(prevSelected => {
      if (prevSelected.includes(ticker)) {
        return prevSelected.filter(item => item !== ticker);
      } else {
        return [...prevSelected, ticker];
      }
    });
  };

  // Fetch companies based on filters - direct approach
  const fetchCompanies = async () => {
    // Store current scroll position
    const scrollPosition = window.scrollY;
    
    setLoading(true);
    setSelectedCompanies([]);
    setShowComparison(false);
    setApiError(null);
    
    try {
      // Build URL with selected parameters
      const url = `http://192.168.64.2:5000/api/rank?goal=${investmentGoal}&risk=${riskTolerance}&sector=${encodeURIComponent(selectedSector)}`;
      
      // Use fetch directly for simplicity with throttling to prevent too many requests
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout
      
      const response = await fetch(url, { signal: controller.signal });
      clearTimeout(timeoutId);
      
      if (!response.ok) {
        throw new Error(`API returned status ${response.status}`);
      }
      
      const data = await response.json();
      
      if (data && data.companies) {
        setCompanies(data.companies);
        setHasSearched(true);
        setDebugInfo({
          message: "API request successful",
          data: data
        });
      } else {
        setCompanies([]);
        setDebugInfo({
          message: "API returned invalid format",
          data: data
        });
      }
    } catch (error) {
      console.error("Error fetching companies:", error);
      setApiError(`Error connecting to API: ${error.message}`);
      setDebugInfo({
        message: "API request failed",
        error: error.toString()
      });
    } finally {
      setLoading(false);
      
      // Restore scroll position after a short delay to let the UI update
      setTimeout(() => {
        window.scrollTo(0, scrollPosition);
      }, 100);
    }
  };

  // Handle search/filter submission
  const handleSearch = () => {
    fetchCompanies();
  };

  // Compare selected companies
  const handleCompare = async () => {
    if (selectedCompanies.length === 0) return;
    
    // Store current scroll position
    const scrollPosition = window.scrollY;
    
    setLoading(true);
    try {
      // API call to get detailed comparison data
      const tickersParam = selectedCompanies.join(',');
      const url = `http://192.168.64.2:5000/api/compare?tickers=${tickersParam}`;
      
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`API returned status ${response.status}`);
      }
      
      const data = await response.json();
      
      setComparisonData(data || []);
      setShowComparison(true);
    } catch (error) {
      console.error("Error fetching comparison data:", error);
      setApiError(`Error fetching comparison data: ${error.message}`);
    } finally {
      setLoading(false);
      
      // Restore scroll position after a short delay
      setTimeout(() => {
        window.scrollTo(0, scrollPosition);
      }, 100);
    }
  };

  // Handle sorting for comparison table
  const requestSort = (key) => {
    let direction = 'asc';
    if (sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    setSortConfig({ key, direction });
  };

  // Sort comparison data
  const sortedData = () => {
    if (!sortConfig.key || !comparisonData.length) return comparisonData;
    
    return [...comparisonData].sort((a, b) => {
      if (a[sortConfig.key] < b[sortConfig.key]) {
        return sortConfig.direction === 'asc' ? -1 : 1;
      }
      if (a[sortConfig.key] > b[sortConfig.key]) {
        return sortConfig.direction === 'asc' ? 1 : -1;
      }
      return 0;
    });
  };

  // Navigate to company detail
  const navigateToCompanyDetail = (ticker) => {
    // This would be replaced with your actual navigation
    console.log(`Navigating to company detail for ${ticker}`);
    // Example: navigate(`/company/${ticker}`);
  };

  return (
    <div className="min-h-screen bg-background text-gray-100">
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Page Title */}
        <h1 className="text-3xl md:text-4xl font-bold mb-8 text-center">
          <span className="border-b-2 border-blue-500 pb-2">Stock Screener</span>
        </h1>
        
        {/* Debug Panel - Keep hidden in production, only show during development */}
        {debugInfo && process.env.NODE_ENV === 'development' && (
          <div className="mb-4 p-4 bg-gray-800 rounded-lg">
            <h3 className="text-lg font-semibold mb-2">Debug Info:</h3>
            <pre className="text-xs overflow-auto max-h-40">
              {JSON.stringify(debugInfo, null, 2)}
            </pre>
          </div>
        )}

        {/* API Error Display */}
        {apiError && (
          <div className="mb-4 p-4 bg-red-900 text-white rounded-lg">
            <h3 className="text-lg font-semibold mb-2">API Error:</h3>
            <p>{apiError}</p>
          </div>
        )}

        {/* Filters Section */}
        <div className="bg-nav rounded-lg shadow-xl p-6 mb-8">
          <div className="grid md:grid-cols-2 gap-6">
            {/* Investment Goal */}
            <div>
              <h2 className="text-xl font-semibold mb-4">Investment Goal</h2>
              <div className="flex gap-3">
                {investmentGoals.map((goal) => (
                  <button
                    key={goal.id}
                    onClick={() => setInvestmentGoal(goal.id)}
                    className={`flex-1 py-3 px-4 rounded-lg transition-colors ${
                      investmentGoal === goal.id
                        ? "bg-blue-600 text-white"
                        : "bg-gray-700 hover:bg-gray-600"
                    }`}
                  >
                    {goal.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Risk Tolerance */}
            <div>
              <h2 className="text-xl font-semibold mb-4">Risk Tolerance</h2>
              <div className="flex gap-3">
                {riskTolerances.map((risk) => (
                  <button
                    key={risk.id}
                    onClick={() => setRiskTolerance(risk.id)}
                    className={`flex-1 py-3 px-4 rounded-lg transition-colors ${
                      riskTolerance === risk.id
                        ? "bg-blue-600 text-white"
                        : "bg-gray-700 hover:bg-gray-600"
                    }`}
                  >
                    {risk.label}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Sectors - Horizontal with SVG Icons */}
          <div className="mt-6">
            <h2 className="text-xl font-semibold mb-4">Sector</h2>
            <div className="flex flex-wrap gap-3">
              {sectors.map((sector) => (
                <button
                  key={sector.id}
                  onClick={() => handleSectorSelect(sector.id)}
                  className={`flex flex-col items-center py-3 px-4 rounded-lg transition-colors ${
                    selectedSector === sector.id
                      ? "bg-blue-600 text-white"
                      : "bg-gray-700 hover:bg-gray-600"
                  }`}
                >
                  <div className="mb-2">{sector.icon}</div>
                  <span className="text-xs whitespace-nowrap">{sector.id}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Search Button */}
          <div className="mt-6 flex justify-center">
            <AuthButton
              type="button"
              className="px-8 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg text-lg font-semibold transition-colors"
              onClick={handleSearch}
              disabled={loading}
            >
              {loading ? (
                <span className="flex items-center">
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Loading...
                </span>
              ) : (
                "Find Companies"
              )}
            </AuthButton>
          </div>
        </div>

        {/* Results Section */}
        <div ref={resultsRef}>
          {/* Company Results Table - Only show after search */}
          {hasSearched && !showComparison && !loading && (
            <div className="bg-nav rounded-lg shadow-xl p-6 mb-8">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-semibold">
                  {companies.length > 0 ? `Companies (${companies.length})` : "No Results"}
                </h2>
                {companies.length > 0 && (
                  <AuthButton
                    type="button"
                    className={`px-6 py-2 rounded-lg transition-colors ${
                      selectedCompanies.length > 0
                        ? "bg-green-600 hover:bg-green-700"
                        : "bg-gray-600 cursor-not-allowed"
                    }`}
                    onClick={handleCompare}
                    disabled={selectedCompanies.length === 0}
                  >
                    Compare ({selectedCompanies.length})
                  </AuthButton>
                )}
              </div>

              {companies.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-600">
                    <thead className="bg-gray-800">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider w-12">
                          Select
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                          Company
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                          Summary
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-gray-700 divide-y divide-gray-600">
                      {companies.map((company) => (
                        <tr 
                          key={company.ticker} 
                          className="hover:bg-gray-600 cursor-pointer transition-colors"
                          onClick={(e) => {
                            // Don't navigate if clicking on the checkbox
                            if (e.target.type !== 'checkbox') {
                              navigateToCompanyDetail(company.ticker);
                            }
                          }}
                        >
                          <td className="px-6 py-4 whitespace-nowrap">
                            <input
                              type="checkbox"
                              className="h-5 w-5 rounded border-gray-400 text-blue-600 focus:ring-blue-500"
                              checked={selectedCompanies.includes(company.ticker)}
                              onChange={(e) => {
                                e.stopPropagation();
                                handleCompanySelect(company.ticker);
                              }}
                            />
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap font-medium">
                            {company.name} ({company.ticker})
                          </td>
                          <td className="px-6 py-4">
                            {company.recommendation}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="text-center py-8">
                  <p className="text-gray-400">
                    No companies match your criteria. Try adjusting your filters or selecting a different sector.
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Comparison Table - Only show after clicking Compare */}
          {showComparison && comparisonData.length > 0 && !loading && (
            <div className="bg-nav rounded-lg shadow-xl p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-semibold">
                  Comparison ({comparisonData.length})
                </h2>
                <AuthButton
                  type="button"
                  className="px-6 py-2 bg-gray-600 hover:bg-gray-700 rounded-lg transition-colors"
                  onClick={() => setShowComparison(false)}
                >
                  Back to Results
                </AuthButton>
              </div>

              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-600">
                  <thead className="bg-gray-800">
                    <tr>
                      {['ticker', 'company_name', 'sector', 'market_cap', 'current_price',
                        'pe_ratio', 'roe', 'dividend_yield', 'debt_equity_ratio',
                        'revenue_growth', 'earnings_growth'].map((column) => (
                        <th 
                          key={column}
                          className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider cursor-pointer hover:bg-gray-700 transition-colors"
                          onClick={() => requestSort(column)}
                        >
                          <div className="flex items-center space-x-1">
                            <span>{column.replace(/_/g, ' ')}</span>
                            {sortConfig.key === column && (
                              <span>
                                {sortConfig.direction === 'asc' ? '↑' : '↓'}
                              </span>
                            )}
                          </div>
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="bg-gray-700 divide-y divide-gray-600">
                    {sortedData().map((company) => (
                      <tr 
                        key={company.ticker} 
                        className="hover:bg-gray-600 cursor-pointer transition-colors"
                        onClick={() => navigateToCompanyDetail(company.ticker)}
                      >
                        {['ticker', 'company_name', 'sector', 'market_cap', 'current_price',
                          'pe_ratio', 'roe', 'dividend_yield', 'debt_equity_ratio',
                          'revenue_growth', 'earnings_growth'].map((column) => (
                          <td key={`${company.ticker}-${column}`} className="px-4 py-4 whitespace-nowrap">
                            {column === 'market_cap' 
                              ? `$${(Number(company[column]) / 1e9).toFixed(2)}B` 
                              : column === 'current_price'
                                ? `$${company[column]}`
                                : (column === 'pe_ratio' || column === 'roe' || 
                                   column === 'dividend_yield' || column === 'debt_equity_ratio' || 
                                   column === 'revenue_growth' || column === 'earnings_growth')
                                  ? `${company[column]}%`
                                  : company[column]}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Screener;