import { useState } from 'react';
import axios from 'axios';

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
;


  return ( 
    <div className="p-4 md:p-8 flex flex-col md:flex-row items-start justify-start bg-background min-h-screen">
      <div className="w-full md:w-1/4 mb-4 md:mb-0">
        <h1 className="text-3xl md:text-4xl font-semibold text-gray-100 mb-5 md:text-left">Dashboard</h1>
      </div>
    </div>
  );
};

export default Dashboard;
