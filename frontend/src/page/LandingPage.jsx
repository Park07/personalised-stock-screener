import { useNavigate } from 'react-router-dom';
import background from '../assets/background.jpg';
import { FaBolt, FaDatabase, FaTachometerAlt, FaPlug, FaServer } from 'react-icons/fa';
import { SiSwagger } from 'react-icons/si';

const LandingPage = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex flex-col">

      <div className="relative flex-grow flex flex-col justify-center items-center p-4 bg-center bg-no-repeat bg-cover" style={{ backgroundImage: `linear-gradient(rgba(0, 0, 0, 0.7), rgba(0, 0, 0, 0.7)), url(${background})` }}>
        <div className="text-center max-w-4xl mx-auto">
          <h1 className="text-6xl md:text-8xl font-bold text-white mb-4">FOXTROT</h1>
          <p className="text-2xl md:text-4xl text-gray-300 mb-8">Financial Events Microservice</p>
          <p className="text-xl text-gray-300 mb-12 max-w-2xl mx-auto">
          Your comprehensive platform for market analysis and investment decisons.
          </p>

          <div className="flex flex-col sm:flex-row justify-center space-y-4 sm:space-y-0 sm:space-x-4">
            <button
              onClick={() => navigate('/register')}
              className="px-8 py-4 bg-blue-600 text-xl text-white rounded-lg shadow-lg hover:bg-blue-700 transition duration-300 transform hover:scale-105">
              Get Started
            </button>

            <button
              onClick={() => navigate('/login')}
              className="px-8 py-4 bg-transparent border-2 border-white text-xl text-white rounded-lg hover:bg-white hover:text-gray-900 transition duration-300 transform hover:scale-105">
              Login
            </button>
          </div>
        </div>
      </div>

      <div className="bg-gray-100 py-16 px-4">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-4xl font-bold text-center text-gray-800 mb-12">Key Benefits</h2>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            <div className="bg-white p-6 rounded-lg shadow-md hover:shadow-xl transition duration-300">
              <FaBolt className="text-4xl text-blue-600 mb-4" />
              <h3 className="text-xl font-semibold mb-2">Real-Time Processing</h3>
              <p className="text-gray-600">
                Instant updates on economic indicators and price trends .
              </p>
            </div>

            <div className="bg-white p-6 rounded-lg shadow-md hover:shadow-xl transition duration-300">
              <FaDatabase className="text-4xl text-blue-600 mb-4" />
              <h3 className="text-xl font-semibold mb-2">Data Enrichment</h3>
              <p className="text-gray-600">
                Cleaned and structured data from Alpaca API, ready for analysis and decision-making.
              </p>
            </div>

            <div className="bg-white p-6 rounded-lg shadow-md hover:shadow-xl transition duration-300">
              <FaPlug className="text-4xl text-blue-600 mb-4" />
              <h3 className="text-xl font-semibold mb-2">Seamless Integration</h3>
              <p className="text-gray-600">
                Supports JSON, WebSockets, and multiple programming languages for easy adoption.
              </p>
            </div>


          </div>
        </div>
      </div>
    </div>
  );
};

export default LandingPage;