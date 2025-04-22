import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useLocation, Routes, Route, useNavigate } from 'react-router-dom';
import './App.css'
import Nav from './component/Nav';
import LandingPage from './page/LandingPage';
import Login from './page/Login';
import Register from './page/Register';
import Dashboard from './page/Dashboard';
import Stocks from './page/Stocks';
import Crypto from './page/Crypto';
import Analysis from './page/Analysis';
import Screener from './page/Screener';

function App() {
    const [token, setToken] = useState(localStorage.getItem('token'));
    const [store, setStore] = useState(null);
    const navigate = useNavigate();
    const location = useLocation();
  
    const handleNewToken = (newToken) => {
      localStorage.setItem('token', newToken);
      setToken(newToken);
      navigate('/frontend/dashboard')
    }

    // useEffect(() => {
    //   if (token) {
    //     axios.get('http://localhost:5005/store', {
    //       headers: { Authorization: `Bearer ${token}` }
    //     })
    //       .then(response => {
    //         setStore(response.data.store);
    //       })
    //       .catch(error => {
    //         alert(error.response.data.error);
    //       });
    //   }  }, [token]);

    useEffect(() => {
      if (!token && !(['/frontend', '/frontend/login', '/frontend/register'].includes(location.pathname))) navigate('/frontend');
      if (token && ['/frontend/login', '/frontend/register'].includes(location.pathname)) navigate('/frontend/dashboard');
    }, [token, location.pathname])  

    return (
        <> 
          <div>
            <Nav token={token} setToken={setToken} setStore={setStore} />
          </div>
          <Routes>
            <Route path="/frontend" element={<LandingPage />} />
            <Route path="/frontend/login" element={<Login token={setToken} handleSuccess={handleNewToken} />} />
            <Route path="/frontend/register" element={<Register token={setToken} />} />
            <Route path="/frontend/dashboard" element={<Dashboard token={token} store={store} setStore={setStore} />} />
            <Route path="/frontend/Crypto" element={<Crypto />} />
            <Route path="/frontend/Stocks" element={<Stocks />} />
            <Route path="/frontend/Analysis" element={<Analysis />} />
            <Route path="/frontend/screener" element={<Screener />} />


          </Routes>
        </>
      );  
}

export default App;
