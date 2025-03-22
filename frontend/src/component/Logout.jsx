import axios from 'axios'
import { useNavigate } from 'react-router-dom';


const Logout = ({ token, setToken, setStore }) => {
  const navigate = useNavigate();

  const logout = () => {
    axios.post('http://35.169.25.122/logout', {
        token: token
    })
      .then(() => {
        localStorage.removeItem('token');
        setToken(null);
        setStore(null);
        navigate('/frontend');
      })
  }

  return <button onClick={logout}>Logout</button>;
}

export default Logout