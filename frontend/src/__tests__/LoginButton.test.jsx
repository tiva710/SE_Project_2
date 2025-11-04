import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import LoginButton from '../components/LoginButton';
import { AuthContext } from '../context/AuthContext';
import axios from 'axios';

jest.mock('@react-oauth/google', () => ({
  useGoogleLogin: jest.fn(),
  GoogleOAuthProvider: ({ children }) => <>{children}</>,
}));

jest.mock('axios');

import { useGoogleLogin } from '@react-oauth/google';

describe('LoginButton Component', () => {
  const mockLogin = jest.fn();

  const renderWithAuth = () => {
    render(
      <AuthContext.Provider value={{ login: mockLogin }}>
        <LoginButton />
      </AuthContext.Provider>
    );
  };

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('renders Google login button', () => {
    renderWithAuth();
    const button = screen.getByRole('button');
    expect(button).toBeInTheDocument();
  });

  test('calls login function on click', async () => {
    const fakeToken = { access_token: 'super-real-token' };
    const fakeUser = { email: 'myemail@test.com', sub: '123' };

    useGoogleLogin.mockImplementation(
      ({ onSuccess }) =>
        () =>
          onSuccess(fakeToken)
    );

    axios.get.mockResolvedValue({ data: fakeUser });

    renderWithAuth();
    fireEvent.click(screen.getByRole('button'));

    //login is async
    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith(fakeUser);
    });
  });

  test('handles login failure correctly', async () => {
    useGoogleLogin.mockImplementation(
      ({ onError }) =>
        () =>
          onError(new Error('Login Failed'))
    );

    renderWithAuth();
    fireEvent.click(screen.getByRole('button'));

    await waitFor(() => {
      expect(screen.getByText(/Login Failed/i)).toBeInTheDocument();
    });
  });

  test('prevents multiple login clicks', async () => {
    let resolveFn;
    useGoogleLogin.mockImplementation(({ onSuccess }) => () => {
      new Promise((resolve) => {
        resolveFn = resolve;
      }).then(() => onSuccess({ email: 'test@test.com' }));
    });

    renderWithAuth();
    const button = screen.getByRole('button');
    fireEvent.click(button);
    fireEvent.click(button);

    resolveFn();
    await waitFor(() => expect(mockLogin).toHaveBeenCalledTimes(1));
  });
});
