import { useState, useEffect } from "react";
import AuthButton from "../component/AuthButton";
import axios from "axios";

const Screener = () => {
  // State management
  const [investmentGoal, setInvestmentGoal] = useState("balanced");
  const [riskTolerance, setRiskTolerance] = useState("moderate");
  const [selectedSector, setSelectedSector] = useState("Technology");
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedCompanies, setSelectedCompanies] = useState([]);
  const [comparisonData, setComparisonData] = useState([]);
  const [showComparison, setShowComparison] = useState(false);
  const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' });

  // Investment goals options
  const investmentGoals = [
    { id: "income", label: "Income" },
    { id: "balanced", label: "Balanced" },
    { id: "growth", label: "Growth" }
  ];

  // Risk tolerance options
  const riskTolerances = [
    { id: "conservative", label: "Conservative" },
    { id: "moderate", label: "Moderate" },
    { id: "aggressive", label: "Aggressive" }
  ];

  // Sectors options
  const sectors = [
    "Technology", "Financial Services", "Healthcare", 
    "Consumer Cyclical", "Consumer Defensive", "Energy", 
    "Basic Materials", "Communication Services", 
    "Industrials", "Real Estate", "Utilities"
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

  // Fetch companies based on filters
  const fetchCompanies = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`http://127.0.0.1:5000/api/rank`, {
        params: {
          goal: investmentGoal,
          risk: riskTolerance,
          sector: selectedSector
        }
      });
      
      setCompanies(response.data.companies || []);
    } catch (error) {
      console.error("Error fetching companies:", error);
    } finally {
      setLoading(false);
    }
  };

  // Handle search/filter submission
  const handleSearch = () => {
    setShowComparison(false);
    fetchCompanies();
  };

  // Compare selected companies
  const handleCompare = async () => {
    if (selectedCompanies.length === 0) return;
    
    setLoading(true);
    try {
      // This would be replaced with your actual API endpoint for detailed company data
      const response = await axios.get(`http://127.0.0.1:5000/api/compare`, {
        params: {
          tickers: selectedCompanies.join(',')
        }
      });
      
      setComparisonData(response.data || []);
      setShowComparison(true);
    } catch (error) {
      console.error("Error fetching comparison data:", error);
    } finally {
      setLoading(false);
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

  // Mock data for initial development/testing
  useEffect(() => {
    // This mock data can be removed once your API is connected
    if (companies.length === 0 && !loading) {
      setCompanies([
        { ticker: "AAPL", name: "Apple Inc.", recommendation: "Strengths: consistent growth, strong balance sheet." },
        { ticker: "MSFT", name: "Microsoft Corporation", recommendation: "Overall profile appears neutral based on key metrics." },
        { ticker: "GOOG", name: "Alphabet Inc.", recommendation: "Cautions: high P/E ratio (28.5)." },
        { ticker: "AMZN", name: "Amazon.com Inc.", recommendation: "Strengths: revenue growth, market leader position." },
        { ticker: "NVDA", name: "NVIDIA Corporation", recommendation: "Cautions: volatility, high valuation multiples." }
      ]);
    }
  }, []);

  return (
    <div className="min-h-screen bg-background text-gray-100">
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Page Title */}
        <h1 className="text-3xl md:text-4xl font-bold mb-8 text-center">
          Stock Screener
        </h1>

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

          {/* Sectors */}
          <div className="mt-6">
            <h2 className="text-xl font-semibold mb-4">Sector</h2>
            <div className="flex flex-wrap gap-3">
              {sectors.map((sector) => (
                <button
                  key={sector}
                  onClick={() => handleSectorSelect(sector)}
                  className={`py-2 px-4 rounded-lg transition-colors ${
                    selectedSector === sector
                      ? "bg-blue-600 text-white"
                      : "bg-gray-700 hover:bg-gray-600"
                  }`}
                >
                  {sector}
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
            >
              Find Companies
            </AuthButton>
          </div>
        </div>

        {/* Results Section */}
        {loading ? (
          <div className="flex justify-center my-12">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
          </div>
        ) : (
          <>
            {/* Company Results Table */}
            {!showComparison && companies.length > 0 && (
              <div className="bg-nav rounded-lg shadow-xl p-6 mb-8">
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-2xl font-semibold">
                    Companies ({companies.length})
                  </h2>
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
                </div>

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
              </div>
            )}

            {/* Comparison Table */}
            {showComparison && (
              <div className="bg-nav rounded-lg shadow-xl p-6">
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-2xl font-semibold">
                    Comparison ({selectedCompanies.length})
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
                              {company[column]}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* No Results Message */}
            {!loading && companies.length === 0 && !showComparison && (
              <div className="bg-nav rounded-lg shadow-xl p-12 text-center">
                <h3 className="text-xl font-medium text-gray-300 mb-4">
                  No companies match your criteria
                </h3>
                <p className="text-gray-400">
                  Try adjusting your filters or selecting a different sector.
                </p>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default Screener;