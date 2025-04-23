import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import AuthButton from "../component/AuthButton";

const CompanyDetail = () => {
  const { ticker } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [company, setCompany] = useState(null);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState("main-ratios");
  const API_BASE_URL = "http://192.168.64.2:5000";
  
  // Fetch company details from your existing API endpoints
  useEffect(() => {
    const fetchCompanyData = async () => {
      if (!ticker) return;
      
      setLoading(true);
      setError(null);
      
      try {
        console.log(`Fetching details for: ${ticker}`);
        
        // Get fundamental metrics
        const metricsUrl = `${API_BASE_URL}/fundamentals/key_metrics?ticker=${ticker}`;
        const metricsResponse = await fetch(metricsUrl);
        
        if (!metricsResponse.ok) {
          throw new Error(`API returned status ${metricsResponse.status}`);
        }
        
        const metricsData = await metricsResponse.json();
        console.log("Metrics data:", metricsData);
        
        // Get ranking data which includes health, valuation, growth scores
        const rankUrl = `${API_BASE_URL}/api/rank?goal=value&risk=moderate&sector=Technology`;
        const rankResponse = await fetch(rankUrl);
        const rankData = await rankResponse.json();
        
        // Find this company in the ranked companies
        let companyDetails = null;
        if (rankData.companies) {
          companyDetails = rankData.companies.find(c => c.ticker === ticker);
        }
        
        console.log("Company details from rank:", companyDetails);
        
        // Combine the data
        setCompany({
          ticker: ticker,
          // Use data from ranking API if available, otherwise use fallbacks
          company_name: companyDetails?.company_name || ticker,
          sector: companyDetails?.sector || "Technology",
          website: companyDetails?.website || null,
          market_cap: companyDetails?.market_cap || null,
          market_cap_formatted: companyDetails?.market_cap_formatted || null,
          current_price: companyDetails?.current_price || null,
          
          // Financial metrics from the fundamental endpoint
          pe: metricsData?.pe || null,
          sector_pe: metricsData?.sector_pe || null,
          peg: metricsData?.peg || null,
          ps: metricsData?.ps || null,
          roe: metricsData?.roe || null,
          debtRatio: metricsData?.debtRatio || null,
          enterpriseValue: metricsData?.enterpriseValue || null,
          freeCashFlowYield: metricsData?.freeCashFlowYield || null,
          revenueGrowth: metricsData?.revenueGrowth || null,
          epsGrowth: metricsData?.epsGrowth || null,
          
          // Scores from the ranking system
          valuation_score: companyDetails?.valuation_score || null,
          growth_score: companyDetails?.growth_score || null,
          health_score: companyDetails?.health_score || null,
          overall_score: companyDetails?.overall_score || null,
          
          // Additional metrics from ranking API if available
          pe_ratio: companyDetails?.pe_ratio || null,
          dividend_yield: companyDetails?.dividend_yield || null,
          payout_ratio: companyDetails?.payout_ratio || null,
          debt_equity_ratio: companyDetails?.debt_equity_ratio || null,
          current_ratio: companyDetails?.current_ratio || null,
          ocf_growth: companyDetails?.ocf_growth || null,
          earnings_growth: companyDetails?.earnings_growth || null,
          revenue_growth: companyDetails?.revenue_growth || null,
          ev_ebitda: companyDetails?.ev_ebitda || null,
        });
      } catch (error) {
        console.error("Error fetching company data:", error);
        setError(`Error fetching data: ${error.message}`);
      } finally {
        setLoading(false);
      }
    };
    
    fetchCompanyData();
  }, [ticker, API_BASE_URL]);
  
  // Format a number as a percentage
  const formatPercent = (value) => {
    if (value === null || value === undefined) return 'N/A';
    return `${(value * 100).toFixed(2)}%`;
  };
  
  // Format currency values
  const formatCurrency = (value) => {
    if (value === null || value === undefined) return 'N/A';
    return `$${value.toFixed(2)}`;
  };
  
  // Format large numbers (like enterprise value)
  const formatLargeNumber = (value) => {
    if (value === null || value === undefined) return 'N/A';
    
    if (value >= 1e12) {
      return `$${(value / 1e12).toFixed(2)}T`;
    } else if (value >= 1e9) {
      return `$${(value / 1e9).toFixed(2)}B`;
    } else if (value >= 1e6) {
      return `$${(value / 1e6).toFixed(2)}M`;
    } else {
      return `$${value.toLocaleString()}`;
    }
  };
  
  // Navigation tabs
  const tabs = [
    { id: "main-ratios", label: "Main Ratios" },
    { id: "valuation", label: "Valuation" },
    { id: "historical", label: "Historical" },
    { id: "business", label: "Business" },
    { id: "financials", label: "Financials" }
  ];
  
  return (
    <div className="min-h-screen bg-background text-gray-100">
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Back Button */}
        <div className="mb-6">
          <AuthButton
            type="button"
            className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
            onClick={() => navigate(-1)}
          >
            ← Back to Screener
          </AuthButton>
        </div>
        
        {/* Error State */}
        {error && (
          <div className="bg-red-900 text-white p-4 rounded-lg mb-6">
            <h3 className="text-lg font-semibold mb-2">Error:</h3>
            <p>{error}</p>
          </div>
        )}
        
        {/* Loading State */}
        {loading && (
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin h-12 w-12 border-t-2 border-b-2 border-blue-500 rounded-full"></div>
          </div>
        )}
        
        {/* Company Details */}
        {!loading && company && (
          <>
            {/* Company Header */}
            <div className="bg-nav rounded-lg shadow-xl p-6 mb-6">
              <div className="flex flex-col md:flex-row justify-between items-start md:items-center">
                <div>
                  <h1 className="text-3xl font-bold">{ticker}</h1>
                  <p className="text-xl text-gray-400">{company.company_name}</p>
                  {company.sector && (
                    <span className="inline-block bg-gray-700 text-gray-300 px-3 py-1 rounded-full text-sm mt-2">
                      {company.sector}
                    </span>
                  )}
                </div>
                <div className="mt-4 md:mt-0 flex flex-col md:items-end">
                  {company.current_price && (
                    <span className="text-2xl font-bold">${company.current_price.toFixed(2)}</span>
                  )}
                  {company.market_cap_formatted && (
                    <span className="text-sm text-gray-400">
                      Market Cap: {company.market_cap_formatted}
                    </span>
                  )}
                  {company.website && (
                    <a 
                      href={company.website} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="text-blue-400 hover:text-blue-300 transition-colors mt-2"
                    >
                      {company.website} 
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 inline ml-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                      </svg>
                    </a>
                  )}
                </div>
              </div>
            </div>
            
            {/* Score Summary Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
              {/* Overall Score */}
              <div className="bg-nav rounded-lg shadow-xl p-4">
                <h3 className="text-sm text-gray-400 mb-1">Overall Score</h3>
                <div className="flex items-center">
                  <div className={`w-16 h-16 rounded-full flex items-center justify-center text-white font-bold ${
                    company.overall_score >= 4 ? 'bg-green-600' :
                    company.overall_score >= 3 ? 'bg-blue-600' :
                    company.overall_score >= 2 ? 'bg-yellow-600' : 'bg-red-600'
                  }`}>
                    {company.overall_score ? company.overall_score.toFixed(1) : 'N/A'}
                  </div>
                  <div className="ml-4">
                    <p className="text-sm text-gray-300">
                      {company.overall_score >= 4 ? 'Excellent' :
                       company.overall_score >= 3 ? 'Good' :
                       company.overall_score >= 2 ? 'Fair' : 'Poor'}
                    </p>
                    <p className="text-xs text-gray-400">
                      Composite Rating
                    </p>
                  </div>
                </div>
              </div>
              
              {/* Valuation Score */}
              <div className="bg-nav rounded-lg shadow-xl p-4">
                <h3 className="text-sm text-gray-400 mb-1">Valuation Score</h3>
                <div className="flex items-center">
                  <div className={`w-16 h-16 rounded-full flex items-center justify-center text-white font-bold ${
                    company.valuation_score >= 4 ? 'bg-green-600' :
                    company.valuation_score >= 3 ? 'bg-blue-600' :
                    company.valuation_score >= 2 ? 'bg-yellow-600' : 'bg-red-600'
                  }`}>
                    {company.valuation_score ? company.valuation_score.toFixed(1) : 'N/A'}
                  </div>
                  <div className="ml-4">
                    <p className="text-sm text-gray-300">Price Attractiveness</p>
                    <p className="text-xs text-gray-400">
                      Based on P/E, PEG, EV/EBITDA
                    </p>
                  </div>
                </div>
              </div>
              
              {/* Growth Score */}
              <div className="bg-nav rounded-lg shadow-xl p-4">
                <h3 className="text-sm text-gray-400 mb-1">Growth Score</h3>
                <div className="flex items-center">
                  <div className={`w-16 h-16 rounded-full flex items-center justify-center text-white font-bold ${
                    company.growth_score >= 4 ? 'bg-green-600' :
                    company.growth_score >= 3 ? 'bg-blue-600' :
                    company.growth_score >= 2 ? 'bg-yellow-600' : 'bg-red-600'
                  }`}>
                    {company.growth_score ? company.growth_score.toFixed(1) : 'N/A'}
                  </div>
                  <div className="ml-4">
                    <p className="text-sm text-gray-300">Growth Potential</p>
                    <p className="text-xs text-gray-400">
                      Revenue, Earnings, Cash Flow
                    </p>
                  </div>
                </div>
              </div>
              
              {/* Health Score */}
              <div className="bg-nav rounded-lg shadow-xl p-4">
                <h3 className="text-sm text-gray-400 mb-1">Health Score</h3>
                <div className="flex items-center">
                  <div className={`w-16 h-16 rounded-full flex items-center justify-center text-white font-bold ${
                    company.health_score >= 4 ? 'bg-green-600' :
                    company.health_score >= 3 ? 'bg-blue-600' :
                    company.health_score >= 2 ? 'bg-yellow-600' : 'bg-red-600'
                  }`}>
                    {company.health_score ? company.health_score.toFixed(1) : 'N/A'}
                  </div>
                  <div className="ml-4">
                    <p className="text-sm text-gray-300">Financial Strength</p>
                    <p className="text-xs text-gray-400">
                      Debt, Liquidity, FCF
                    </p>
                  </div>
                </div>
              </div>
            </div>
            
            {/* Navigation Tabs */}
            <div className="mb-6 border-b border-gray-600">
              <nav className="flex space-x-2 overflow-x-auto">
                {tabs.map(tab => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`py-3 px-4 font-medium text-sm whitespace-nowrap ${
                      activeTab === tab.id
                        ? 'text-blue-400 border-b-2 border-blue-400'
                        : 'text-gray-400 hover:text-gray-300'
                    }`}
                  >
                    {tab.label}
                  </button>
                ))}
              </nav>
            </div>
            
            {/* Main Ratios Section */}
            {activeTab === 'main-ratios' && (
              <div className="bg-nav rounded-lg shadow-xl p-6 mb-6">
                <h2 className="text-xl font-semibold mb-6">Main Ratios</h2>
                
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                  {/* Valuation Metrics */}
                  <div>
                    <h3 className="text-lg font-semibold mb-4 text-gray-300">Valuation</h3>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-400">P/E Ratio</span>
                        <span className="text-sm font-medium">
                          {company.pe_ratio ? company.pe_ratio.toFixed(2) : 'N/A'}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-400">P/B Ratio</span>
                        <span className="text-sm font-medium">N/A</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-400">P/S Ratio</span>
                        <span className="text-sm font-medium">
                          {company.ps ? company.ps.toFixed(2) : 'N/A'}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-400">P/FCF Ratio</span>
                        <span className="text-sm font-medium">N/A</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-400">EV/EBITDA</span>
                        <span className="text-sm font-medium">
                          {company.ev_ebitda ? company.ev_ebitda.toFixed(2) : 'N/A'}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-400">PEG Ratio</span>
                        <span className="text-sm font-medium">
                          {company.peg ? company.peg.toFixed(2) : 'N/A'}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-400">Dividend Yield</span>
                        <span className="text-sm font-medium">
                          {company.dividend_yield ? formatPercent(company.dividend_yield) : '0%'}
                        </span>
                      </div>
                    </div>
                  </div>
                  
                  {/* Solvency Metrics */}
                  <div>
                    <h3 className="text-lg font-semibold mb-4 text-gray-300">Solvency</h3>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-400">Debt/Equity</span>
                        <span className="text-sm font-medium">
                          {company.debt_equity_ratio ? company.debt_equity_ratio.toFixed(2) : 'N/A'}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-400">Interest Coverage</span>
                        <span className="text-sm font-medium">N/A</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-400">Cashflow/Debt</span>
                        <span className="text-sm font-medium">N/A</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-400">Debt Ratio</span>
                        <span className="text-sm font-medium">
                          {company.debtRatio ? company.debtRatio.toFixed(2) : 'N/A'}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-400">Long Term Debt/Cap</span>
                        <span className="text-sm font-medium">N/A</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-400">Current Ratio</span>
                        <span className="text-sm font-medium">
                          {company.current_ratio ? company.current_ratio.toFixed(2) : 'N/A'}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-400">Cash Ratio</span>
                        <span className="text-sm font-medium">N/A</span>
                      </div>
                    </div>
                  </div>
                  
                  {/* Efficiency Metrics */}
                  <div>
                    <h3 className="text-lg font-semibold mb-4 text-gray-300">Efficiency</h3>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-400">Return on Equity</span>
                        <span className="text-sm font-medium">
                          {company.roe ? formatPercent(company.roe) : 'N/A'}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-400">Return on Capital</span>
                        <span className="text-sm font-medium">N/A</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-400">Gross Margin</span>
                        <span className="text-sm font-medium">N/A</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-400">Net Profit Margin</span>
                        <span className="text-sm font-medium">N/A</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-400">Asset Turnover</span>
                        <span className="text-sm font-medium">N/A</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-400">Inventory Turnover</span>
                        <span className="text-sm font-medium">N/A</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-400">Receivables Turnover</span>
                        <span className="text-sm font-medium">N/A</span>
                      </div>
                    </div>
                  </div>
                  
                  {/* Growth Metrics */}
                  <div>
                    <h3 className="text-lg font-semibold mb-4 text-gray-300">Growth</h3>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-400">Revenue Growth (1Y)</span>
                        <span className="text-sm font-medium">
                          {company.revenue_growth ? formatPercent(company.revenue_growth) : 'N/A'}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-400">Net Income Growth (1Y)</span>
                        <span className="text-sm font-medium">
                          {company.earnings_growth ? formatPercent(company.earnings_growth) : 'N/A'}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-400">Revenue Growth (5Y)</span>
                        <span className="text-sm font-medium">N/A</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-400">Net Income Growth (5Y)</span>
                        <span className="text-sm font-medium">N/A</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-400">OCF Growth (1Y)</span>
                        <span className="text-sm font-medium">
                          {company.ocf_growth ? formatPercent(company.ocf_growth) : 'N/A'}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-400">Expected Growth (Q)</span>
                        <span className="text-sm font-medium">N/A</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-400">Expected Growth (Y)</span>
                        <span className="text-sm font-medium">N/A</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
            
            {/* Valuation Analysis Section */}
            {activeTab === 'valuation' && (
              <div className="bg-nav rounded-lg shadow-xl p-6 mb-6">
                <h2 className="text-xl font-semibold mb-6">Valuation Analysis</h2>
                
                <div className="mb-8">
                  <h3 className="text-lg font-medium mb-4">Historical Valuation</h3>
                  <div className="bg-gray-800 rounded-lg p-6 h-72 flex items-center justify-center">
                    <iframe 
                      src={`${API_BASE_URL}/api/charts/pe_history?ticker=${ticker}`} 
                      className="w-full h-full rounded border-0"
                      title="PE History Chart"
                    />
                  </div>
                </div>
                
                <div className="mb-8">
                  <h3 className="text-lg font-medium mb-4">Peer Comparison</h3>
                  <div className="bg-gray-800 rounded-lg p-6 h-72 flex items-center justify-center">
                    <iframe 
                      src={`${API_BASE_URL}/api/charts/peer_comparison?ticker=${ticker}`} 
                      className="w-full h-full rounded border-0"
                      title="Peer Comparison Chart"
                    />
                  </div>
                </div>
                
                <div>
                  <h3 className="text-lg font-medium mb-4">Intrinsic Value Analysis</h3>
                  <div className="bg-gray-800 rounded-lg p-6 h-72 flex items-center justify-center">
                    <iframe 
                      src={`${API_BASE_URL}/api/charts/dcf_valuation?ticker=${ticker}`} 
                      className="w-full h-full rounded border-0"
                      title="DCF Valuation Chart"
                    />
                  </div>
                </div>
              </div>
            )}
            
            {/* Historical Performance Section */}
            {activeTab === 'historical' && (
              <div className="bg-nav rounded-lg shadow-xl p-6 mb-6">
                <h2 className="text-xl font-semibold mb-6">Historical Performance</h2>
                
                <div className="mb-8">
                  <h3 className="text-lg font-medium mb-4">Revenue & Earnings Growth</h3>
                  <div className="bg-gray-800 rounded-lg p-6 h-72 flex items-center justify-center">
                    <iframe 
                      src={`${API_BASE_URL}/api/charts/growth_history?ticker=${ticker}`} 
                      className="w-full h-full rounded border-0"
                      title="Growth History Chart"
                    />
                  </div>
                </div>
                
                <div>
                  <h3 className="text-lg font-medium mb-4">Free Cash Flow Yield</h3>
                  <div className="bg-gray-800 rounded-lg p-6 h-72 flex items-center justify-center">
                    <iframe 
                      src={`${API_BASE_URL}/api/charts/fcf_yield?ticker=${ticker}`} 
                      className="w-full h-full rounded border-0"
                      title="FCF Yield Chart"
                    />
                  </div>
                </div>
              </div>
            )}
            
            {/* Business Overview Section */}
            {activeTab === 'business' && (
              <div className="bg-nav rounded-lg shadow-xl p-6 mb-6">
                <h2 className="text-xl font-semibold mb-6">Business Overview</h2>
                
                {/* Basic placeholder for business description */}
                <div className="mb-8">
                  <h3 className="text-lg font-medium mb-4">Company Description</h3>
                  <div className="bg-gray-800 rounded-lg p-6">
                    <p className="text-gray-300">
                      Detailed business information will be available here. In the meantime, you can visit the company's website for more information.
                    </p>
                    {company.website && (
                      <a 
                        href={company.website} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-blue-400 hover:text-blue-300 transition-colors mt-4 inline-block"
                      >
                        Visit company website
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 inline ml-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                        </svg>
                      </a>
                    )}
                  </div>
                </div>
              </div>
            )}
            
            {/* Financials Section */}
            {activeTab === 'financials' && (
              <div className="bg-nav rounded-lg shadow-xl p-6 mb-6">
                <h2 className="text-xl font-semibold mb-6">Financial Statements</h2>
                
                {/* Placeholder for financial statements */}
                <div className="mb-8">
                  <h3 className="text-lg font-medium mb-4">Income Statement</h3>
                  <div className="bg-gray-800 rounded-lg p-6 h-72 flex items-center justify-center">
                    <iframe 
                      src={`${API_BASE_URL}/api/financials/income?ticker=${ticker}`} 
                      className="w-full h-full rounded border-0"
                      title="Income Statement"
                    />
                  </div>
                </div>
                
                <div className="mb-8">
                  <h3 className="text-lg font-medium mb-4">Balance Sheet</h3>
                  <div className="bg-gray-800 rounded-lg p-6 h-72 flex items-center justify-center">
                    <iframe 
                      src={`${API_BASE_URL}/api/financials/balance?ticker=${ticker}`} 
                      className="w-full h-full rounded border-0"
                      title="Balance Sheet"
                    />
                  </div>
                </div>
                
                <div className="mb-8">
                  <h3 className="text-lg font-medium mb-4">Cash Flow Statement</h3>
                  <div className="bg-gray-800 rounded-lg p-6 h-72 flex items-center justify-center">
                    <iframe 
                      src={`${API_BASE_URL}/api/financials/cashflow?ticker=${ticker}`} 
                      className="w-full h-full rounded border-0"
                      title="Cash Flow Statement"
                    />
                  </div>
                </div>
              </div>
            )}
            
            {/* Data Sources */}
            <div className="bg-nav rounded-lg shadow-xl p-4 text-center text-sm text-gray-400 mt-6">
              Last updated: {new Date().toLocaleDateString()}
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default CompanyDetail;