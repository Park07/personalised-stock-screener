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
  <div className="p-4 md:p-8 flex flex-col items-start justify-start bg-background min-h-screen">
    <div className="w-full mb-8">
      <h1 className="text-3xl md:text-4xl font-semibold text-gray-100 mb-2 inline-block border-b-2 border-blue-500 pb-1">Dashboard</h1>    
    </div>
    
    <div className="flex flex-col md:flex-row w-full gap-8">

      <div className="w-full md:w-1/2 lg:w-2/5 flex flex-col">
        <div className="bg-gray-800 p-6 rounded-lg shadow-lg">
          <p className="text-gray-300 text-lg leading-relaxed">
            Our Financial Events Microservice provides real-time, structured, and enriched financial event data, 
            enabling trading firms, hedge funds, and fintech platforms to make faster and more informed decisions.
            We train LLM accross hundreds of stocks to give you the most accurate analysis for your investment goals.
          </p>
          
          <div className="bg-gray-800 p-6 rounded-lg shadow-lg">
            <ul className="text-gray-300 space-y-3 list-disc pl-5">
              <li>Structured, enriched financial event data to make faster, more informed decisions</li>
              <li>Clear analysis to identify market trends, opportunities, and manage risk</li>
              <li>Price prediction for the top 100 stocks</li>
              <li>Seamless API integration with comprehensive Swagger documentation</li>
            </ul>
          </div>
          
          <div className="flex flex-col space-y-4">
            <Link to="/frontend/stocks" 
              className="w-full px-6 py-3 bg-blue-600 text-white rounded-md shadow-md hover:bg-blue-700 transition duration-300 text-center"
            >
              Explore Stocks Data
            </Link>

            <Link to="/frontend/crypto" 
              className="w-full px-6 py-3 bg-purple-600 text-white rounded-md shadow-md hover:bg-purple-700 transition duration-300 text-center"
            >
              Explore Crypto Data
            </Link>

            <a href="https://app.swaggerhub.com/apis/student-a85-ad6/SENG3011_H17ALGOTRADING/1.0.0" target="_blank" rel="noopener noreferrer"
            className="w-full px-6 py-3 bg-gray-700 text-white rounded-md shadow-md hover:bg-gray-600 transition duration-300 text-center"
            > 
              View API Documentation 
            </a>
          </div>
        </div>
      </div>
      
      <div className="relative group overflow-hidden rounded-xl shadow-lg">
        <Link to="/frontend/stocks">
          <img 
            src={stockImage} 
            alt="Stocks" 
            className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/70 to-transparent flex items-end p-6 transition-transform duration-300 group-hover:scale-105">
            <h3 className="text-2xl font-bold text-white">Stock Market Data</h3>
          </div>
        </Link>
      </div>

      <div className="relative group overflow-hidden rounded-xl shadow-lg">
        <Link to="/frontend/crypto">
          <img 
            src={cryptoImage} 
            alt="Crypto" 
            className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/70 to-transparent flex items-end p-6 transition-transform duration-300 group-hover:scale-105">
            <h3 className="text-2xl font-bold text-white">Cryptocurrency Data</h3>
          </div>
        </Link>
      </div>
    </div>

    <div className="mt-12 w-full text-center bg-gray-800 p-6 rounded-lg shadow-lg">
      <h2 className="text-2xl font-semibold text-white mb-2">Need Help Getting Started?</h2>
      <p className="text-gray-300 mb-4">
        Here's a quick guide to help you make the most of our Financial Events Microservice:
      </p>
      <ol className="text-left text-gray-300 list-decimal list-inside space-y-3 max-w-2xl mx-auto">
        <li>
          <strong>Select your market:</strong> Choose whether you're interested in <span className="text-blue-400 font-semibold">Crypto</span> or <span className="text-purple-400 font-semibold">Stocks</span>.
        </li>
        <li>
          <strong>Enter the asset name:</strong> Provide a valid cryptocurrency or stock name you want to explore.
        </li>
        <li>
          <strong>Choose a time period for the graph:</strong> View historical trends over your preferred time range.
        </li>
        <li>
          <strong>Select your analysis period:</strong> Tailor insights based on how frequently you plan to trade — daily, weekly, or long-term.
        </li>
        <li>
          <strong>Submit your query:</strong> Get a visual graph, detailed analysis with recommendations to <span className="text-green-400 font-semibold">Buy</span>, <span className="text-yellow-400 font-semibold">Hold</span>, or <span className="text-red-400 font-semibold">Sell</span>.
        </li>
        <li>
          <strong>Bonus:</strong> If it's a top 100 stock, you'll also receive a <span className="text-teal-400 font-semibold">price prediction</span> based on our proprietary model.
        </li>
      </ol>
    </div>

  </div>
);
};

export default Dashboard;
