import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import ChatInterface from '../components/ChatInterface';
import userEvent from '@testing-library/user-event';
import axios from 'axios';

jest.mock('axios');

describe('ChatInterface Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders the empty chat state correctly', () => {
    render(<ChatInterface />);

    expect(
      screen.getByText(/Ask questions about your uploaded transcriptions/i)
    ).toBeInTheDocument();

    expect(screen.getByPlaceholderText(/Ask about your transcripts.../i)).toBeInTheDocument();
  });

  test('renders chat input and send button', () => {
    render(<ChatInterface />);

    const input = screen.getByPlaceholderText(/Ask about your transcripts.../i);
    const button = screen.getByRole('button', { name: /send/i });

    expect(input).toBeInTheDocument();
    expect(button).toBeInTheDocument();
  });

  test('typing updates the input value', () => {
    render(<ChatInterface />);
    const input = screen.getByPlaceholderText(/Ask about your transcripts.../i);

    fireEvent.change(input, { target: { value: 'New feature idea' } });
    expect(input.value).toBe('New feature idea');
  });

  test('pressing Enter triggers message send', async () => {
    axios.post.mockResolvedValueOnce({
      data: { answer: 'Calendar integrated!' },
    });

    render(<ChatInterface />);
    const input = screen.getByPlaceholderText(/Ask about your transcripts.../i);

    await userEvent.type(input, 'Integrate calendar{enter}');

    const botMessage = await screen.findByText(/Calendar integrated/i);

    expect(botMessage).toBeInTheDocument();

    expect(axios.post).toHaveBeenCalledWith(
      'http://127.0.0.1:8000/conversation/chat',
      { query: 'Integrate calendar' },
      expect.any(Object)
    );
  });

  test('clears input field after sending message', async () => {
    axios.post.mockResolvedValueOnce({ data: { answer: 'Done.' } });

    render(<ChatInterface />);
    const input = screen.getByPlaceholderText(/Ask about your transcripts.../i);
    const button = screen.getByRole('button', { name: /send/i });

    fireEvent.change(input, { target: { value: 'Auto-clear test' } });
    fireEvent.click(button);

    expect(input.value).toBe('');
  });

  test('does not send empty messages', () => {
    render(<ChatInterface />);
    const button = screen.getByRole('button', { name: /send/i });
    fireEvent.click(button);
    expect(axios.post).not.toHaveBeenCalled();
  });

  test('shows loading indicator when sending message', async () => {
    axios.post.mockImplementation(() => new Promise(() => {})); // never resolves

    render(<ChatInterface />);
    const input = screen.getByPlaceholderText(/Ask about your transcripts.../i);
    const button = screen.getByRole('button', { name: /send/i });

    fireEvent.change(input, { target: { value: 'Test loading' } });
    fireEvent.click(button);

    expect(screen.getByTestId('loading-indicator')).toBeInTheDocument();
  });

  test('displays error message when API call fails', async () => {
    axios.post.mockRejectedValueOnce(new Error('Network Error'));

    render(<ChatInterface />);
    const input = screen.getByPlaceholderText(/Ask about your transcripts.../i);
    const button = screen.getByRole('button', { name: /send/i });

    fireEvent.change(input, { target: { value: 'Fail test' } });
    fireEvent.click(button);

    const errorMessage = await screen.findByText(/⚠️ Error: Unable to reach backend./i);
    expect(errorMessage).toBeInTheDocument();
  });

  test('displays multiple sequential messages correctly', async () => {
    axios.post
      .mockResolvedValueOnce({ data: { answer: 'First reply' } })
      .mockResolvedValueOnce({ data: { answer: 'Second reply' } });

    render(<ChatInterface />);
    const input = screen.getByPlaceholderText(/Ask about your transcripts.../i);
    const button = screen.getByRole('button', { name: /send/i });

    fireEvent.change(input, { target: { value: 'Message 1' } });
    fireEvent.click(button);
    await screen.findByText(/First reply/i);

    fireEvent.change(input, { target: { value: 'Message 2' } });
    fireEvent.click(button);
    await screen.findByText(/Second reply/i);

    expect(screen.getByText(/First reply/i)).toBeInTheDocument();
    expect(screen.getByText(/Second reply/i)).toBeInTheDocument();
  });
});
