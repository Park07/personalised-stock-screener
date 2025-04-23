import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import AuthButton from "../component/AuthButton";
import SpiderChart from "../component/SpiderChart";



const CompanyDetail = () => {
  const { ticker } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [company, setCompany] = useState(null);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState("main-ratios");
  const [news, setNews] = useState([]);
  const [newsLoading, setNewsLoading] = useState(false);
  const [newsError, setNewsError] = useState(null);
  const [chartCache, setChartCache] = useState({});
  const [chartLoading, setChartLoading] = useState({});
  const API_BASE_URL = "http://192.168.64.2:5000";

  const IR_OVERRIDE = {
    NVDA: "https://investor.nvidia.com/home/default.aspx",
    MSFT: "https://www.microsoft.com/en-us/investor/default.aspx",
    AAPL: "https://investor.apple.com/investor-relations/default.aspx",
    };

    const investorUrl =
    IR_OVERRIDE[ticker?.toUpperCase()] ||         
    `https://investor.${ticker?.toLowerCase()}.com`; 

    const secUrl = `https://www.sec.gov/cgi-bin/browse-edgar?CIK=${ticker}&owner=exclude&action=getcompany`;

  
  const loadChart = async (chartType, ticker) => {
    const cacheKey = `${chartType}-${ticker}`;
    
    // Return cached chart if available
    if (chartCache[cacheKey]) {
      return chartCache[cacheKey];
    }
    
    // Set loading state for this chart
    setChartLoading(prev => ({ ...prev, [cacheKey]: true }));
    
    try {
      const response = await fetch(`${API_BASE_URL}/${chartType}?ticker=${ticker}`);
      if (!response.ok) {
        throw new Error(`Failed to fetch chart: ${response.status}`);
      }
      
      // Handle the response
      const data = await response.blob();
      const imageUrl = URL.createObjectURL(data);
      
      // Update the cache
      setChartCache(prev => ({ 
        ...prev, 
        [cacheKey]: imageUrl 
      }));
      
      return imageUrl;
    } catch (error) {
      console.error(`Error loading chart ${chartType}:`, error);
      return null;
    } finally {
      setChartLoading(prev => ({ ...prev, [cacheKey]: false }));
    }
  };
  
  // Add this useEffect to preload charts when tab changes
  useEffect(() => {
    const preloadCharts = async () => {
      if (activeTab === 'valuation' && ticker) {
        // Preload valuation charts
        await Promise.all([
          loadChart('fundamentals/pe_chart', ticker),
          loadChart('fundamentals/enhanced_valuation_chart', ticker)
        ]);
      } else if (activeTab === 'historical' && ticker) {
        // Preload historical charts
        await Promise.all([
          loadChart('fundamentals_historical/generate_yearly_performance_chart', ticker),
          loadChart('fundamentals_historical/free_cash_flow_chart', ticker)
        ]);
      }
    };
    
    preloadCharts();
  }, [activeTab, ticker]);

  // Fetch company details from your existing API endpoints
  useEffect(() => {
    const fetchCompanyData = async () => {
      if (!ticker) return;
      
      setLoading(true);
      setError(null);
      
      try {
        console.log(`Fetching details for: ${ticker}`);
        
        // Default sector before we try to determine it
        let companySector = "Technology";
        
        // Get fundamental metrics
        const metricsUrl = `${API_BASE_URL}/fundamentals/key_metrics?ticker=${ticker}`;
        const metricsResponse = await fetch(metricsUrl);
        
        if (!metricsResponse.ok) {
            throw new Error(`API returned status ${metricsResponse.status}`);
        }
        
        const metricsData = await metricsResponse.json();
        console.log("Metrics data:", metricsData);
        
        // Try to get the sector from metrics data if available
        if (metricsData && metricsData.sector) {
            companySector = metricsData.sector;
        }
        
        // Default values (later can be replaced with user preferences)
        const investmentGoal = "value";
        const riskTolerance = "moderate";
        
        // Get ranking data which includes health, valuation, growth scores
        const rankUrl = `${API_BASE_URL}/api/rank?goal=${investmentGoal}&risk=${riskTolerance}`;
        const rankResponse = await fetch(rankUrl);
        const rankData = await rankResponse.json();
        
        // Find this company in the ranked companies
        let companyDetails = null;
        if (rankData.companies) {
            companyDetails = rankData.companies.find(c => c.ticker === ticker);
            
            // If we found company details with a sector, use that
            if (companyDetails && companyDetails.sector) {
            companySector = companyDetails.sector;
            }
        }
      
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
  
  // Fetch company news when ticker changes or news tab is selected
  useEffect(() => {
    const fetchNews = async () => {
      if (!ticker || activeTab !== 'news') return;
      
      setNewsLoading(true);
      setNewsError(null);
      
      try {
        const newsUrl = `${API_BASE_URL}/api/company/news?ticker=${ticker}`;
        const response = await fetch(newsUrl);
        
        if (!response.ok) {
          throw new Error(`Failed to fetch news: ${response.status}`);
        }
        
        const newsData = await response.json();
        setNews(newsData.news || []);
      } catch (error) {
        console.error("Error fetching company news:", error);
        setNewsError(`Failed to load news: ${error.message}`);
      } finally {
        setNewsLoading(false);
      }
    };
    
    fetchNews();
  }, [ticker, activeTab, API_BASE_URL]);
  
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
  
  // Format a date string for news display
  const formatNewsDate = (dateString) => {
    if (!dateString) return '';
    
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
    } catch (e) {
      return dateString;
    }
  };
  
  // Navigation tabs
  const tabs = [
    { id: "main-ratios", label: "Main Ratios" },
    { id: "valuation", label: "Valuation" },
    { id: "historical", label: "Historical" },
    { id: "news", label: "News" },
    { id: "investors", label: "Investors" }
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
                      activeTab === tab.id ? 'block' : 'hidden'
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
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Spider Chart for Overall Scores */}
                  <div className="bg-gray-800 rounded-lg p-4">
                    <h3 className="text-lg font-semibold mb-4 text-center text-gray-300">Company Scores</h3>
                    <div className="h-80">
                      <SpiderChart 
                        scores={{
                          overall_score: company.overall_score || 0,
                          valuation_score: company.valuation_score || 0,
                          growth_score: company.growth_score || 0,
                          health_score: company.health_score || 0
                        }}
                      />
                    </div>
                  </div>
                  
                  <div className="space-y-6">
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
                          <span className="text-sm text-gray-400">P/S Ratio</span>
                          <span className="text-sm font-medium">
                            {company.ps ? company.ps.toFixed(2) : 'N/A'}
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
                          <span className="text-sm text-gray-400">Debt Ratio</span>
                          <span className="text-sm font-medium">
                            {company.debtRatio ? company.debtRatio.toFixed(2) : 'N/A'}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-400">Current Ratio</span>
                          <span className="text-sm font-medium">
                            {company.current_ratio ? company.current_ratio.toFixed(2) : 'N/A'}
                          </span>
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
                          <span className="text-sm text-gray-400">OCF Growth (1Y)</span>
                          <span className="text-sm font-medium">
                            {company.ocf_growth ? formatPercent(company.ocf_growth) : 'N/A'}
                          </span>
                        </div>
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
                
                <div className="mb-12">
                <h3 className="text-lg font-medium mb-4">P/E Ratio Analysis</h3>
                <div className="bg-gray-800 rounded-lg p-6 h-[460px] flex items-center justify-center relative">
                    {chartLoading[`fundamentals/pe_chart-${ticker}`] && (
                    <div className="absolute inset-0 flex items-center justify-center bg-gray-800 bg-opacity-75 z-10">
                        <div className="animate-spin h-10 w-10 border-t-2 border-b-2 border-blue-500 rounded-full"></div>
                    </div>
                    )}
                    {chartCache[`fundamentals/pe_chart-${ticker}`] ? (
                    <img 
                        src={chartCache[`fundamentals/pe_chart-${ticker}`]}
                        className="max-w-full max-h-full object-contain"
                        alt="PE Ratio Chart"
                        style={{ width: '100%', height: 'auto', maxHeight: '460px' }}
                    />
                    ) : (
                    <div className="text-gray-500">Loading chart...</div>
                    )}
                </div>
                </div>
                
                <div className="mb-8">
                <h3 className="text-lg font-medium mb-4">Enhanced Valuation Analysis</h3>
                <div className="bg-gray-800 rounded-lg p-6 h-[460px] flex items-center justify-center relative">
                    {chartLoading[`fundamentals/enhanced_valuation_chart-${ticker}`] && (
                    <div className="absolute inset-0 flex items-center justify-center bg-gray-800 bg-opacity-75 z-10">
                        <div className="animate-spin h-10 w-10 border-t-2 border-b-2 border-blue-500 rounded-full"></div>
                    </div>
                    )}
                    {chartCache[`fundamentals/enhanced_valuation_chart-${ticker}`] ? (
                    <img 
                        src={chartCache[`fundamentals/enhanced_valuation_chart-${ticker}`]}
                        className="max-w-full max-h-full object-contain"
                        alt="Enhanced Valuation Chart"
                        style={{ width: '100%', height: 'auto', maxHeight: '460px' }}
                    />
                    ) : (
                    <div className="text-gray-500">Loading chart...</div>
                    )}
                </div>
                </div>
            </div>
            )}
            
            {/* Historical Performance Section */}
            {activeTab === 'historical' && (
            <div className="bg-nav rounded-lg shadow-xl p-6 mb-6">
                <h2 className="text-xl font-semibold mb-6">Historical Performance</h2>
                
                <div className="mb-12">
                <h3 className="text-lg font-medium mb-4">Yearly Performance</h3>
                <div className="bg-gray-800 rounded-lg p-6 h-460px flex items-center justify-center relative">
                    {chartLoading[`fundamentals_historical/generate_yearly_performance_chart-${ticker}`] && (
                    <div className="absolute inset-0 flex items-center justify-center bg-gray-800 bg-opacity-75 z-10">
                        <div className="animate-spin h-10 w-10 border-t-2 border-b-2 border-blue-500 rounded-full"></div>
                    </div>
                    )}
                    {chartCache[`fundamentals_historical/generate_yearly_performance_chart-${ticker}`] ? (
                    <img 
                        src={chartCache[`fundamentals_historical/generate_yearly_performance_chart-${ticker}`]}
                        className="max-w-full max-h-full object-contain"
                        alt="Yearly Performance Chart"
                        style={{ width: '100%', height: 'auto', maxHeight: '460px' }}
                    />
                    ) : (
                    <div className="text-gray-500">Loading chart...</div>
                    )}
                </div>
                </div>
                
                <div>
                <h3 className="text-lg font-medium mb-4">Free Cash Flow Analysis</h3>
                <div className="bg-gray-800 rounded-lg p-6 h-[460px] flex items-center justify-center relative">
                    {chartLoading[`fundamentals_historical/free_cash_flow_chart-${ticker}`] && (
                    <div className="absolute inset-0 flex items-center justify-center bg-gray-800 bg-opacity-75 z-10">
                        <div className="animate-spin h-10 w-10 border-t-2 border-b-2 border-blue-500 rounded-full"></div>
                    </div>
                    )}
                    {chartCache[`fundamentals_historical/free_cash_flow_chart-${ticker}`] ? (
                    <img 
                        src={chartCache[`fundamentals_historical/free_cash_flow_chart-${ticker}`]}
                        className="max-w-full max-h-full object-contain"
                        alt="Free Cash Flow Chart"
                        style={{ width: '100%', height: 'auto', maxHeight: '460px' }}
                    />
                    ) : (
                    <div className="text-gray-500">Loading chart...</div>
                    )}
                </div>
                </div>
            </div>
            )}
            
            {/* News Section */}
            {activeTab === 'news' && (
              <div className="bg-nav rounded-lg shadow-xl p-6 mb-6">
                <h2 className="text-xl font-semibold mb-6">Latest News</h2>
                
                {/* News Loading State */}
                {newsLoading && (
                  <div className="flex justify-center items-center h-48">
                    <div className="animate-spin h-10 w-10 border-t-2 border-b-2 border-blue-500 rounded-full"></div>
                  </div>
                )}
                
                {/* News Error State */}
                {newsError && (
                  <div className="bg-red-900/30 text-white p-4 rounded-lg mb-6">
                    <p>{newsError}</p>
                  </div>
                )}
                
                {/* News Items */}
                {!newsLoading && !newsError && news.length === 0 && (
                  <div className="text-center text-gray-400 py-10">
                    <p>No recent news found for {ticker}</p>
                  </div>
                )}
                
                {!newsLoading && !newsError && news.length > 0 && (
                  <div className="space-y-6">
                    {news.map((item, index) => (
                      <div key={index} className="bg-gray-800 rounded-lg p-4 hover:bg-gray-700 transition-colors">
                        <div className="flex flex-col md:flex-row">
                          {/* News Image (if available) */}
                          {item.image_url && (
                            <div className="w-full md:w-1/4 mb-4 md:mb-0 md:mr-4">
                              <img 
                                src={item.image_url} 
                                alt={item.title}
                                className="w-full h-32 object-cover rounded-lg"
                                onError={(e) => {
                                  e.target.onerror = null;
                                  e.target.style.display = 'none';
                                }}
                              />
                            </div>
                          )}
                          
                          {/* News Content */}
                          <div className={item.image_url ? "w-full md:w-3/4" : "w-full"}>
                            <h3 className="text-lg font-medium mb-2">
                              <a 
                                href={item.url} 
                                target="_blank" 
                                rel="noopener noreferrer"
                                className="text-blue-400 hover:text-blue-300 transition-colors"
                              >
                                {item.title}
                              </a>
                            </h3>
                            
                            <div className="flex items-center text-sm text-gray-400 mb-2">
                              <span className="mr-3">{item.source}</span>
                              <span>{formatNewsDate(item.published_at)}</span>
                            </div>
                            
                            <p className="text-gray-300 text-sm">
                              {item.summary}
                            </p>
                            
                            <a 
                              href={item.url} 
                              target="_blank" 
                              rel="noopener noreferrer"
                              className="inline-block mt-3 text-sm text-blue-400 hover:text-blue-300 transition-colors"
                            >
                              Read more →
                            </a>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
            
            {/* Business Overview Section */}
            {activeTab === 'investors' && (
              <div className="flex flex-col space-y-3 mt-4">
              {/* 10-K Reports (SEC) */}
              <a 
                href={secUrl}
                target="_blank" 
                rel="noopener noreferrer"
                className="text-blue-400 hover:text-blue-300 transition-colors inline-flex items-center"
              >
                <span>SEC Filings (10-K, 10-Q, 8-K etc...)s</span>
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 ml-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                </svg>
              </a>
              
              {/* Investor Relations (dynamically generated) */}

                 {/* Corporate IR site (override → fallback) */}
            <a
                href={investorUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-400 hover:text-blue-300 inline-flex items-center"
                >
                <span>Investor Relations</span>
                <svg className="h-4 w-4 ml-1" viewBox="0 0 24 24" fill="none"
                    stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
                    <path d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4"/>
                    <path d="M14 4h6v6M20 4L10 14"/>
                </svg>
                </a>

            </div>
                )}

          </>
        )}
      </div>
    </div>
  );
};

export default CompanyDetail;
              