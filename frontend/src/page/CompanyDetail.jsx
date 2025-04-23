import { useState, useEffect } from "react";
import { useParams, useNavigate, useSearchParams } from "react-router-dom"; // Removed useLocation as searchParams is preferred
import AuthButton from "../component/AuthButton";
import SpiderChart from "../component/SpiderChart";

// Helper function (assuming it exists elsewhere or define it here)
const formatLargeNumber = (value) => {
    if (value === null || value === undefined) return 'N/A';
    const numValue = Number(value);
    if (isNaN(numValue)) return 'N/A';

    if (numValue >= 1e12) return `$${(numValue / 1e12).toFixed(2)}T`;
    if (numValue >= 1e9) return `$${(numValue / 1e9).toFixed(2)}B`;
    if (numValue >= 1e6) return `$${(numValue / 1e6).toFixed(2)}M`;
    return `$${numValue.toLocaleString()}`;
};

const formatPercent = (value) => {
    if (value === null || value === undefined) return 'N/A';
     const numValue = Number(value);
     if (isNaN(numValue)) return 'N/A';
    return `${(numValue * 100).toFixed(2)}%`;
};

const formatNewsDate = (dateString) => {
    if (!dateString) return '';
    try {
        const date = new Date(dateString);
        // Check if date is valid before formatting
        if (isNaN(date.getTime())) return dateString; // Return original if invalid
        return date.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
    } catch (e) {
        return dateString; // Return original on error
    }
};


