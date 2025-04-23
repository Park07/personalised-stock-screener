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
          </p>
          
          <div className="bg-gray-800 p-6 rounded-lg shadow-lg">
            <ul className="text-gray-300 space-y-3 list-disc pl-5">
              <li>Structured, enriched financial event data to make faster, more informed decisions</li>
              <li>Clear advice to identify market trends, opportunities, and manage risk</li>
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
  </div>
);
};

export default Dashboard;
