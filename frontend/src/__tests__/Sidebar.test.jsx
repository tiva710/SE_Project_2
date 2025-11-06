import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import Sidebar from '../components/Sidebar';
import { AuthContext } from '../context/AuthContext';
import { GoogleOAuthProvider } from '@react-oauth/google';
import axios from 'axios';
import { act } from '@testing-library/react';

jest.mock('axios');

const mockToggle = jest.fn();
const mockClearGraph = jest.fn();
const mockGraphReady = jest.fn();
const mockTranscribeComplete = jest.fn();
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
      <Sidebar 
        isOpen={false} 
        onToggle={mockToggle} 
        onClearGraph={mockClearGraph}
        onGraphReady={mockGraphReady}
        onTranscribeComplete={mockTranscribeComplete}
      />
    );
    const button = screen.getByRole('button');
    expect(button).toBeInTheDocument();
  });

  test('renders sidebar header and user info when open (guest)', () => {
    renderWithProviders(
      <Sidebar 
        isOpen={true} 
        onToggle={mockToggle} 
        onClearGraph={mockClearGraph}
        onGraphReady={mockGraphReady}
        onTranscribeComplete={mockTranscribeComplete}
      />
    );
    expect(screen.getByText(/ReqTrace/i)).toBeInTheDocument();
    expect(screen.getByText(/Guest User/i)).toBeInTheDocument();
    expect(screen.getByText(/Login \/ Sign Up/i)).toBeInTheDocument();
  });

  test('renders sidebar header and user info when open (logged-in)', () => {
    const user = { email: 'test@example.com', picture: 'avatar.png' };
    renderWithProviders(
      <Sidebar 
        isOpen={true} 
        onToggle={mockToggle} 
        onClearGraph={mockClearGraph}
        onGraphReady={mockGraphReady}
        onTranscribeComplete={mockTranscribeComplete}
      />,
      { user }
    );

    const emailElements = screen.getAllByText(user.email);
    expect(emailElements.length).toBeGreaterThan(0);
    expect(emailElements[0]).toBeInTheDocument();

    expect(screen.getByText(/ReqTrace/i)).toBeInTheDocument();
    expect(screen.getByText(/Logout/i)).toBeInTheDocument();
  });

  test('clicking Clear Graph calls onClearGraph', () => {
    renderWithProviders(
      <Sidebar 
        isOpen={true} 
        onToggle={mockToggle} 
        onClearGraph={mockClearGraph}
        onGraphReady={mockGraphReady}
        onTranscribeComplete={mockTranscribeComplete}
      />
    );
    const clearBtn = screen.getByText(/Clear Graph/i);
    fireEvent.click(clearBtn);
    expect(mockClearGraph).toHaveBeenCalledTimes(1);
  });

  test('clicking logout calls logout function', () => {
    const user = { email: 'test@example.com' };
    renderWithProviders(
      <Sidebar 
        isOpen={true} 
        onToggle={mockToggle} 
        onClearGraph={mockClearGraph}
        onGraphReady={mockGraphReady}
        onTranscribeComplete={mockTranscribeComplete}
      />,
      { user }
    );
    const logoutBtn = screen.getByText(/Logout/i);
    fireEvent.click(logoutBtn);
    expect(mockLogout).toHaveBeenCalledTimes(1);
  });

  test('transcriptions dropdown toggles', async () => {
    renderWithProviders(
      <Sidebar 
        isOpen={true} 
        onToggle={mockToggle} 
        onClearGraph={mockClearGraph}
        onGraphReady={mockGraphReady}
        onTranscribeComplete={mockTranscribeComplete}
      />
    );

    const toggleBtn = screen.getByText(/Show Transcriptions/i);

    // Should show "No transcriptions yet" when opened
    await act(async () => {
      fireEvent.click(toggleBtn);
    });
    
    await waitFor(() => {
      expect(screen.getByText(/No transcriptions yet/i)).toBeInTheDocument();
    });

    // Click again to close
    await act(async () => {
      fireEvent.click(toggleBtn);
    });
    
    await waitFor(() => {
      expect(screen.queryByText(/No transcriptions yet/i)).not.toBeInTheDocument();
    });
  });

  test('audio upload calls backend and updates transcriptions', async () => {
    const mockData = {
      entry: { id: 1, filename: 'test.mp3', text: 'Hello World', timestamp: '10:00' },
      conversation_id: 'rec_123',
      audio_id: 'audio_456',
      graph_data: { nodes: [], links: [] },
    };
    axios.post.mockResolvedValue({ data: mockData });

    renderWithProviders(
      <Sidebar 
        isOpen={true} 
        onToggle={mockToggle} 
        onClearGraph={mockClearGraph}
        onGraphReady={mockGraphReady}
        onTranscribeComplete={mockTranscribeComplete}
      />
    );

    const file = new File(['audio content'], 'test.mp3', { type: 'audio/mp3' });

    // Find the file input
    const label = screen.getByText(/Upload Audio/i).closest('label');
    const input = label?.querySelector('input[type="file"]');

    await act(async () => {
      fireEvent.change(input, { target: { files: [file] } });
    });

    await waitFor(() => {
      expect(axios.post).toHaveBeenCalledWith(
        expect.stringContaining('transcribe'),
        expect.any(FormData),
        expect.any(Object)
      );
    });

    expect(mockTranscribeComplete).toHaveBeenCalled();
  });

  test('rejects invalid file type upload', async () => {
    renderWithProviders(
      <Sidebar 
        isOpen={true} 
        onToggle={mockToggle} 
        onClearGraph={mockClearGraph}
        onGraphReady={mockGraphReady}
        onTranscribeComplete={mockTranscribeComplete}
      />
    );

    const file = new File(['content'], 'invalid.txt', { type: 'text/plain' });
    const label = screen.getByText(/Upload Audio/i).closest('label');
    const input = label?.querySelector('input[type="file"]');

    await act(async () => {
      fireEvent.change(input, { target: { files: [file] } });
    });

    expect(window.alert).toHaveBeenCalledWith('Unsupported file type!');
    expect(axios.post).not.toHaveBeenCalled();
  });

  test('clearing graph updates UI', async () => {
    renderWithProviders(
      <Sidebar 
        isOpen={true} 
        onToggle={mockToggle} 
        onClearGraph={mockClearGraph}
        onGraphReady={mockGraphReady}
        onTranscribeComplete={mockTranscribeComplete}
      />
    );

    const clearBtn = screen.getByText(/Clear Graph/i);
    
    await act(async () => {
      fireEvent.click(clearBtn);
    });

    expect(mockClearGraph).toHaveBeenCalledTimes(1);
  });
});