const CompanyDetail = () => {
    const { ticker } = useParams();
    const navigate = useNavigate();
    const [searchParams] = useSearchParams(); // Hook to read URL query parameters

    // --- Read parameters directly from URL ---
    // Provide sensible defaults if parameters are missing
    const goalFromUrl = searchParams.get("goal") || "value";
    const riskFromUrl = searchParams.get("risk") || "moderate";
    const sectorFromUrl = searchParams.get("sector") || null; // Allow null initially, determine later if needed

    // --- State variables ---
    const [loading, setLoading] = useState(false);
    const [company, setCompany] = useState(null);
    const [error, setError] = useState(null);
    const [activeTab, setActiveTab] = useState("main-ratios");
    const [news, setNews] = useState([]);
    const [newsLoading, setNewsLoading] = useState(false);
    const [newsError, setNewsError] = useState(null);
    // State for latest price
    const [latestPrice, setLatestPrice] = useState(null);
    const [latestPriceLoading, setLatestPriceLoading] = useState(false);
    const [priceError, setPriceError] = useState(null);

    const API_BASE_URL = "http://192.168.64.2:5000";

    // --- Links ---
    const IR_OVERRIDE = {
        NVDA: "https://investor.nvidia.com/home/default.aspx",
        MSFT: "https://www.microsoft.com/en-us/investor/default.aspx",
        AAPL: "https://investor.apple.com/investor-relations/default.aspx",
    };
    const investorUrl = IR_OVERRIDE[ticker?.toUpperCase()] || `https://investor.${ticker?.toLowerCase()}.com`;
    const secUrl = `https://www.sec.gov/cgi-bin/browse-edgar?CIK=${ticker}&owner=exclude&action=getcompany`;

    useEffect(() => {
        if (!ticker) return;
        let isMounted = true;
        const fetchLatestPrice = async () => {
            setLatestPriceLoading(true);
            setPriceError(null);
            setLatestPrice(null);
            try {
                const priceUrl = `${API_BASE_URL}/api/latest_price?ticker=${ticker}`;
                const priceResponse = await fetch(priceUrl);
                if (!isMounted) return;
                if (!priceResponse.ok) {
                    let errorMsg = `Failed price fetch: ${priceResponse.status}`;
                    try { const errData = await priceResponse.json(); errorMsg = errData.error || errorMsg; } catch (e) {/* ignore */}
                    throw new Error(errorMsg);
                }
                const priceData = await priceResponse.json();
                if (priceData && typeof priceData.price === 'number') {
                    if (isMounted) setLatestPrice(priceData.price);
                } else {
                     if (isMounted) setPriceError("Invalid price data received");
                }
            } catch(error) {
                 console.error("Error fetching latest price:", error);
                 if (isMounted) setPriceError(error.message);
            } finally {
                 if (isMounted) setLatestPriceLoading(false);
            }
        };
        fetchLatestPrice();
        return () => { isMounted = false; }; // Cleanup
    }, [ticker, API_BASE_URL]); 

    // --- Fetch company details ---
    useEffect(() => {
        console.log("CompanyDetail useEffect triggered. Ticker:", ticker);
        console.log("URL parameters read:", { goalFromUrl, riskFromUrl, sectorFromUrl });

        const fetchCompanyData = async () => {
            if (!ticker) return;

            setLoading(true);
            setError(null);
            setCompany(null); // Clear previous data

            try {
                console.log(`Workspaceing details for: ${ticker} using goal=${goalFromUrl}, risk=${riskFromUrl}, sector=${sectorFromUrl}`);

                // --- Fetch 1: Get Core Metrics ---
                const metricsUrl = `${API_BASE_URL}/fundamentals/key_metrics?ticker=${ticker}`;
                const metricsResponse = await fetch(metricsUrl);
                if (!metricsResponse.ok) {
                    let errorMsg = `API returned status ${metricsResponse.status} for key_metrics`;
                    try { const errData = await metricsResponse.json(); errorMsg = errData.error || errorMsg; } catch (e) {/* ignore */}
                    throw new Error(errorMsg);
                }
                const metricsData = await metricsResponse.json();
                console.log("Metrics data:", metricsData);

                // Determine the sector to use for ranking: URL param > metrics data > default
                const effectiveSector = sectorFromUrl || metricsData?.sector || "Technology";
                console.log("Effective sector for rank call:", effectiveSector);

                // --- Fetch 2: Get Ranking Data (using CORRECT parameters) ---
                const rankUrl = `${API_BASE_URL}/api/rank?goal=${goalFromUrl}&risk=${riskFromUrl}&sector=${encodeURIComponent(effectiveSector)}`;
                console.log("Fetching ranks with URL:", rankUrl);
                const rankResponse = await fetch(rankUrl);

                let companyDetails = null; // Initialize
                if (!rankResponse.ok) {
                     console.warn(`Rank API returned status ${rankResponse.status}. Proceeding without rank-specific details.`);
                     // Optionally, try parsing error JSON from rank API
                     try {
                        const rankErrorData = await rankResponse.json();
                        console.warn("Rank API error data:", rankErrorData);
                     } catch(e) {/* ignore if not json */}
                } else {
                    const rankData = await rankResponse.json();
                    if (rankData && rankData.companies) {
                        companyDetails = rankData.companies.find(c => c.ticker === ticker);
                        if (!companyDetails) {
                            console.warn(`Company ${ticker} not found in rank results for sector ${effectiveSector}. Rank details will be missing.`);
                        }
                    } else {
                         console.warn("Rank API response missing 'companies' array.");
                    }
                }
                console.log("Company details from rank:", companyDetails); // This might be null if rank failed or company not found

                // --- Combine the data ---
                setCompany({
                    ticker: ticker,
                    company_name: companyDetails?.company_name || metricsData?.companyName || ticker,
                    sector: effectiveSector, // Use the sector determined above
                    website: companyDetails?.website || metricsData?.website || null,
                    market_cap: companyDetails?.market_cap || metricsData?.marketCap || null,
                    market_cap_formatted: companyDetails?.market_cap_formatted || formatLargeNumber(metricsData?.marketCap) || null,
                    current_price: companyDetails?.current_price || metricsData?.price || null,

                    // Metrics from fundamental endpoint (provide defaults)
                    pe: metricsData?.pe ?? null,
                    sector_pe: metricsData?.sector_pe ?? null,
                    peg: metricsData?.peg ?? null,
                    ps: metricsData?.ps ?? null,
                    roe: metricsData?.roe ?? null,
                    debtRatio: metricsData?.debtRatio ?? null,
                    enterpriseValue: metricsData?.enterpriseValue ?? null,
                    freeCashFlowYield: metricsData?.freeCashFlowYield ?? null,
                    // Ensure these names match your actual metricsData keys
                    revenueGrowth: metricsData?.revenueGrowth ?? null,
                    epsGrowth: metricsData?.epsGrowth ?? null,

                    // Scores from the ranking system (handle potential null companyDetails)
                    valuation_score: companyDetails?.valuation_score ?? null,
                    growth_score: companyDetails?.growth_score ?? null,
                    health_score: companyDetails?.health_score ?? null,
                    overall_score: companyDetails?.overall_score ?? null,

                    // Additional metrics primarily from ranking (handle potential null companyDetails)
                    pe_ratio: companyDetails?.pe_ratio ?? null,
                    dividend_yield: companyDetails?.dividend_yield ?? null,
                    payout_ratio: companyDetails?.payout_ratio ?? null,
                    debt_equity_ratio: companyDetails?.debt_equity_ratio ?? null,
                    current_ratio: companyDetails?.current_ratio ?? null,
                    ocf_growth: companyDetails?.ocf_growth ?? null,
                    earnings_growth: companyDetails?.earnings_growth ?? null,
                    // Note: revenue_growth exists in both, rank might be more specific (e.g., TTM)
                    // Decide which source to prioritize or rename one. Assuming rank is priority:
                    revenue_growth: companyDetails?.revenue_growth ?? metricsData?.revenueGrowth ?? null,
                    ev_ebitda: companyDetails?.ev_ebitda ?? null,
                });

            } catch (error) {
                console.error("Error fetching company data:", error);
                setError(`Error fetching data: ${error.message}`);
            } finally {
                setLoading(false);
            }
        };

        fetchCompanyData();

        // Cleanup function for useEffect (optional but good practice)
        return () => {
            console.log("CompanyDetail cleanup for ticker:", ticker);
            // Cancel any pending fetches if using AbortController more broadly
        };
    // IMPORTANT: Depend on the parameters read from the URL
    }, [ticker, goalFromUrl, riskFromUrl, sectorFromUrl, API_BASE_URL]);


    // --- Fetch company news (No changes needed here, kept for completeness) ---
    useEffect(() => {
        const fetchNews = async () => {
            if (!ticker || activeTab !== 'news' || news.length > 0 || newsLoading) return;

            setNewsLoading(true);
            setNewsError(null);

            try {
                 console.log("Fetching news for:", ticker);
                const newsUrl = `${API_BASE_URL}/api/company/news?ticker=${ticker}`;
                const response = await fetch(newsUrl);
                if (!response.ok) throw new Error(`Failed to fetch news: ${response.status}`);
                const newsData = await response.json();
                setNews(newsData.news || []);
            } catch (error) {
                console.error("Error fetching company news:", error);
                setNewsError(`Failed to load news: ${error.message}`);
                 setNews([]);
            } finally {
                setNewsLoading(false);
            }
        };

        // Only fetch news when the news tab is active
        if (activeTab === 'news') {
            fetchNews();
        }

        // Clear news when changing tabs *away* from news (optional)
        return () => {
            if (activeTab !== 'news') {
               // setNews([]); // Decide if you want news cleared when leaving tab
            }
        };

    }, [ticker, activeTab, API_BASE_URL, news.length, newsLoading]); // Rerun if ticker/tab changes

    const tabs = [
        { id: "main-ratios", label: "Main Ratios" },
        { id: "valuation", label: "Valuation" },
        { id: "historical", label: "Historical" },
        { id: "news", label: "News" },
        // Corrected from 'Business Overview' to 'Investors' based on your last code
        { id: "investors", label: "Investors" }
    ];

    // --- Helper for image loading error ---
    const handleImageError = (e) => {
        console.warn(`Chart failed to load: ${e.target.alt || 'Unknown Chart'} (src: ${e.target.src})`);
        // Simple text fallback
         const parent = e.target.parentNode;
         if (parent) {
            e.target.style.display = 'none'; // Hide broken image icon
            // Add text only if not already added
            if (!parent.querySelector('.chart-error-message')) {
                 const errorMsg = document.createElement('p');
                 errorMsg.className = 'text-red-500 text-xs chart-error-message';
                 errorMsg.textContent = `Chart unavailable (${e.target.alt})`;
                 parent.appendChild(errorMsg);
             }
         }
    };
    const displayPrice = !latestPriceLoading && !priceError && latestPrice !== null
        ? latestPrice
        : company?.current_price ?? null;



    return (
        <div className="min-h-screen bg-background text-gray-100">
            <div className="max-w-7xl mx-auto px-4 py-8">
                {/* Back Button */}
                <div className="mb-6">
                    <AuthButton
                        type="button"
                        className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
                        onClick={() => navigate(-1)} // Go back preserving history state
                    >
                        ← Back to Screener
                    </AuthButton>
                </div>

                {/* Error State */}
                {error && (
                    <div className="bg-red-900 text-white p-4 rounded-lg mb-6">
                        <h3 className="text-lg font-semibold mb-2">Error Loading Company Data:</h3>
                        <p>{error}</p>
                        <button
                           onClick={() => window.location.reload()} // Simple reload as a retry
                           className="mt-2 px-3 py-1 bg-blue-600 hover:bg-blue-700 rounded text-sm"
                         >
                           Retry
                         </button>
                    </div>
                )}

                {/* Loading State */}
                {loading && (
                    <div className="flex justify-center items-center h-64">
                        <div className="animate-spin h-12 w-12 border-t-2 border-b-2 border-blue-500 rounded-full"></div>
                        <p className="ml-4 text-lg">Loading Company Data for {ticker}...</p>
                    </div>
                )}

                {/* Company Details - Render only when data is available */}
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
                                <div className="mt-4 md:mt-0 flex flex-col md:items-end text-right">
                                     {displayPrice !== null && (
                                         <span className="text-2xl font-bold">
                                         ${displayPrice.toFixed(2)}
                                         {!latestPriceLoading && !priceError && latestPrice !== null && company?.current_price !== null && (
                                             <span className={`ml-2 text-sm ${latestPrice > company.current_price ? 'text-green-500' : latestPrice < company.current_price ? 'text-red-500' : 'text-gray-400'}`}>
                                                 {latestPrice > company.current_price ? '▲' : latestPrice < company.current_price ? '▼' : ''}
                                                 {((latestPrice - company.current_price) / company.current_price * 100).toFixed(2)}%
                                             </span>
                                         )}
                                     </span>
                                    )}
                                    {latestPriceLoading && (
                                    <span className="text-sm text-gray-400">Loading latest price...</span>
                                    )}
                                    
                                     {company.website && (
                                        <a
                                            href={company.website.startsWith('http') ? company.website : `https://${company.website}`} // Ensure protocol
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="text-blue-400 hover:text-blue-300 transition-colors mt-2 block max-w-xs truncate" // Added block, max-width, truncate
                                            title={company.website} // Show full URL on hover
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
                                     <div className={`w-16 h-16 rounded-full flex items-center justify-center text-white font-bold text-xl ${
                                         company.overall_score === null ? 'bg-gray-600' : // Gray if N/A
                                         company.overall_score >= 4 ? 'bg-green-600' :
                                         company.overall_score >= 3 ? 'bg-blue-600' :
                                         company.overall_score >= 2 ? 'bg-yellow-600' : 'bg-red-600'
                                     }`}>
                                         {company.overall_score !== null ? company.overall_score.toFixed(1) : 'N/A'}
                                     </div>
                                     <div className="ml-4">
                                          <p className="text-sm text-gray-300">
                                             {company.overall_score === null ? 'Unavailable' :
                                              company.overall_score >= 4 ? 'Excellent' :
                                              company.overall_score >= 3 ? 'Good' :
                                              company.overall_score >= 2 ? 'Fair' : 'Poor'}
                                          </p>
                                          <p className="text-xs text-gray-400">Composite Rating</p>
                                      </div>
                                  </div>
                              </div>
                              {/* Valuation Score */}
                              <div className="bg-nav rounded-lg shadow-xl p-4">
                                  <h3 className="text-sm text-gray-400 mb-1">Valuation Score</h3>
                                   <div className="flex items-center">
                                       <div className={`w-16 h-16 rounded-full flex items-center justify-center text-white font-bold text-xl ${
                                           company.valuation_score === null ? 'bg-gray-600' :
                                           company.valuation_score >= 4 ? 'bg-green-600' :
                                           company.valuation_score >= 3 ? 'bg-blue-600' :
                                           company.valuation_score >= 2 ? 'bg-yellow-600' : 'bg-red-600'
                                       }`}>
                                           {company.valuation_score !== null ? company.valuation_score.toFixed(1) : 'N/A'}
                                       </div>
                                       <div className="ml-4">
                                            <p className="text-sm text-gray-300">Price Attractiveness</p>
                                            <p className="text-xs text-gray-400">Based on P/E, PEG, EV/EBITDA</p>
                                        </div>
                                    </div>
                               </div>
                               {/* Growth Score */}
                               <div className="bg-nav rounded-lg shadow-xl p-4">
                                   <h3 className="text-sm text-gray-400 mb-1">Growth Score</h3>
                                    <div className="flex items-center">
                                       <div className={`w-16 h-16 rounded-full flex items-center justify-center text-white font-bold text-xl ${
                                            company.growth_score === null ? 'bg-gray-600' :
                                            company.growth_score >= 4 ? 'bg-green-600' :
                                            company.growth_score >= 3 ? 'bg-blue-600' :
                                            company.growth_score >= 2 ? 'bg-yellow-600' : 'bg-red-600'
                                       }`}>
                                           {company.growth_score !== null ? company.growth_score.toFixed(1) : 'N/A'}
                                       </div>
                                       <div className="ml-4">
                                           <p className="text-sm text-gray-300">Growth Potential</p>
                                           <p className="text-xs text-gray-400">Revenue, Earnings, Cash Flow</p>
                                        </div>
                                     </div>
                                </div>
                                {/* Health Score */}
                                <div className="bg-nav rounded-lg shadow-xl p-4">
                                    <h3 className="text-sm text-gray-400 mb-1">Health Score</h3>
                                     <div className="flex items-center">
                                       <div className={`w-16 h-16 rounded-full flex items-center justify-center text-white font-bold text-xl ${
                                          company.health_score === null ? 'bg-gray-600' :
                                          company.health_score >= 4 ? 'bg-green-600' :
                                          company.health_score >= 3 ? 'bg-blue-600' :
                                          company.health_score >= 2 ? 'bg-yellow-600' : 'bg-red-600'
                                       }`}>
                                           {company.health_score !== null ? company.health_score.toFixed(1) : 'N/A'}
                                       </div>
                                       <div className="ml-4">
                                           <p className="text-sm text-gray-300">Financial Strength</p>
                                           <p className="text-xs text-gray-400">Debt, Liquidity, FCF</p>
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
                                        // Corrected Class Logic
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

                        {/* Tab Content Area - Render all structures, hide inactive */}
                        <div className="tab-content">
                            {/* --- Main Ratios Section --- */}
                            <div className={activeTab === 'main-ratios' ? 'block' : 'hidden'}>
                                <div className="bg-nav rounded-lg shadow-xl p-6 mb-6">
                                    <h2 className="text-xl font-semibold mb-6">Main Ratios</h2>
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                        {/* Spider Chart */}
                                        <div className="bg-gray-800 rounded-lg p-4">
                                             <h3 className="text-lg font-semibold mb-4 text-center text-gray-300">Company Scores</h3>
                                             <div className="h-80">
                                                 <SpiderChart
                                                     scores={{
                                                         overall_score: company.overall_score ?? 0,
                                                         valuation_score: company.valuation_score ?? 0,
                                                         growth_score: company.growth_score ?? 0,
                                                         health_score: company.health_score ?? 0
                                                     }}
                                                 />
                                             </div>
                                         </div>
                                        {/* Ratios List */}
                                        <div className="space-y-6">
                                              {/* Valuation Metrics */}
                                              <div>
                                                  <h3 className="text-lg font-semibold mb-4 text-gray-300">Valuation</h3>
                                                  <div className="space-y-2">
                                                      <div className="flex justify-between"><span className="text-sm text-gray-400">P/E Ratio</span><span className="text-sm font-medium">{company.pe_ratio?.toFixed(2) ?? 'N/A'}</span></div>
                                                      <div className="flex justify-between"><span className="text-sm text-gray-400">EV/EBITDA</span><span className="text-sm font-medium">{company.ev_ebitda?.toFixed(2) ?? 'N/A'}</span></div>
                                                      <div className="flex justify-between"><span className="text-sm text-gray-400">PEG Ratio</span><span className="text-sm font-medium">{company.peg?.toFixed(2) ?? 'N/A'}</span></div>
                                                      <div className="flex justify-between"><span className="text-sm text-gray-400">P/S Ratio</span><span className="text-sm font-medium">{company.ps?.toFixed(2) ?? 'N/A'}</span></div>
                                                      <div className="flex justify-between"><span className="text-sm text-gray-400">Dividend Yield</span><span className="text-sm font-medium">{company.dividend_yield !== null ? formatPercent(company.dividend_yield) : '0%'}</span></div>
                                                  </div>
                                              </div>
                                              {/* Solvency Metrics */}
                                              <div>
                                                  <h3 className="text-lg font-semibold mb-4 text-gray-300">Solvency</h3>
                                                  <div className="space-y-2">
                                                      <div className="flex justify-between"><span className="text-sm text-gray-400">Debt/Equity</span><span className="text-sm font-medium">{company.debt_equity_ratio?.toFixed(2) ?? 'N/A'}</span></div>
                                                      <div className="flex justify-between"><span className="text-sm text-gray-400">Debt Ratio</span><span className="text-sm font-medium">{company.debtRatio?.toFixed(2) ?? 'N/A'}</span></div>
                                                      <div className="flex justify-between"><span className="text-sm text-gray-400">Current Ratio</span><span className="text-sm font-medium">{company.current_ratio?.toFixed(2) ?? 'N/A'}</span></div>
                                                  </div>
                                              </div>
                                              {/* Growth Metrics */}
                                              <div>
                                                  <h3 className="text-lg font-semibold mb-4 text-gray-300">Growth</h3>
                                                  <div className="space-y-2">
                                                      <div className="flex justify-between"><span className="text-sm text-gray-400">Revenue Growth (1Y)</span><span className="text-sm font-medium">{company.revenue_growth !== null ? formatPercent(company.revenue_growth) : 'N/A'}</span></div>
                                                      <div className="flex justify-between"><span className="text-sm text-gray-400">Net Income Growth (1Y)</span><span className="text-sm font-medium">{company.earnings_growth !== null ? formatPercent(company.earnings_growth) : 'N/A'}</span></div>
                                                      <div className="flex justify-between"><span className="text-sm text-gray-400">OCF Growth (1Y)</span><span className="text-sm font-medium">{company.ocf_growth !== null ? formatPercent(company.ocf_growth) : 'N/A'}</span></div>
                                                  </div>
                                               </div>
                                         </div>
                                    </div>
                                </div>
                            </div> {/* End Main Ratios */}

                             {/* --- Valuation Analysis Section --- */}
                             {/* Using direct src and hidden class approach */}
                            <div className={activeTab === 'valuation' ? 'block' : 'hidden'}>
                                <div className="bg-nav rounded-lg shadow-xl p-6 mb-6">
                                    <h2 className="text-xl font-semibold mb-6">Valuation Analysis</h2>
                                    {/* P/E Ratio Chart */}
                                    <div className="mb-12">
                                        <h3 className="text-lg font-medium mb-4">P/E Ratio Analysis</h3>
                                        <div className="bg-gray-800 rounded-lg p-4 h-[460px] flex items-center justify-center">
                                            <img
                                                src={`${API_BASE_URL}/fundamentals/pe_chart?ticker=${ticker}&theme=dark`}
                                                key={`${ticker}-pe`}
                                                className="max-w-full max-h-full object-contain rounded"
                                                alt="PE Chart"
                                                loading="lazy"
                                                onError={handleImageError}
                                            />
                                        </div>
                                    </div>
                                    {/* Enhanced Valuation Chart */}
                                    <div className="mb-12"> {/* Keep spacing consistent */}
                                        <h3 className="text-lg font-medium mb-4">Intrinsic Value Analysis</h3>
                                        <div className="bg-gray-800 rounded-lg p-4 h-[460px] flex items-center justify-center">
                                            <img
                                                src={`${API_BASE_URL}/fundamentals/enhanced_valuation_chart?ticker=${ticker}&theme=dark`}
                                                key={`${ticker}-enhval`}
                                                className="max-w-full max-h-full object-contain rounded"
                                                alt="Enhanced Valuation Chart"
                                                loading="lazy"
                                                onError={handleImageError}
                                            />
                                        </div>
                                    </div>
                                </div>
                            </div> {/* End Valuation */}

                             {/* --- Historical Performance Section --- */}
                            <div className={activeTab === 'historical' ? 'block' : 'hidden'}>
                                <div className="bg-nav rounded-lg shadow-xl p-6 mb-6">
                                    <h2 className="text-xl font-semibold mb-6">Historical Performance</h2>
                                    {/* Yearly Performance Chart */}
                                    <div className="mb-12">
                                        <h3 className="text-lg font-medium mb-4">Yearly Performance</h3>
                                        <div className="bg-gray-800 rounded-lg p-4 h-[460px] flex items-center justify-center">
                                            <img
                                                src={`${API_BASE_URL}/fundamentals_historical/generate_yearly_performance_chart?ticker=${ticker}&theme=dark`}
                                                key={`${ticker}-yrperf`}
                                                className="max-w-full max-h-full object-contain rounded"
                                                alt="Yearly Performance Chart"
                                                loading="lazy"
                                                onError={handleImageError}
                                            />
                                        </div>
                                    </div>
                                     {/* Free Cash Flow Chart */}
                                    <div> {/* No margin-bottom on last item */}
                                        <h3 className="text-lg font-medium mb-4">Free Cash Flow Analysis</h3>
                                        <div className="bg-gray-800 rounded-lg p-4 h-[460px] flex items-center justify-center">
                                            <img
                                                src={`${API_BASE_URL}/fundamentals_historical/free_cash_flow_chart?ticker=${ticker}&theme=dark`}
                                                key={`${ticker}-fcf`}
                                                className="max-w-full max-h-full object-contain rounded"
                                                alt="Free Cash Flow Chart"
                                                loading="lazy"
                                                onError={handleImageError}
                                            />
                                        </div>
                                    </div>
                                </div>
                            </div> {/* End Historical */}

                             {/* --- News Section --- */}
                            <div className={activeTab === 'news' ? 'block' : 'hidden'}>
                                 <div className="bg-nav rounded-lg shadow-xl p-6 mb-6">
                                     <h2 className="text-xl font-semibold mb-6">Latest News</h2>
                                     {newsLoading && ( <div className="flex justify-center items-center h-48"><div className="animate-spin h-10 w-10 border-t-2 border-b-2 border-blue-500 rounded-full"></div></div> )}
                                     {newsError && ( <div className="bg-red-900/30 text-white p-4 rounded-lg mb-6"><p>{newsError}</p></div> )}
                                     {!newsLoading && !newsError && news.length === 0 && ( <div className="text-center text-gray-400 py-10"><p>No recent news found for {ticker}</p></div> )}
                                     {!newsLoading && !newsError && news.length > 0 && (
                                         <div className="space-y-6">
                                             {news.map((item, index) => (
                                                 <div key={index} className="bg-gray-800 rounded-lg p-4 hover:bg-gray-700 transition-colors">
                                                     <div className="flex flex-col md:flex-row">
                                                         {item.image_url && ( <div className="w-full md:w-1/4 mb-4 md:mb-0 md:mr-4"><img src={item.image_url} alt={item.title} className="w-full h-32 object-cover rounded-lg" onError={(e) => { e.target.onerror = null; e.target.style.display = 'none'; }} /></div> )}
                                                         <div className={item.image_url ? "w-full md:w-3/4" : "w-full"}>
                                                             <h3 className="text-lg font-medium mb-2"><a href={item.url} target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:text-blue-300 transition-colors">{item.title}</a></h3>
                                                             <div className="flex items-center text-sm text-gray-400 mb-2"><span className="mr-3">{item.source}</span><span>{formatNewsDate(item.published_at)}</span></div>
                                                             <p className="text-gray-300 text-sm">{item.summary}</p>
                                                             <a href={item.url} target="_blank" rel="noopener noreferrer" className="inline-block mt-3 text-sm text-blue-400 hover:text-blue-300 transition-colors">Read more →</a>
                                                         </div>
                                                     </div>
                                                 </div>
                                             ))}
                                         </div>
                                     )}
                                 </div>
                             </div> {/* End News */}

                             {/* --- Investors/Business Section --- */}
                            <div className={activeTab === 'investors' ? 'block' : 'hidden'}>
                                 <div className="bg-nav rounded-lg shadow-xl p-6 mb-6">
                                     <h2 className="text-xl font-semibold mb-6">Investor Information</h2>
                                     <div className="space-y-4"> {/* Added spacing */}
                                         <div>
                                             <h3 className="text-lg font-medium mb-2 text-gray-300">Official Links</h3>
                                             <div className="flex flex-col space-y-2 items-start bg-gray-800 p-4 rounded-lg">
                                                 {/* SEC Filings */}
                                                 <a href={secUrl} target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:text-blue-300 transition-colors inline-flex items-center">
                                                     <span>SEC Filings (EDGAR)</span>
                                                     <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 ml-1" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" /></svg>
                                                 </a>
                                                 {/* Investor Relations */}
                                                 <a href={investorUrl} target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:text-blue-300 transition-colors inline-flex items-center">
                                                     <span>Investor Relations Website</span>
                                                      <svg className="h-4 w-4 ml-1" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round"><path d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4"/><path d="M14 4h6v6M20 4L10 14"/></svg>
                                                 </a>
                                             </div>
                                         </div>
                                        
                                     </div>
                                 </div>
                             </div> {/* End Investors */}
                         </div> {/* End Tab Content Area */}


                        {/* Data Sources Footer */}
                        <div className="bg-nav rounded-lg shadow-xl p-4 text-center text-sm text-gray-400 mt-6">
                            Last updated: {new Date().toLocaleDateString()}
                        </div>
                    </>
                )}
                 {/* Show message if no company data and not loading */}
                {!loading && !company && !error && (
                     <div className="text-center text-gray-500 mt-10">
                         <p>Enter a ticker symbol or use the screener to find companies.</p>
                     </div>
                 )}
            </div>
        </div>
    );
};

export default CompanyDetail;