import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import ChatInterface from '../components/ChatInterface';
import axios from 'axios';

jest.mock('axios');

describe('ChatInterface Integration', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders initial messages and adds a bot response after sending', async () => {
    // mock axios call
    axios.post.mockResolvedValueOnce({
      data: { answer: 'More!' },
    });

    render(<ChatInterface />);

    // user sends new message
    const input = screen.getByPlaceholderText(/Ask about your transcripts.../i);
    fireEvent.change(input, { target: { value: 'Tell me more' } });

    const sendBtn = screen.getByRole('button', { name: /send/i });
    fireEvent.click(sendBtn);

    await waitFor(() =>
      expect(axios.post).toHaveBeenCalledWith(
        'http://127.0.0.1:8000/conversation/chat',
        { query: 'Tell me more' },
        expect.any(Object)
      )
    );

    await waitFor(() => expect(screen.getByText('More!')).toBeInTheDocument());
  });
});
