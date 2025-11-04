import React, { useContext, useState } from 'react';
import { useGoogleLogin } from '@react-oauth/google';
import axios from 'axios';
import { AuthContext } from '../context/AuthContext';

export default function LoginButton() {
  const { login } = useContext(AuthContext);
  const [error, setError] = useState('');

  const loginAction = useGoogleLogin({
    onSuccess: async (tokenResponse) => {
      try {
        const res = await axios.get('https://www.googleapis.com/oauth2/v3/userinfo', {
          headers: { Authorization: `Bearer ${tokenResponse.access_token}` },
        });
        login(res.data);
        setError('');
      } catch (err) {
        console.error('Error fetching user info: ', err);
        setError('Login Failed');
      }
    },
    onError: () => setError('Login Failed'),
  });

  return (
    <div>
      <button
        onClick={() => loginAction()}
        className="w-full mt-2 px-3 py-1.5 bg-teal-600 hover:bg-teal-700 rounded text-sm transition-colors"
      >
        Login / Sign Up
      </button>
      {error && <p>{error}</p>}
    </div>
  );
}
