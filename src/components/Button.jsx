import { useState } from 'react';

/**
 * A reusable Button component with click counter
 */
function Button({ text = 'Click me', initialCount = 0, className = '' }) {
  const [count, setCount] = useState(initialCount);
  
  const handleClick = () => {
    setCount(prevCount => prevCount + 1);
  };
  
  return (
    <button 
      className={`button ${className}`}
      onClick={handleClick}
      data-testid="test-button"
    >
      {text} (clicked {count} times)
    </button>
  );
}

export default Button; 