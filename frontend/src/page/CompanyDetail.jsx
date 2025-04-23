import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { formatMarketCap } from './Screener'; // Import the formatter we created
import AuthButton from '../component/AuthButton';

const CompanyDetail = () => {
  const { ticker } = useParams();
  const navigate = useNavigate();
  const [company, setCompany] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Chart URLs - these will be set when data is fetched
  const [peChartUrl, setPeChartUrl] = useState(null);
  const [cashFlowChartUrl, setCashFlowChartUrl] = useState(null);
  const [performanceChartUrl, setPerformanceChartUrl] = useState(null);
  const [valuationChartUrl, setEnhancedValuationChartUrl] = useState(null);
  
  const API_BASE_URL = "http://192.168.64.2:5000";

  // Helper function to fetch chart images
  const fetchChart = async (url, params, setStateFunction, chartName) => {
    try {
      const response = await fetch(`${url}?${new URLSearchParams(params)}`);
      
      if (!response.ok) {
        console.error(`Failed to fetch ${chartName}: ${response.status}`);
        return;
      }
      
      // For PNG responses, we just need the URL
      setStateFunction(`${url}?${new URLSearchParams(params)}`);
    } catch (error) {
      console.error(`Error fetching ${chartName}:`, error);
    }
  };

  useEffect(() => {
    const fetchCompanyDetails = async () => {
      setLoading(true);
      setError(null);
      
      try {
        const url = `${API_BASE_URL}/api/company/${ticker}`;
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
        
        // Format market cap and other numeric values
        const formattedData = {
          ...data,
          market_cap_formatted: formatMarketCap(data.market_cap)
        };
        
        setCompany(formattedData);
        
        // Fetch chart images once we have the company data
        // PE Chart
        fetchChart(`${API_BASE_URL}/fundamentals/pe_chart`, {
          ticker: ticker,
          format: "png",
          theme: "dark",
          type: "plotly"
        }, setPeChartUrl, "PE chart");
        
        // Performance Chart
        fetchChart(`${API_BASE_URL}/fundamentals_historical/generate_yearly_performance_chart`, {
          ticker, 
          quarters: 4, 
          dark_theme: true, 
          format: "png"
        }, setPerformanceChartUrl, "performance chart");
        
        // Cash Flow Chart
        fetchChart(`${API_BASE_URL}/fundamentals_historical/free_cash_flow_chart`, {
          ticker, 
          years: 4, 
          theme: "dark", 
          format: "png"
        }, setCashFlowChartUrl, "cash flow chart");
        
        // Enhanced Valuation Chart
        fetchChart(`${API_BASE_URL}/fundamentals/enhanced_valuation_chart`, {
          ticker, 
          theme: "dark", 
          format: "png"
        }, setEnhancedValuationChartUrl, "valuation chart");
        
      } catch (error) {
        console.error("Error fetching company details:", error);
        setError(`Error fetching company details: ${error.message}`);
      }
      finally {
        setLoading(false)
      }
    };
        
        fetchCompanyDetails();
    }, [ticker, API_BASE_URL]);
  
    // Format a score (1-5 scale) into a color and label
    const getScoreDisplay = (score) => {
      let color, label;
      
      if (score >= 4.5) {
        color = 'bg-green-500';
        label = 'Excellent';
      } else if (score >= 3.5) {
        color = 'bg-green-400';
        label = 'Good';
      } else if (score >= 2.5) {
        color = 'bg-yellow-400';
        label = 'Average';
      } else if (score >= 1.5) {
        color = 'bg-orange-400';
        label = 'Below Average';
      } else {
        color = 'bg-red-500';
        label = 'Poor';
      }
      
      return { color, label };
    };
  
    // Format a percentage value
    const formatPercent = (value) => {
      if (value === undefined || value === null) return 'N/A';
      return `${(value * 100).toFixed(2)}%`;
    };
  
    // Simple placeholder for company logo
    const CompanyLogo = ({ ticker, size = "medium" }) => {
      // Size classes
      const sizeClasses = {
        small: "w-8 h-8",
        medium: "w-12 h-12",
        large: "w-20 h-20"
      };
      
      // Generate a unique background color based on ticker
      const getTickerColor = () => {
        const colors = [
          'bg-blue-600', 'bg-green-600', 'bg-purple-600', 
          'bg-red-600', 'bg-yellow-600', 'bg-indigo-600', 
          'bg-pink-600', 'bg-teal-600'
        ];
        
        // Simple hash function for consistent color
        let hash = 0;
        for (let i = 0; i < ticker.length; i++) {
          hash = ticker.charCodeAt(i) + ((hash << 5) - hash);
        }
        
        return colors[Math.abs(hash) % colors.length];
      };
    
      return (
        <div className={`${sizeClasses[size]} rounded-lg ${getTickerColor()} flex items-center justify-center text-white font-bold`}>
          {ticker.slice(0, 2)}
        </div>
      );
    };
  
    if (loading) {
      return (
        <div className="min-h-screen bg-background text-gray-100 flex justify-center items-center">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
        </div>
      );
    }
  
    if (error || !company) {
      return (
        <div className="min-h-screen bg-background text-gray-100 p-6">
          <div className="max-w-4xl mx-auto">
            <div className="bg-red-900 rounded-lg p-6 mb-6">
              <h1 className="text-2xl font-bold mb-4">Error Loading Company Data</h1>
              <p>{error || "Could not load company data"}</p>
              <Link to="/screener" className="mt-4 inline-block px-4 py-2 bg-blue-600 rounded-md hover:bg-blue-700">
                Return to Screener
              </Link>
            </div>
          </div>
        </div>
      );
    }
  
    // Get score displays
    const overallScoreDisplay = getScoreDisplay(company.overall_score);
    const valuationScoreDisplay = getScoreDisplay(company.valuation_score);
    const healthScoreDisplay = getScoreDisplay(company.health_score);
    const growthScoreDisplay = getScoreDisplay(company.growth_score);
  
    return (
      <div className="min-h-screen bg-background text-gray-100">
        <div className="max-w-7xl mx-auto px-4 py-8">
          {/* Back button */}
          <div className="mb-6">
            <Link 
              to="/screener" 
              className="inline-flex items-center text-blue-400 hover:text-blue-300"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-1" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M9.707 16.707a1 1 0 01-1.414 0l-6-6a1 1 0 010-1.414l6-6a1 1 0 011.414 1.414L5.414 9H17a1 1 0 110 2H5.414l4.293 4.293a1 1 0 010 1.414z" clipRule="evenodd" />
              </svg>
              Back to Screener
            </Link>
          </div>
          
          {/* Company Header Section */}
          <div className="bg-nav rounded-lg shadow-xl p-6 mb-8">
            <div className="flex flex-col md:flex-row items-start md:items-center gap-6">
              {/* Company Logo */}
              <div className="w-24 h-24 rounded-lg overflow-hidden bg-gray-800 flex items-center justify-center">
                <CompanyLogo ticker={company.ticker} size="large" />
              </div>
              
              {/* Company Basic Info */}
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <h1 className="text-3xl font-bold">{company.name}</h1>
                  <span className="text-xl text-gray-400">${company.ticker}</span>
                </div>
                <div className="mt-2 flex flex-wrap gap-4 text-gray-300">
                  <div>
                    <span className="font-medium">Sector:</span> {company.sector}
                  </div>
                  <div>
                    <span className="font-medium">Industry:</span> {company.industry || 'N/A'}
                  </div>
                  <div>
                    <span className="font-medium">Market Cap:</span> {company.market_cap_formatted}
                  </div>
                  <div>
                    <span className="font-medium">Price:</span> ${company.current_price?.toFixed(2) || 'N/A'}
                  </div>
                </div>
              </div>
              
              {/* Overall Score */}
              <div className="flex flex-col items-center">
                <div className="text-lg font-semibold mb-2">Overall Score</div>
                <div className={`${overallScoreDisplay.color} w-20 h-20 rounded-full flex items-center justify-center text-2xl font-bold`}>
                  {company.overall_score?.toFixed(1) || 'N/A'}
                </div>
                <div className="mt-2 text-sm">{overallScoreDisplay.label}</div>
              </div>
            </div>
            
            {/* Company Description */}
            <div className="mt-6">
              <h2 className="text-xl font-semibold mb-3">About</h2>
              <p className="text-gray-300 leading-relaxed">
                {company.description || 'No company description available.'}
              </p>
            </div>
          </div>
          
          {/* Score Components Section */}
          <div className="bg-nav rounded-lg shadow-xl p-6 mb-8">
            <h2 className="text-2xl font-semibold mb-4">Investment Metrics</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Valuation Score */}
              <div className="bg-gray-800 rounded-lg p-4">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-xl font-medium">Valuation</h3>
                  <div className={`${valuationScoreDisplay.color} px-3 py-1 rounded-full text-sm font-medium`}>
                    {company.valuation_score?.toFixed(1) || 'N/A'} - {valuationScoreDisplay.label}
                  </div>
                </div>
                
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span>P/E Ratio</span>
                    <span className="font-medium">{company.pe_ratio?.toFixed(2) || 'N/A'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Forward P/E</span>
                    <span className="font-medium">{company.forward_pe?.toFixed(2) || 'N/A'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>PEG Ratio</span>
                    <span className="font-medium">{company.peg_ratio?.toFixed(2) || 'N/A'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Price/Book</span>
                    <span className="font-medium">{company.price_to_book?.toFixed(2) || 'N/A'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>EV/EBITDA</span>
                    <span className="font-medium">{company.ev_ebitda?.toFixed(2) || 'N/A'}</span>
                  </div>
                </div>
              </div>
              
              {/* Financial Health Score */}
              <div className="bg-gray-800 rounded-lg p-4">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-xl font-medium">Financial Health</h3>
                  <div className={`${healthScoreDisplay.color} px-3 py-1 rounded-full text-sm font-medium`}>
                    {company.health_score?.toFixed(1) || 'N/A'} - {healthScoreDisplay.label}
                  </div>
                </div>
                
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span>Current Ratio</span>
                    <span className="font-medium">{company.current_ratio?.toFixed(2) || 'N/A'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Quick Ratio</span>
                    <span className="font-medium">{company.quick_ratio?.toFixed(2) || 'N/A'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Debt/Equity</span>
                    <span className="font-medium">{company.debt_to_equity?.toFixed(2) || 'N/A'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Interest Coverage</span>
                    <span className="font-medium">{company.interest_coverage?.toFixed(2) || 'N/A'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Dividend Yield</span>
                    <span className="font-medium">{formatPercent(company.dividend_yield)}</span>
                  </div>
                </div>
              </div>
              
              {/* Growth Score */}
              <div className="bg-gray-800 rounded-lg p-4">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-xl font-medium">Growth</h3>
                  <div className={`${growthScoreDisplay.color} px-3 py-1 rounded-full text-sm font-medium`}>
                    {company.growth_score?.toFixed(1) || 'N/A'} - {growthScoreDisplay.label}
                  </div>
                </div>
                
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span>Revenue Growth (3yr)</span>
                    <span className="font-medium">{formatPercent(company.revenue_growth_3yr)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Earnings Growth (3yr)</span>
                    <span className="font-medium">{formatPercent(company.earnings_growth_3yr)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>FCF Growth (3yr)</span>
                    <span className="font-medium">{formatPercent(company.fcf_growth_3yr)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Payout Ratio</span>
                    <span className="font-medium">{formatPercent(company.payout_ratio)}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          {/* Historical Charts Section */}
          <div className="bg-nav rounded-lg shadow-xl p-6">
            <h2 className="text-2xl font-semibold mb-6">Historical Analysis</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              {/* Valuation Charts */}
              <div className="space-y-6">
                <h3 className="text-xl font-medium border-b border-gray-700 pb-2">Valuation</h3>
                
                {/* P/E vs Sector P/E Chart */}
                <div className="bg-gray-800 rounded-lg p-4">
                  <h4 className="text-lg font-medium mb-4">P/E Ratio vs Sector</h4>
                  <div className="h-64 flex items-center justify-center">
                    {peChartUrl ? (
                      <img 
                        src={peChartUrl} 
                        alt="P/E Ratio Chart" 
                        className="max-w-full max-h-full object-contain"
                      />
                    ) : (
                      <div className="text-gray-500 flex items-center">
                        <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Loading P/E chart...
                      </div>
                    )}
                  </div>
                </div>
                
                {/* Enhanced Valuation Chart */}
                <div className="bg-gray-800 rounded-lg p-4">
                  <h4 className="text-lg font-medium mb-4">Intrinsic Value vs Price</h4>
                  <div className="h-64 flex items-center justify-center">
                    {valuationChartUrl ? (
                      <img 
                        src={valuationChartUrl}
                        alt="Intrinsic Value Chart" 
                        className="max-w-full max-h-full object-contain"
                      />
                    ) : (
                      <div className="text-gray-500 flex items-center">
                        <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Loading valuation chart...
                      </div>
                    )}
                  </div>
                </div>
              </div>
              
              {/* Financial Charts */}
              <div className="space-y-6">
                <h3 className="text-xl font-medium border-b border-gray-700 pb-2">Financial Performance</h3>
                
                {/* Free Cash Flow Chart */}
                <div className="bg-gray-800 rounded-lg p-4">
                  <h4 className="text-lg font-medium mb-4">Free Cash Flow (4yr)</h4>
                  <div className="h-64 flex items-center justify-center">
                    {cashFlowChartUrl ? (
                      <img 
                        src={cashFlowChartUrl}
                        alt="Free Cash Flow Chart" 
                        className="max-w-full max-h-full object-contain"
                      />
                    ) : (
                      <div className="text-gray-500 flex items-center">
                        <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Loading cash flow chart...
                      </div>
                    )}
                  </div>
                </div>
                
                {/* Performance Chart (Earnings vs Revenue) */}
                <div className="bg-gray-800 rounded-lg p-4">
                  <h4 className="text-lg font-medium mb-4">Performance Metrics (4yr)</h4>
                  <div className="h-64 flex items-center justify-center">
                    {performanceChartUrl ? (
                      <img 
                        src={performanceChartUrl}
                        alt="Performance Chart" 
                        className="max-w-full max-h-full object-contain"
                      />
                    ) : (
                      <div className="text-gray-500 flex items-center">
                        <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Loading performance chart...
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };
  
export default CompanyDetail;