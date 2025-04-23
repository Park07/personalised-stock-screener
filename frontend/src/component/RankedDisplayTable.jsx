import React, { useState } from 'react';

// --- Reusable Helper Components (Keep from your EnhancedResultsTable) ---

// Info tooltip component
const InfoTooltip = ({ title, content }) => {
  const [isVisible, setIsVisible] = useState(false);
  return (
    <div className="relative inline-block ml-1 align-middle">
      <button /* ... SVG and handlers ... */ > {/* ... */}</button>
      {isVisible && (
        <div className="absolute z-20 w-60 p-2 mt-2 text-sm text-white bg-gray-700 rounded-md shadow-lg -translate-x-1/2 left-1/2 bottom-full mb-1">
          {/* ... Tooltip content ... */}
        </div>
      )}
    </div>
  );
};

// Company logo component (simple initials)
const CompanyLogo = ({ ticker }) => (
  <div className="w-8 h-8 rounded-full flex items-center justify-center text-white text-xs font-bold bg-gradient-to-br from-indigo-600 to-purple-700 mr-3 flex-shrink-0">
    {ticker?.substring(0, 2) || '??'}
  </div>
);

// --- Main Table Component ---
const RankedDisplayTable = ({
  companies = [],         // Array from /api/rank (already formatted by backend)
  onSelect,             // Function to call when checkbox changes (passes ticker)
  selectedCompanies,    // Set or Array of selected tickers
  onCompanyClick        // Function to call when name is clicked (passes ticker)
}) => {

  if (!companies || companies.length === 0) {
    return <p className="text-gray-400 text-center py-4">No companies match your criteria.</p>;
  }

  const isSelected = (ticker) => selectedCompanies instanceof Set ? selectedCompanies.has(ticker) : selectedCompanies.includes(ticker);

  // Define columns based on data provided by the backend formatter
  const columns = [
    { id: 'select', label: '', width: 'w-12 text-center', tooltip: 'Select company' },
    { id: 'company', label: 'Company', width: 'min-w-[250px]', tooltip: 'Company name and ticker symbol' },
    { id: 'sector', label: 'Sector', tooltip: 'Industry sector' },
    { id: 'market_cap', label: 'Market Cap', tooltip: 'Market Capitalization' },
    { id: 'pe_ratio', label: 'P/E Ratio', tooltip: 'Price-to-Earnings Ratio (TTM)' },
    { id: 'roe', label: 'ROE', tooltip: 'Return on Equity (TTM)' },
    { id: 'profile_score', label: 'Score', tooltip: 'Profile match score (0-100)' },
    { id: 'recommendation', label: 'Summary', tooltip: 'Brief recommendation based on profile' },
  ];

  return (
    <div className="bg-gray-900 rounded-lg shadow-lg overflow-hidden border border-gray-700">
      <div className="overflow-x-auto">
        <table className="min-w-full">
          <thead className="bg-gray-800">
            <tr>
              {columns.map(col => (
                 <th key={col.id} className={`px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider ${col.width || ''}`}>
                   <div className="flex items-center">
                     {col.label}
                     {col.tooltip && <InfoTooltip title={col.label} content={col.tooltip} />}
                   </div>
                 </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-700">
            {companies.map((company) => (
              <tr
                key={company.ticker}
                className={`hover:bg-gray-800 transition-colors ${isSelected(company.ticker) ? 'bg-gray-700' : ''}`} // Highlight if selected
              >
                {/* Checkbox Cell */}
                <td className="px-4 py-3 text-center">
                  <input
                    type="checkbox"
                    aria-label={`Select ${company.name}`}
                    checked={isSelected(company.ticker)}
                    onChange={() => onSelect(company.ticker)}
                    className="form-checkbox h-4 w-4 rounded border-gray-600 text-blue-500 bg-gray-700 focus:ring-blue-500 focus:ring-offset-gray-900"
                  />
                </td>
                {/* Company Cell */}
                <td className="px-4 py-3 whitespace-nowrap">
                   <div className="flex items-center">
                     <CompanyLogo ticker={company.ticker} />
                     <div>
                        <div
                          className="font-medium text-white hover:text-blue-400 cursor-pointer"
                          onClick={() => onCompanyClick(company.ticker)} // Trigger detail view
                         >
                            {company.name || 'N/A'} ({company.ticker})
                         </div>
                     </div>
                   </div>
                </td>
                {/* Data Cells */}
                <td className="px-4 py-3 text-sm text-gray-300">{company.sector || 'N/A'}</td>
                <td className="px-4 py-3 text-sm text-gray-300 text-right">{company.market_cap || 'N/A'}</td>
                <td className="px-4 py-3 text-sm text-gray-300 text-right">{company.pe_ratio || 'N/A'}</td>
                <td className="px-4 py-3 text-sm text-gray-300 text-right">{company.roe || 'N/A'}</td>
                <td className="px-4 py-3 text-sm font-semibold text-white text-right">{company.profile_score || 'N/A'}</td>
                <td className="px-4 py-3 text-xs text-gray-400">{company.recommendation || 'N/A'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default RankedCompaniesTable;