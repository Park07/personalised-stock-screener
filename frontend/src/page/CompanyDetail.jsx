import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import AuthButton from "../component/AuthButton";

const CompanyDetail = () => {
  const { ticker } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [company, setCompany] = useState(null);
  const [error, setError] = useState(null);
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
        // This leverages your existing rank endpoint
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
          <div className="space-y-6">
            {/* Company Header */}
            <div className="bg-nav rounded-lg shadow-xl p-6">
              <div className="flex flex-col md:flex-row justify-between items-start md:items-center">
                <div>
                  <h1 className="text-3xl font-bold">{ticker}</h1>
                  <p className="text-xl text-gray-400">{company.company_name}</p>
                </div>
                <div className="mt-4 md:mt-0 flex flex-col md:items-end">
                  <span className="bg-gray-700 text-gray-300 px-3 py-1 rounded-full text-sm mb-2">
                    {company.sector}
                  </span>
                  {company.current_price && (
                    <span className="text-2xl font-bold">${company.current_price.toFixed(2)}</span>
                  )}
                  {company.market_cap_formatted && (
                    <span className="text-sm text-gray-400">
                      Market Cap: {company.market_cap_formatted}
                    </span>
                  )}
                </div>
              </div>
              
              {/* Company Website Link */}
              {company.website && (
                <div className="mt-4">
                  <a 
                    href={company.website} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="text-blue-400 hover:text-blue-300 transition-colors"
                  >
                    {company.website} 
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 inline ml-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                    </svg>
                  </a>
                </div>
              )}
            </div>
            
            {/* Score Summary Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
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
            
            {/* Financial Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
              {/* Valuation Metrics */}
              <div className="bg-nav rounded-lg shadow-xl p-6">
                <h3 className="text-lg font-semibold mb-4 border-b border-gray-600 pb-2">
                  <span className="flex items-center">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 8h6m-5 0a3 3 0 110 6H9l3 3m-3-6h6m6 1a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    Valuation
                  </span>
                </h3>
                <div className="space-y-3">
                  <div className="grid grid-cols-2">
                    <p className="text-sm text-gray-400">P/E Ratio</p>
                    <p className="text-sm font-medium text-right">
                      {company.pe_ratio || company.pe ? 
                       (company.pe_ratio || company.pe).toFixed(2) : 'N/A'}
                    </p>
                  </div>
                  <div className="grid grid-cols-2">
                    <p className="text-sm text-gray-400">Sector P/E</p>
                    <p className="text-sm font-medium text-right">
                      {company.sector_pe ? company.sector_pe.toFixed(2) : 'N/A'}
                    </p>
                  </div>
                  <div className="grid grid-cols-2">
                    <p className="text-sm text-gray-400">PEG Ratio</p>
                    <p className="text-sm font-medium text-right">
                      {company.peg ? company.peg.toFixed(2) : 'N/A'}
                    </p>
                  </div>
                  <div className="grid grid-cols-2">
                    <p className="text-sm text-gray-400">P/S Ratio</p>
                    <p className="text-sm font-medium text-right">
                      {company.ps ? company.ps.toFixed(2) : 'N/A'}
                    </p>
                  </div>
                  <div className="grid grid-cols-2">
                    <p className="text-sm text-gray-400">EV/EBITDA</p>
                    <p className="text-sm font-medium text-right">
                      {company.ev_ebitda ? company.ev_ebitda.toFixed(2) : 'N/A'}
                    </p>
                  </div>
                </div>
              </div>
              
              {/* Growth Metrics */}
              <div className="bg-nav rounded-lg shadow-xl p-6">
                <h3 className="text-lg font-semibold mb-4 border-b border-gray-600 pb-2">
                  <span className="flex items-center">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                    </svg>
                    Growth
                  </span>
                </h3>
                <div className="space-y-3">
                  <div className="grid grid-cols-2">
                    <p className="text-sm text-gray-400">Revenue Growth</p>
                    <p className="text-sm font-medium text-right">
                      {company.revenue_growth ? formatPercent(company.revenue_growth) : 'N/A'}
                    </p>
                  </div>
                  <div className="grid grid-cols-2">
                    <p className="text-sm text-gray-400">Earnings Growth</p>
                    <p className="text-sm font-medium text-right">
                      {company.earnings_growth || company.epsGrowth ? 
                       formatPercent(company.earnings_growth || company.epsGrowth) : 'N/A'}
                    </p>
                  </div>
                  <div className="grid grid-cols-2">
                    <p className="text-sm text-gray-400">OCF Growth</p>
                    <p className="text-sm font-medium text-right">
                      {company.ocf_growth ? formatPercent(company.ocf_growth) : 'N/A'}
                    </p>
                  </div>
                </div>
              </div>
              
              {/* Income Metrics */}
              <div className="bg-nav rounded-lg shadow-xl p-6">
                <h3 className="text-lg font-semibold mb-4 border-b border-gray-600 pb-2">
                  <span className="flex items-center">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2 text-yellow-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" />
                    </svg>
                    Income
                  </span>
                </h3>
                <div className="space-y-3">
                  <div className="grid grid-cols-2">
                    <p className="text-sm text-gray-400">Dividend Yield</p>
                    <p className="text-sm font-medium text-right">
                      {company.dividend_yield ? formatPercent(company.dividend_yield) : 'N/A'}
                    </p>
                  </div>
                  <div className="grid grid-cols-2">
                    <p className="text-sm text-gray-400">Payout Ratio</p>
                    <p className="text-sm font-medium text-right">
                      {company.payout_ratio ? formatPercent(company.payout_ratio) : 'N/A'}
                    </p>
                  </div>
                  <div className="grid grid-cols-2">
                    <p className="text-sm text-gray-400">FCF Yield</p>
                    <p className="text-sm font-medium text-right">
                      {company.freeCashFlowYield ? formatPercent(company.freeCashFlowYield) : 'N/A'}
                    </p>
                  </div>
                  <div className="grid grid-cols-2">
                    <p className="text-sm text-gray-400">Return on Equity</p>
                    <p className="text-sm font-medium text-right">
                      {company.roe ? formatPercent(company.roe) : 'N/A'}
                    </p>
                  </div>
                </div>
              </div>
              
              {/* Financial Health */}
              <div className="bg-nav rounded-lg shadow-xl p-6">
                <h3 className="text-lg font-semibold mb-4 border-b border-gray-600 pb-2">
                  <span className="flex items-center">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                    </svg>
                    Financial Health
                  </span>
                </h3>
                <div className="space-y-3">
                  <div className="grid grid-cols-2">
                    <p className="text-sm text-gray-400">Debt/Equity</p>
                    <p className="text-sm font-medium text-right">
                      {company.debt_equity_ratio ? company.debt_equity_ratio.toFixed(2) : 'N/A'}
                    </p>
                  </div>
                  <div className="grid grid-cols-2">
                    <p className="text-sm text-gray-400">Debt Ratio</p>
                    <p className="text-sm font-medium text-right">
                      {company.debtRatio ? company.debtRatio.toFixed(2) : 'N/A'}
                    </p>
                  </div>
                  <div className="grid grid-cols-2">
                    <p className="text-sm text-gray-400">Current Ratio</p>
                    <p className="text-sm font-medium text-right">
                      {company.current_ratio ? company.current_ratio.toFixed(2) : 'N/A'}
                    </p>
                  </div>
                </div>
              </div>
              
              {/* Market Data */}
              <div className="bg-nav rounded-lg shadow-xl p-6">
                <h3 className="text-lg font-semibold mb-4 border-b border-gray-600 pb-2">
                  <span className="flex items-center">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2 text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
                    </svg>
                    Market Data
                  </span>
                </h3>
                <div className="space-y-3">
                  <div className="grid grid-cols-2">
                    <p className="text-sm text-gray-400">Current Price</p>
                    <p className="text-sm font-medium text-right">
                      {company.current_price ? formatCurrency(company.current_price) : 'N/A'}
                    </p>
                  </div>
                  <div className="grid grid-cols-2">
                    <p className="text-sm text-gray-400">Market Cap</p>
                    <p className="text-sm font-medium text-right">
                      {company.market_cap_formatted || 
                       (company.market_cap ? formatLargeNumber(company.market_cap) : 'N/A')}
                    </p>
                  </div>
                  <div className="grid grid-cols-2">
                    <p className="text-sm text-gray-400">Enterprise Value</p>
                    <p className="text-sm font-medium text-right">
                      {company.enterpriseValue ? formatLargeNumber(company.enterpriseValue) : 'N/A'}
                    </p>
                  </div>
                </div>
              </div>
            </div>
            
            {/* Chart Placeholder Sections */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Valuation Charts Section */}
              <div className="bg-nav rounded-lg shadow-xl p-6">
                <h3 className="text-lg font-semibold mb-6 border-b border-gray-600 pb-2">
                  Valuation Analysis
                </h3>
                
                {/* PE Ratio Chart Placeholder */}
                <div className="mb-6">
                  <h4 className="text-md font-medium mb-2 text-gray-300">P/E Ratio vs Sector</h4>
                  <div className="bg-gray-800 h-48 rounded-lg flex items-center justify-center">
                    <p className="text-gray-500">
                      P/E Ratio Chart - Coming Soon
                    </p>
                  </div>
                </div>
                
                {/* Intrinsic Value Chart Placeholder */}
                <div>
                  <h4 className="text-md font-medium mb-2 text-gray-300">Intrinsic Value Analysis</h4>
                  <div className="bg-gray-800 h-48 rounded-lg flex items-center justify-center">
                    <p className="text-gray-500">
                      Intrinsic Value Chart - Coming Soon
                    </p>
                  </div>
                </div>
              </div>
              
              {/* Historical Charts Section */}
              <div className="bg-nav rounded-lg shadow-xl p-6">
                <h3 className="text-lg font-semibold mb-6 border-b border-gray-600 pb-2">
                  Historical Performance
                </h3>
                
                {/* Revenue Growth Chart Placeholder */}
                <div className="mb-6">
                  <h4 className="text-md font-medium mb-2 text-gray-300">Revenue Growth</h4>
                  <div className="bg-gray-800 h-48 rounded-lg flex items-center justify-center">
                    <p className="text-gray-500">
                      Revenue Growth Chart - Coming Soon
                    </p>
                  </div>
                </div>
                
                {/* FCF Yield Chart Placeholder */}
                <div>
                  <h4 className="text-md font-medium mb-2 text-gray-300">Free Cash Flow Yield</h4>
                  <div className="bg-gray-800 h-48 rounded-lg flex items-center justify-center">
                    <p className="text-gray-500">
                      FCF Yield Chart - Coming Soon
                    </p>
                  </div>
                </div>
              </div>
            </div>
            
            {/* Data Sources */}
            <div className="bg-nav rounded-lg shadow-xl p-4 text-center text-sm text-gray-400">
              Data provided by financial APIs. Last updated: {new Date().toLocaleDateString()}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default CompanyDetail;
