import { Link, useLocation } from 'react-router-dom';
import Logout from './Logout';

function Nav({ token, setToken, setStore }) {
  const location = useLocation();

  // Hide Navbar on landing page
  if (location.pathname === '/frontend') {
    return null;
  }

  return (
    <header className="flex justify-between items-center bg-nav px-6 py-4 shadow-md">
      {/* Left-side nav links */}
      <nav className="flex gap-6 items-center font-semibold text-base">
        {!token ? (
          <>
            <Link to="/frontend">
              <div className="px-4 py-2 hover:bg-blue-950 hover:text-white rounded-md transition-all cursor-pointer text-gray-400">Home</div>
            </Link>
            <Link to="/frontend/register">
              <div className="px-4 py-2 hover:bg-blue-950 hover:text-white rounded-md transition-all cursor-pointer text-gray-400">Register</div>
            </Link>
            <Link to="/frontend/login">
              <div className="px-4 py-2 hover:bg-blue-950 hover:text-white rounded-md transition-all cursor-pointer text-gray-400">Login</div>
            </Link>
          </>
        ) : (
          <>
            <Link to="/frontend/dashboard">
              <div className="px-4 py-2 hover:bg-blue-950 hover:text-white rounded-md transition-all cursor-pointer text-gray-400">Dashboard</div>
            </Link>
            <Link to="/frontend/analysis">
              <div className="px-4 py-2 hover:bg-blue-950 hover:text-white rounded-md transition-all cursor-pointer text-gray-400">Analysis</div>
            </Link>
            <Link to="/frontend/stocks">
              <div className="px-4 py-2 hover:bg-blue-950 hover:text-white rounded-md transition-all cursor-pointer text-gray-400">Stocks</div>
            </Link>
            <Link to="/frontend/crypto">
              <div className="px-4 py-2 hover:bg-blue-950 hover:text-white rounded-md transition-all cursor-pointer text-gray-400">Crypto</div>
            </Link>
          </>
        )}
      </nav>

      {/* Right-side logout */}
      {token && (
        <div className="ml-auto">
          <div className="px-4 py-2 hover:bg-blue-950 hover:text-white rounded-md transition-all cursor-pointer text-gray-400">
            <Logout token={token} setToken={setToken} setStore={setStore} />
          </div>
        </div>
      )}
    </header>
  );
}

export default Nav;
