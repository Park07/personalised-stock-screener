// InfoTooltip for specific financial terms
import React from 'react';
import Tippy from '@tippyjs/react';
import 'tippy.js/dist/tippy.css';

const InfoTooltip = ({ term }) => {
  // Define explanations for financial terms
  const explanations = {
    "P/E Ratio": "Price-to-Earnings ratio. Shows how much investors pay per dollar of earnings. Lower values may indicate better 'bargain'. Generally 15 - 25 is good, tech companies are usually overvalued and isn't unusual to have pe over 30 but healthy",
    "EV/EBITDA": "Enterprise Value to EBITDA. Compares company value to earnings before interest, taxes, depreciation & amortisation.",
    "PEG Ratio": "Price/Earnings to Growth ratio. A PEG under 1.0 suggests the stock may be undervalued relative to its growth.",
    "P/S Ratio": "Price-to-Sales ratio. Shows how much investors pay per dollar of revenue. Lower is generally better.",
    "Dividend Yield": "Annual dividends as a percentage of stock price. Shows income return from dividends.",
    "Debt/Equity": "Total debt divided by shareholders' equity. Higher ratios indicate more financial leverage and risk, which can amplify both gains and losses.",
    "Debt Ratio": "Total debt divided by total assets. Shows what percentage of assets are financed by debt.",
    "Current Ratio": "Current assets divided by current liabilities. Above 1.0 means company can pay short-term debts. 1.5 - 3.0 is healthy",
    "Revenue Growth (1Y)": "Year-over-year percentage increase in total revenue. Higher growth indicates expanding business.",
    "Net Income Growth (1Y)": "Year-over-year percentage change in profit. Shows if the company is becoming more profitable.",
    "OCF Growth (1Y)": "Operating Cash Flow growth. Shows if the company is generating more cash from core operations."
  };

  const explanation = explanations[term];

  // Don't show tooltip if we don't have an explanation for this term
  if (!explanation) {
    return null;
  }

  return (
    <Tippy content={explanation}>
      <button
        className="ml-1 text-gray-400 hover:text-blue-400 focus:outline-none transition-colors"
        type="button"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="w-4 h-4"
        >
          <circle cx="12" cy="12" r="10"></circle>
          <line x1="12" y1="16" x2="12" y2="12"></line>
          <line x1="12" y1="8" x2="12.01" y2="8"></line>
        </svg>
      </button>
    </Tippy>
  );
};

export default InfoTooltip;