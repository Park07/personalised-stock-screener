import { useState, useRef, useEffect, useCallback } from "react";
import AuthButton from "../component/AuthButton";
import ScoreResultsView from "../component/ScoreResultsView";
import { GoalExplanation, RiskExplanation } from "../component/InvestmentExplanation";

const Screener = () => {
  // State management
  const [investmentGoal, setInvestmentGoal] = useState("value");
  const [riskTolerance, setRiskTolerance] = useState("moderate");
  const [selectedSector, setSelectedSector] = useState("Technology");
  const [companies, setCompanies] = useState([]);
  const [hasSearched, setHasSearched] = useState(false);
  const [loading, setLoading] = useState(false);
  const [selectedCompanies, setSelectedCompanies] = useState([]);
  const [comparisonData, setComparisonData] = useState([]);
  const [showComparison, setShowComparison] = useState(false);
  const [apiError, setApiError] = useState(null);

  // Ref to maintain scroll position
  const resultsRef = useRef(null);
  const API_BASE_URL = "http://192.168.64.2:5000";

  // Simple alert info (would be more dynamic in a real app)
  const alertInfo = {
    title: "Market Update",
    message: "S&P 500 up 1.2% today. Technology sector continues to outperform.",
    type: "info"
  };

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

  // Fetch companies with useCallback to create a stable function reference
  const fetchCompanies = useCallback(async (isRecalculation = false) => {
    // Store current scroll position
    const scrollPosition = window.scrollY;
    
    setLoading(true);
    setApiError(null);
    
    // Only clear selections if this is a new search, not a recalculation
    if (!isRecalculation) {
      setSelectedCompanies([]);
      setShowComparison(false);
    }
    
    try {
      // Build URL with selected parameters - using dynamic API_BASE_URL
      const url = `${API_BASE_URL}/api/rank?goal=${investmentGoal}&risk=${riskTolerance}&sector=${encodeURIComponent(selectedSector)}`;
      
      console.log("Fetching from URL:", url); // For debugging
      
      // Use fetch directly with timeout protection
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout
      
      const response = await fetch(url, { 
        signal: controller.signal,
        headers: {
          'Accept': 'application/json'
        }
      });
      clearTimeout(timeoutId);
      
      if (!response.ok) {
        throw new Error(`API returned status ${response.status}`);
      }
      
      // Check if response is actually JSON
      const contentType = response.headers.get("content-type");
      if (!contentType || !contentType.includes("application/json")) {
        throw new Error("Received non-JSON response from server");
      }
      
      const data = await response.json();
      
      if (data && data.companies) {
        // Use the companies data directly from API
        setCompanies(data.companies);
        setHasSearched(true);
      } else {
        setCompanies([]);
        setHasSearched(true);
      }
    } catch (error) {
      console.error("Error fetching companies:", error);
      setApiError(`Error connecting to API: ${error.message}`);
    } finally {
      setLoading(false);
      
      // Restore scroll position after a short delay to let the UI update
      setTimeout(() => {
        window.scrollTo(0, scrollPosition);
      }, 100);
    }
  }, [investmentGoal, riskTolerance, selectedSector, API_BASE_URL]); // Dependencies for useCallback

  // Effect to automatically refetch when investment goal or risk tolerance changes
  useEffect(() => {
    // Only refetch if there are already results to update
    if (hasSearched) {
      console.log(`Profile changed: ${investmentGoal}, ${riskTolerance}. Refetching...`);
      fetchCompanies(true); // true = isRecalculation (don't clear selections)
    }
  }, [fetchCompanies, hasSearched]); // React to changes in fetchCompanies (which depends on goal/risk)

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

  // Handle search/filter submission - initial search
  const handleSearch = () => {
    fetchCompanies(false); // This is a new search, not a recalculation
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
      const url = `${API_BASE_URL}/api/compare?tickers=${tickersParam}`;
      
      console.log("Comparing companies using URL:", url);
      
      const response = await fetch(url, {
        headers: {
          'Accept': 'application/json'
        }
      });
      
      if (!response.ok) {
        throw new Error(`API returned status ${response.status}`);
      }
      
      const contentType = response.headers.get("content-type");
      if (!contentType || !contentType.includes("application/json")) {
        throw new Error("Received non-JSON response from server");
      }
      
      const data = await response.json();
      
      // Handle different API response formats
      if (data.companies) {
        setComparisonData(data.companies);
      } else if (Array.isArray(data)) {
        setComparisonData(data);
      } else {
        setComparisonData([]);
      }
      
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

  // Simple alert banner
  const AlertBanner = ({ title, message, type }) => {
    const getBgColor = () => {
      switch(type) {
        case 'info': return 'bg-blue-900';
        case 'warning': return 'bg-amber-900';
        case 'success': return 'bg-green-900';
        case 'error': return 'bg-red-900';
        default: return 'bg-gray-900';
      }
    };
    
    return (
      <div className={`rounded-lg px-4 py-3 mb-4 shadow-lg ${getBgColor()}`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            {type === 'info' && (
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-5 h-5 mr-2 text-blue-400">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="12" y1="16" x2="12" y2="12"></line>
                <line x1="12" y1="8" x2="12.01" y2="8"></line>
              </svg>
            )}
            <span className="font-semibold">{title}</span>
          </div>
          <span className="text-sm text-gray-300">{message}</span>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-background text-gray-100">
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Alert Banner */}
        <AlertBanner title={alertInfo.title} message={alertInfo.message} type={alertInfo.type} />
        
        {/* Page Title */}
        <h1 className="text-3xl md:text-4xl font-bold mb-8 text-center">
          <span className="border-b-2 border-blue-500 pb-2">Stock Screener</span>
        </h1>
        
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
              <GoalExplanation />
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
              <RiskExplanation />
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
          {/* Score-based Results View - Only show after search */}
          {hasSearched && !showComparison && !loading && (
            <div className="mb-8">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-2xl font-semibold">
                  {companies.length > 0 ? `Results (${companies.length})` : "No Results"}
                </h2>
                {companies.length > 0 && selectedCompanies.length > 0 && (
                  <AuthButton
                    type="button"
                    className="px-6 py-2 bg-green-600 hover:bg-green-700 rounded-lg transition-colors"
                    onClick={handleCompare}
                  >
                    Compare ({selectedCompanies.length})
                  </AuthButton>
                )}
              </div>

              <ScoreResultsView 
                companies={companies} 
                onSelect={handleCompanySelect}
                selectedCompanies={selectedCompanies}
                maxResults={20} // Show top 20 companies
              />
            </div>
          )}

          {/* Comparison View - Only show after clicking Compare */}
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

              {/* Comparison Chart - This would ideally be a Parallel Coordinates Plot */}
              <div className="h-96 bg-gray-800 rounded-lg p-4 flex items-center justify-center">
                <p className="text-gray-400">
                  Comparison chart would be displayed here. In a real implementation, this would be a 
                  Parallel Coordinates Plot showing the relationships between different metrics.
                </p>
              </div>

              {/* Comparison Table */}
              <div className="mt-6">
                <h3 className="text-xl font-semibold mb-4">Detailed Comparison</h3>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-600">
                    <thead className="bg-gray-800">
                      <tr>
                        {['ticker', 'company_name', 'sector', 'market_cap', 'current_price',
                          'pe_ratio', 'ev_ebitda', 'dividend_yield', 'payout_ratio',
                          'debt_equity_ratio', 'current_ratio', 'revenue_growth',
                          'earnings_growth', 'ocf_growth'].map((column) => (
                          <th 
                            key={column}
                            className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider cursor-pointer hover:bg-gray-700 transition-colors"
                          >
                            <div className="flex items-center">
                              <span>{column.replace(/_/g, ' ')}</span>
                            </div>
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="bg-gray-700 divide-y divide-gray-600">
                      {comparisonData.map((company) => (
                        <tr 
                          key={company.ticker} 
                          className="hover:bg-gray-600 transition-colors"
                        >
                          {['ticker', 'company_name', 'sector', 'market_cap', 'current_price',
                            'pe_ratio', 'ev_ebitda', 'dividend_yield', 'payout_ratio',
                            'debt_equity_ratio', 'current_ratio', 'revenue_growth',
                            'earnings_growth', 'ocf_growth'].map((column) => (
                            <td key={`${company.ticker}-${column}`} className="px-4 py-4 whitespace-nowrap">
                              {column === 'market_cap' 
                                ? `$${(Number(company[column]) / 1e9).toFixed(2)}B` 
                                : column === 'current_price'
                                  ? `$${company[column]}`
                                  : (column === 'pe_ratio' || column === 'ev_ebitda' || 
                                     column === 'dividend_yield' || column === 'payout_ratio' || 
                                     column === 'debt_equity_ratio' || column === 'current_ratio' || 
                                     column === 'revenue_growth' || column === 'earnings_growth' || 
                                     column === 'ocf_growth')
                                    ? (typeof company[column] === 'number' 
                                        ? column.includes('growth') || column === 'dividend_yield' || column === 'payout_ratio'
                                          ? `${(company[column] * 100).toFixed(2)}%` 
                                          : company[column].toFixed(2)
                                        : 'N/A')
                                    : company[column] || 'N/A'}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Screener;