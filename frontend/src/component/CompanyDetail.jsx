import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import ImprovedCompanyLogo from './ImprovedCompanyLogo';
import ScoreIndicator from './ScoreIndicator';
import AuthButton from './AuthButton';

const CompanyDetail = () => {
  const { ticker } = useParams();
  const navigate = useNavigate();
  const [company, setCompany] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    const fetchCompanyData = async () => {
      if (!ticker) return;
      
      setLoading(true);
      setError(null);
      
      try {
        // API endpoint for company details
        const url = `http://35.169.25.122/api/company/${ticker}`;
        
        const response = await fetch(url);
        if (!response.ok) {
          throw new Error(`API returned status ${response.status}`);
        }
        
        const data = await response.json();
        
        setCompany(data);
      } catch (err) {
        console.error("Error fetching company data:", err);
        setError(`Failed to load data for ${ticker}: ${err.message}`);
        
        // For development - mock data
        setCompany({
          ticker: ticker,
          name: `${ticker} Corporation`,
          sector: "Technology",
          market_cap: "750B",
          current_price: 165.23,
          pe_ratio: 24.5,
          ev_ebitda: 18.7,
          dividend_yield: 0.012,
          payout_ratio: 0.24,
          debt_equity_ratio: 1.2,
          current_ratio: 2.5,
          revenue_growth: 0.15,
          earnings_growth: 0.18,
          ocf_growth: 0.12,
          valuation_score: 4.2,
          health_score: 4.5,
          growth_score: 4.0,
          overall_score: 4.3,
          description: "This is a leading technology company that specializes in consumer electronics, software, and online services. The company has shown consistent growth over the past decade and maintains a strong market position.",
          competitors: ["AAPL", "MSFT", "GOOG", "AMZN"],
          historical_data: [
            { date: "2023-04-01", price: 150.25 },
            { date: "2023-05-01", price: 155.67 },
            { date: "2023-06-01", price: 160.12 },
            { date: "2023-07-01", price: 158.75 },
            { date: "2023-08-01", price: 162.33 },
            { date: "2023-09-01", price: 165.80 },
            { date: "2023-10-01", price: 163.45 },
            { date: "2023-11-01", price: 167.90 },
            { date: "2023-12-01", price: 172.15 },
            { date: "2024-01-01", price: 175.50 },
            { date: "2024-02-01", price: 170.25 },
            { date: "2024-03-01", price: 165.23 }
          ]
        });
      } finally {
        setLoading(false);
      }
    };
    
    fetchCompanyData();
  }, [ticker]);
  
  if (loading) {
    return (
      <div className="min-h-screen bg-background text-gray-100 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="min-h-screen bg-background text-gray-100 p-8">
        <div className="max-w-4xl mx-auto bg-red-900 rounded-lg p-6">
          <h2 className="text-2xl font-bold mb-4">Error</h2>
          <p>{error}</p>
          <AuthButton
            type="button"
            className="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg"
            onClick={() => navigate('/screener')}
          >
            Back to Screener
          </AuthButton>
        </div>
      </div>
    );
  }
  
  if (!company) {
    return (
      <div className="min-h-screen bg-background text-gray-100 p-8">
        <div className="max-w-4xl mx-auto bg-gray-800 rounded-lg p-6">
          <h2 className="text-2xl font-bold mb-4">Company Not Found</h2>
          <p>We couldn't find information for ticker: {ticker}</p>
          <AuthButton
            type="button"
            className="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg"
            onClick={() => navigate('/screener')}
          >
            Back to Screener
          </AuthButton>
        </div>
      </div>
    );
  }
  
  return (
    <div className="min-h-screen bg-background text-gray-100">
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Navigation */}
        <div className="mb-6">
          <AuthButton
            type="button"
            className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg flex items-center"
            onClick={() => navigate('/screener')}
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M9.707 16.707a1 1 0 01-1.414 0l-6-6a1 1 0 010-1.414l6-6a1 1 0 011.414 1.414L5.414 9H17a1 1 0 110 2H5.414l4.293 4.293a1 1 0 010 1.414z" clipRule="evenodd" />
            </svg>
            Back to Screener
          </AuthButton>
        </div>
        
        {/* Company Header */}
        <div className="bg-nav rounded-lg shadow-xl p-6 mb-8">
          <div className="flex items-center">
            <ImprovedCompanyLogo ticker={company.ticker} name={company.name} />
            <div className="ml-4">
              <h1 className="text-3xl font-bold">{company.name}</h1>
              <div className="flex space-x-4 text-gray-400">
                <span className="font-medium text-blue-400">{company.ticker}</span>
                <span>{company.sector}</span>
                <span>Market Cap: {company.market_cap}</span>
              </div>
            </div>
          </div>
        </div>
        
        {/* Company Overview */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="md:col-span-2 bg-nav rounded-lg shadow-xl p-6">
            <h2 className="text-xl font-semibold mb-4">Company Overview</h2>
            <p className="text-gray-300 mb-6">{company.description}</p>
            
            <h3 className="text-lg font-medium mb-2">Key Statistics</h3>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <div>
                <div className="text-gray-400 mb-1">Current Price</div>
                <div className="text-xl">${company.current_price}</div>
              </div>
              <div>
                <div className="text-gray-400 mb-1">P/E Ratio</div>
                <div className="text-xl">{company.pe_ratio}</div>
              </div>
              <div>
                <div className="text-gray-400 mb-1">EV/EBITDA</div>
                <div className="text-xl">{company.ev_ebitda}</div>
              </div>
              <div>
                <div className="text-gray-400 mb-1">Dividend Yield</div>
                <div className="text-xl">{(company.dividend_yield * 100).toFixed(2)}%</div>
              </div>
              <div>
                <div className="text-gray-400 mb-1">Debt/Equity</div>
                <div className="text-xl">{company.debt_equity_ratio}</div>
              </div>
              <div>
                <div className="text-gray-400 mb-1">Revenue Growth</div>
                <div className="text-xl">{(company.revenue_growth * 100).toFixed(2)}%</div>
              </div>
            </div>
          </div>
          
          {/* Scores Panel */}
          <div className="bg-nav rounded-lg shadow-xl p-6">
            <h2 className="text-xl font-semibold mb-4">Investment Scores</h2>
            <div className="space-y-4">
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
        
        {/* Stock Chart (Placeholder) */}
        <div className="bg-nav rounded-lg shadow-xl p-6 mb-8">
          <h2 className="text-xl font-semibold mb-4">Price History</h2>
          <div className="h-72 bg-gray-800 rounded-lg flex items-center justify-center">
            <p className="text-gray-400">Price chart would be displayed here</p>
          </div>
        </div>
        
        {/* Competitors */}
        <div className="bg-nav rounded-lg shadow-xl p-6">
          <h2 className="text-xl font-semibold mb-4">Competitors</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {company.competitors.map(ticker => (
              <div 
                key={ticker}
                className="bg-gray-800 rounded-lg p-4 cursor-pointer hover:bg-gray-700 transition-colors"
                onClick={() => navigate(`/company/${ticker}`)}
              >
                <div className="font-medium text-blue-400">{ticker}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default CompanyDetail;