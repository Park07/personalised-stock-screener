import { useState } from 'react';
import axios from 'axios';
import TextInput from '../component/TextInput';
import AuthButton from '../component/AuthButton';
import AuthContainer from '../component/AuthContainer';
import { useNavigate } from 'react-router-dom';

function Register() {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errorMessage, setErrorMessage] = useState(''); 

  const register = (event) => {
    event.preventDefault(); 
    axios.post('http://127.0.0.1:5000/register', {
      username: username,
      email: email,
      password: password,
    })
      .then(() => {
        useNavigate('/frontend/login')
      })
      .catch((error) => {
        setErrorMessage(error.message); 
      });
  }
  return (
    <AuthContainer>
      <h2 className="text-2xl font-semibold text-center text-gray-200">Register</h2>
      <form onSubmit={register} className="space-y-4">
        <div>
          <label htmlFor="email" className="block text-sm font-medium text-gray-400">Username</label>
          <TextInput
            type="username"
            id="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="Enter your username"
          />
        </div>
        <div>
          <label htmlFor="email" className="block text-sm font-medium text-gray-400">Email</label>
          <TextInput
            type="email"
            id="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Enter your email"
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
        <AuthButton type="submit">
          Register
        </AuthButton>
      </form>
      {errorMessage && (
        <p className="text-red-500 text-sm mt-4">{errorMessage}</p> 
      )}
    </AuthContainer>
  );
}

export default Register;
