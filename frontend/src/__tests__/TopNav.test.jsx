import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import TopNav from '../components/TopNav';

describe('TopNav Component', () => {
  const mockSetActiveView = jest.fn();

  beforeEach(() => {
    mockSetActiveView.mockClear();
  });

  test('renders all navigation buttons', () => {
    render(<TopNav activeView="home" setActiveView={mockSetActiveView} />);
    expect(screen.getByText(/Home/i)).toBeInTheDocument();
    expect(screen.getByText(/About/i)).toBeInTheDocument();
    expect(screen.getByText(/Settings/i)).toBeInTheDocument();
    expect(screen.getByText(/Help/i)).toBeInTheDocument();
  });

  test('clicking a button calls setActiveView with correct id', () => {
    render(<TopNav activeView="home" setActiveView={mockSetActiveView} />);
    fireEvent.click(screen.getByText(/Home/i));
    expect(mockSetActiveView).toHaveBeenCalledWith('home');
  });
});
