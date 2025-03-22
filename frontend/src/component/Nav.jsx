import { Link, useLocation } from 'react-router-dom';
import Logout from './Logout';

function Nav ({ token, setToken, setStore }) {
  const location = useLocation();
  // Dont display Navbar landing page
  if (location.pathname === '/') {
    return null;
  }
  return (
    <header className="flex justify-between items-center bg-nav">
      <ul className="flex items-center gap-12 font-semibold text-base">
        {!token ? (
          <>
            <Link to="/frontend">
              <li className="p-3 hover:bg-blue-950 hover:text-white rounded-md transition-all cursor-pointer text-gray-400">Home</li>
            </Link>
            <Link to="/frontend/register">
              <li className="p-3 hover:bg-blue-950 hover:text-white rounded-md transition-all cursor-pointer text-gray-400">Register</li>
            </Link>
            <Link to="/frontend/login">
              <li className="p-3 hover:bg-blue-950 hover:text-white rounded-md transition-all cursor-pointer text-gray-400">Login</li>
            </Link>
          </>
        ) : null}
      </ul>

      {token && (
        <ul className="flex items-center font-semibold text-base">
          <li className="p-3 hover:bg-blue-950 hover:text-white rounded-md transition-all cursor-pointer text-gray-400">
            <Logout token={token} setToken={setToken} setStore={setStore} className="block w-full h-full" />
          </li>
        </ul>
      )}
    </header>
  )
}

export default Nav