import { useNavigate } from 'react-router-dom';
import background from '../assets/background.jpg';


const LandingPage = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex flex-col justify-center items-center p-4 bg-center bg-no-repeat bg-cover" style={{ backgroundImage: `url(${background})` }}>
      <h1 className="text-8xl font-bold text-gray-100 mb-4">Welcome to FOXTROT</h1>
      <p className="text-4xl text-gray-300 mb-8">Never make poor investments again.</p>
      
      <div className="flex space-x-4">
        <button 
          onClick={() => navigate('/frontend/login')}
          className="px-6 py-3 bg-nav text-xl text-white rounded-md shadow-md hover:bg-blue-700 transition duration-300">
          Login
        </button>
        
        <button 
          onClick={() => navigate('/frontend/register')}
          className="px-6 py-3 bg-nav text-xl text-white rounded-md shadow-md hover:bg-blue-700 transition duration-300">
          Register
        </button>
      </div>
    </div>
  );
};

export default LandingPage;