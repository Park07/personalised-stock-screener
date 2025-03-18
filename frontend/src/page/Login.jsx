import { useState } from 'react';
import axios from 'axios';
import TextInput from '../component/TextInput';
import AuthButton from '../component/AuthButton';
import AuthContainer from '../component/AuthContainer';

function Login({ handleSuccess }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false); 
  const [errorMessage, setErrorMessage] = useState(''); 

  const login = (e) => {
    e.preventDefault();
    setLoading(true);
    axios.post('http://127.0.0.1:5000/login', {
      username: username,
      password: password,
    })
      .then((response) => {
        handleSuccess(response.data.token);
        setLoading(false);
      })
      .catch((error) => {
        setErrorMessage(error.message); 
        setLoading(false);
      });
  }

  return (
    <AuthContainer>
      <h2 className="text-2xl font-semibold text-center text-gray-200">Login</h2>
      <form onSubmit={login} className="space-y-4">
        <div>
          <label htmlFor="username" className="block text-sm font-medium text-gray-400">Username</label>
          <TextInput
            type="username"
            id="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="Enter your username"
          />
        </div>
        <div>
          <label htmlFor="password" className="block text-sm font-medium text-gray-400">Password</label>
          <TextInput
            type="password"
            id="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Enter your password"
          />
        </div>
        <AuthButton type="submit" disabled = {loading}>
          {loading ? 'Logging in...' : 'Login'}
        </AuthButton>
      </form>
      {errorMessage && (
        <p className="text-red-500 text-sm mt-4">{errorMessage}</p> // Display error message
      )}
    </AuthContainer>
  );
}

export default Login;
