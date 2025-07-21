import React from 'react';
import { useNavigate } from 'react-router-dom';

const Logout = ({ setToken }) => {
  const navigate = useNavigate();

  const handleLogout = () => {
    // 1. Remove the token from the browser's memory
    localStorage.removeItem('token');
    // 2. Update the application's state to know we are logged out
    setToken(null);
    // 3. Send the user back to the home page
    navigate('/');
  };

  return (
    <div
      onClick={handleLogout}
      className="px-4 py-2 hover:bg-blue-950 hover:text-white rounded-md transition-all cursor-pointer text-gray-400"
    >
      Logout
    </div>
  );
};

export default Logout;