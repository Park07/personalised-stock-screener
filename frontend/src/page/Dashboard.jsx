import { useState } from 'react';
import axios from 'axios';
import AuthButton from '../component/AuthButton';
import { Link, useLocation } from 'react-router-dom';
import stockImage from '../assets/stocks.png';
import cryptoImage from '../assets/crypto.png';


const Dashboard = function ({ token, store, setStore }) {

//   const reallySetStore = (newStore) => {
//     axios.put('http://localhost:5005/store', {
//       store: newStore,
//     }, {
//       headers: { Authorization: `Bearer ${token}` }
//     })
//       .then(() => {
//         setStore(newStore);
//       })
//   }
// ;


return (
  <div className="bg-gray-900 min-h-screen text-gray-200 py-8 px-6 md:px-12">
  <div className="max-w-7xl mx-auto">

    <h1 className="text-4xl font-bold border-b-4 border-blue-500 pb-2 mb-10">
      Dashboard
    </h1>

    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

      <div className="lg:col-span-1 bg-gray-800 p-8 rounded-xl shadow-xl">
        <p className="mb-6 leading-relaxed">
          Our Financial Events Microservice delivers real-time, structured, and enriched financial data, enabling faster and informed decision-making for investors, hedge funds, and fintech platforms.
        </p>

        <ul className="space-y-2 pl-5 list-disc">
          <li>Structured, real-time financial data</li>
          <li>Market analysis and trend identification</li>
          <li>Top 100 stock price predictions</li>
          <li>Easy-to-use API with Swagger integration</li>
        </ul>

        <div className="mt-8 flex flex-col gap-4">
          <Link to="/frontend/stocks"
          className="w-full px-6 py-3 bg-blue-600 text-white rounded-md shadow-md hover:bg-blue-700 transition duration-300 text-center"
            >Explore Stocks Data</Link>
          <Link to="/frontend/crypto" className="w-full px-6 py-3 bg-purple-600 text-white rounded-md shadow-md hover:bg-purple-700 transition duration-300 text-center"
            >Explore Crypto Data</Link>
          <Link to="/frontend/screener" className="w-full px-6 py-3 bg-indigo-500 text-white rounded-md shadow-md hover:bg-indigo-600 transition duration-300 text-center"
            >Explore Stock Screener</Link>
          <a href="https://app.swaggerhub.com/apis/student-a85-ad6/SENG3011_H17ALGOTRADING/1.0.0" target="_blank"
            className="w-full px-6 py-3 bg-gray-600 text-white rounded-md shadow-md hover:bg-gray-700 transition duration-300 text-center"
            >View API Documentation</a>
        </div>
      </div>

      <div className="lg:col-span-2 grid grid-cols-1 md:grid-cols-2 gap-8">
        <Link to="/frontend/stocks" className="group relative overflow-hidden rounded-xl shadow-lg">
          <img src={stockImage} alt="Stocks" className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110" />
          <div className="absolute inset-0 bg-gradient-to-t from-black/80 to-transparent flex items-end p-6">
            <h3 className="text-2xl font-semibold">Stock Market Data</h3>
          </div>
        </Link>

        <Link to="/frontend/crypto" className="group relative overflow-hidden rounded-xl shadow-lg">
          <img src={cryptoImage} alt="Crypto" className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110" />
          <div className="absolute inset-0 bg-gradient-to-t from-black/80 to-transparent flex items-end p-6">
            <h3 className="text-2xl font-semibold">Cryptocurrency Data</h3>
          </div>
        </Link>
      </div>
    </div>

    <div className="mt-12 bg-gray-800 rounded-xl p-8 shadow-xl">
      <h2 className="text-2xl font-semibold text-center mb-4">Getting Started Guide</h2>
      <ol className="list-decimal list-inside space-y-3 max-w-4xl mx-auto">
        <li><strong>Select your market:</strong> <span className="text-blue-400">Stocks</span> or <span className="text-purple-400">Crypto</span>.</li>
        <li><strong>Enter the asset:</strong> Provide a valid asset name.</li>
        <li><strong>Select timeframe:</strong> Analyze historical trends.</li>
        <li><strong>Analysis period:</strong> Tailor insights (daily, weekly, long-term).</li>
        <li><strong>Submit:</strong> Visualize detailed analysis with clear recommendations.</li>
        <li><strong>Bonus:</strong> Price predictions for top 100 stocks.</li>
      </ol>
    </div>
  </div>
</div>
);

};

export default Dashboard;
