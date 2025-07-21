import React, { useState, useEffect } from 'react';
import { useLocation, Routes, Route, useNavigate } from 'react-router-dom';
import './App.css';
import Nav from './component/Nav';
import LandingPage from './page/LandingPage';
import Login from './page/Login';
import Register from './page/Register';
import Dashboard from './page/Dashboard';
import Stocks from './page/Stocks';
import Crypto from './page/Crypto';
import Screener from './page/Screener';
import CompanyDetail from './page/CompanyDetail';
import Logout from './page/Logout';

function App() {
    const [token, setToken] = useState(localStorage.getItem('token'));
    const navigate = useNavigate();
    const location = useLocation();

    const handleNewToken = (newToken) => {
        localStorage.setItem('token', newToken);
        setToken(newToken);
        // Navigate to the simple path. The browser will show /frontend/dashboard.
        navigate('/dashboard');
    };

    useEffect(() => {
        const isAuthPage = ['/login', '/register'].includes(location.pathname);
        const isLandingPage = location.pathname === '/';

        // If user is logged IN and tries to go to login/register, redirect to dashboard.
        if (token && isAuthPage) {
            navigate('/dashboard');
        }

        // If user is logged OUT and is NOT on the landing or an auth page, redirect to the landing page.
        if (!token && !isLandingPage && !isAuthPage) {
            navigate('/');
        }
    }, [token, location.pathname, navigate]);

    return (
        <>
            <Nav token={token} setToken={setToken} />
            <Routes>
                {/* All paths are now simple and relative */}
                <Route path="/" element={<LandingPage />} />
                <Route path="/login" element={<Login handleSuccess={handleNewToken} />} />
                <Route path="/register" element={<Register />} />
                <Route path="/logout" element={<Logout setToken={setToken} />} />
                <Route path="/dashboard" element={<Dashboard token={token} />} />
                <Route path="/crypto" element={<Crypto />} />
                <Route path="/stocks" element={<Stocks />} />
                <Route path="/screener" element={<Screener />} />
                <Route path="/company/:ticker" element={<CompanyDetail />} />
            </Routes>
        </>
    );
}

export default App;