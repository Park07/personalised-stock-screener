import React from 'react';

// Simple placeholder for company logo based on Ticker
const CompanyLogo = ({ ticker }) => (
  <div className="w-8 h-8 rounded-full flex items-center justify-center text-white text-xs font-bold bg-gradient-to-br from-gray-600 to-gray-800 mr-3">
    {ticker?.substring(0, 2) || '??'}
  </div>
);

// The table component
const RankedCompaniesTable = ({
  companies = [],        // The array from /api/rank
  onSelect,            // Function to call when checkbox changes (passes ticker)
  selectedCompanies,   // Set or Array of selected tickers
  onCompanyClick       // Function to call when name is clicked (passes ticker)
}) => {

  if (!companies || companies.length === 0) {
    return <p className="text-gray-400 text-center py-4">No companies match your criteria.</p>;
  }

  // Determine if a ticker is selected (works for Set or Array)
  const isSelected = (ticker) => selectedCompanies instanceof Set ? selectedCompanies.has(ticker) : selectedCompanies.includes(ticker);

  return (
    <div className="bg-[#1a1d26] rounded-lg shadow-xl overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full">
          <thead className="bg-gray-800">
            <tr>
              <th className="px-4 py-3 w-12 text-center text-xs font-medium text-gray-300 uppercase tracking-wider">
                 {/* Optional: Select All Checkbox can go here */}
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                Company
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                Recommendation Summary
              </th>
            </tr>
          </thead>
          <tbody className="bg-gray-700 divide-y divide-gray-600">
            {companies.map((company) => (
              <tr
                key={company.ticker}
                className={`hover:bg-gray-600 transition-colors ${isSelected(company.ticker) ? 'bg-gray-600' : ''}`}
              >
                <td className="px-4 py-3 text-center">
                  <input
                    type="checkbox"
                    aria-label={`Select ${company.name}`}
                    checked={isSelected(company.ticker)}
                    onChange={() => onSelect(company.ticker)} // Call handler with ticker
                    className="form-checkbox h-5 w-5 rounded border-gray-500 text-blue-500 bg-gray-800 focus:ring-blue-400 focus:ring-offset-gray-700"
                  />
                </td>
                <td className="px-4 py-4 whitespace-nowrap">
                   <div className="flex items-center">
                     <CompanyLogo ticker={company.ticker} />
                     <div>
                        <div
                          className="font-medium text-white hover:text-blue-400 cursor-pointer"
                          onClick={(e) => {
                            e.preventDefault(); // Prevent row click if needed
                            onCompanyClick(company.ticker); // Trigger detail view navigation
                           }}
                         >
                            {company.name || 'N/A'} ({company.ticker})
                         </div>
                         {/* Optional: Display sector from cache if needed/available */}
                         {/* <div className="text-sm text-gray-400">{company.sector || 'N/A'}</div> */}
                     </div>
                   </div>
                </td>
                <td className="px-4 py-4 text-sm text-gray-300">
                  {company.recommendation || 'No summary available.'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default RankedCompaniesTable;