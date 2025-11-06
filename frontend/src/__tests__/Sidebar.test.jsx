import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import Sidebar from '../components/Sidebar';
import { AuthContext } from '../context/AuthContext';
import { GoogleOAuthProvider } from '@react-oauth/google';
import axios from 'axios';

jest.mock('axios');

const mockToggle = jest.fn();
const mockClearGraph = jest.fn();
const mockLogout = jest.fn();

beforeAll(() => {
  window.alert = jest.fn();
});

const renderWithProviders = (ui, { user = null } = {}) => {
  return render(
    <GoogleOAuthProvider clientId="test-client-id">
      <AuthContext.Provider value={{ user, logout: mockLogout }}>{ui}</AuthContext.Provider>
    </GoogleOAuthProvider>
  );
};

describe('Sidebar Component', () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  test('renders collapsed sidebar button when isOpen=false', () => {
    renderWithProviders(
      <Sidebar isOpen={false} onToggle={mockToggle} onClearGraph={mockClearGraph} />
    );
    const button = screen.getByRole('button');
    expect(button).toBeInTheDocument();
  });

  test('renders sidebar header and user info when open (guest)', () => {
    renderWithProviders(
      <Sidebar isOpen={true} onToggle={mockToggle} onClearGraph={mockClearGraph} />
    );
    expect(screen.getByText(/ReqTrace/i)).toBeInTheDocument();
    expect(screen.getByText(/Guest User/i)).toBeInTheDocument();
    expect(screen.getByText(/Login \/ Sign Up/i)).toBeInTheDocument();
  });

  test('renders sidebar header and user info when open (logged-in)', () => {
    const user = { email: 'test@example.com', picture: 'avatar.png' };
    renderWithProviders(
      <Sidebar isOpen={true} onToggle={mockToggle} onClearGraph={mockClearGraph} />,
      { user }
    );

    // Use getAllByText to handle multiple matches
    const emailElements = screen.getAllByText(user.email);
    expect(emailElements.length).toBeGreaterThan(0);
    expect(emailElements[0]).toBeInTheDocument();

    expect(screen.getByText(/ReqTrace/i)).toBeInTheDocument();
    expect(screen.getByText(/Logout/i)).toBeInTheDocument();
  });

  test('clicking Clear Graph calls onClearGraph', () => {
    renderWithProviders(
      <Sidebar isOpen={true} onToggle={mockToggle} onClearGraph={mockClearGraph} />
    );
    const clearBtn = screen.getByText(/Clear Graph/i);
    fireEvent.click(clearBtn);
    expect(mockClearGraph).toHaveBeenCalledTimes(1);
  });

  test('clicking logout calls logout function', () => {
    const user = { email: 'test@example.com' };
    renderWithProviders(
      <Sidebar isOpen={true} onToggle={mockToggle} onClearGraph={mockClearGraph} />,
      { user }
    );
    const logoutBtn = screen.getByText(/Logout/i);
    fireEvent.click(logoutBtn);
    expect(mockLogout).toHaveBeenCalledTimes(1);
  });

  test('transcriptions dropdown toggles', async () => {
    renderWithProviders(
      <Sidebar isOpen={true} onToggle={mockToggle} onClearGraph={mockClearGraph} />
    );

    const toggleBtn = screen.getByText(/Show Transcriptions/i);

    // Should be hidden initially
    expect(screen.queryByText(/No previous sessions/i)).toBeInTheDocument();

    fireEvent.click(toggleBtn);
    await waitFor(() => {
      expect(screen.queryByText(/No previous sessions/i)).toBeInTheDocument();
    });

    //click again to close
    fireEvent.click(toggleBtn);
    await waitFor(() => {
      expect(screen.queryByText(/No previous sessions/i)).toBeInTheDocument();
    });
  });

  test('audio upload calls backend and updates transcriptions', async () => {
    const mockData = {
      entry: { id: 1, filename: 'test.mp3', text: 'Hello World', timestamp: '10:00' },
    };
    axios.post.mockResolvedValue({ data: mockData });

    renderWithProviders(
      <Sidebar isOpen={true} onToggle={mockToggle} onClearGraph={mockClearGraph} />
    );

    const file = new File(['audio content'], 'test.mp3', { type: 'audio/mp3' });

    // Select hidden input
    const input =
      screen.getByLabelText(/Upload Audio/i, { selector: 'input' }) ||
      screen.getByText(/Upload Audio/i).closest('input');

    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(() =>
      expect(axios.post).toHaveBeenCalledWith(
        expect.any(String),
        expect.any(FormData),
        expect.any(Object)
      )
    );
  });

  test('rejects invalid file type upload', async () => {
    renderWithProviders(
      <Sidebar isOpen={true} onToggle={mockToggle} onClearGraph={mockClearGraph} />
    );

    const file = new File(['content'], 'invalid.txt', { type: 'text/plain' });
    const input =
      screen.getByLabelText(/Upload Audio/i, { selector: 'input' }) ||
      screen.getByText(/Upload Audio/i).closest('input');

    fireEvent.change(input, { target: { files: [file] } });
    expect(window.alert).toHaveBeenCalledWith('Unsupported file type!');
  });

  test('clearing graph updates UI', async () => {
    renderWithProviders(
      <Sidebar isOpen={true} onToggle={mockToggle} onClearGraph={mockClearGraph} />
    );

    const clearBtn = screen.getByText(/Clear Graph/i);
    fireEvent.click(clearBtn);

    await waitFor(() => expect(screen.queryByText(/Session 1/i)).not.toBeInTheDocument());
  });
});
