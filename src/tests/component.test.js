/**
 * Component Unit Test Example
 * 
 * This test demonstrates testing a React component in isolation
 * using React Testing Library.
 */

import { render, screen, fireEvent } from '@testing-library/react';
import Button from '../components/Button';

describe('Button Component', () => {
  test('renders with default text', () => {
    render(<Button />);
    const buttonElement = screen.getByTestId('test-button');
    expect(buttonElement).toBeInTheDocument();
    expect(buttonElement).toHaveTextContent('Click me (clicked 0 times)');
  });

  test('renders with custom text', () => {
    render(<Button text="Submit" />);
    const buttonElement = screen.getByTestId('test-button');
    expect(buttonElement).toHaveTextContent('Submit (clicked 0 times)');
  });

  test('initializes with provided count', () => {
    render(<Button initialCount={5} />);
    const buttonElement = screen.getByTestId('test-button');
    expect(buttonElement).toHaveTextContent('(clicked 5 times)');
  });

  test('increments counter when clicked', () => {
    render(<Button />);
    const buttonElement = screen.getByTestId('test-button');
    
    // Initial state
    expect(buttonElement).toHaveTextContent('(clicked 0 times)');
    
    // Click the button once
    fireEvent.click(buttonElement);
    expect(buttonElement).toHaveTextContent('(clicked 1 times)');
    
    // Click two more times
    fireEvent.click(buttonElement);
    fireEvent.click(buttonElement);
    expect(buttonElement).toHaveTextContent('(clicked 3 times)');
  });

  test('applies custom className', () => {
    render(<Button className="primary" />);
    const buttonElement = screen.getByTestId('test-button');
    expect(buttonElement).toHaveClass('button');
    expect(buttonElement).toHaveClass('primary');
  });
}); 