/**
 * Isolated Unit Test Example
 * 
 * This test demonstrates testing a pure function in isolation
 * without any dependencies or side effects.
 */

// A pure function to test
export function sum(a, b) {
  return a + b;
}

// Another pure function that uses the first function
export function sumAndMultiply(a, b, multiplier) {
  return sum(a, b) * multiplier;
}

// Jest tests
describe('Isolated Pure Functions', () => {
  // Test for the sum function
  describe('sum function', () => {
    test('adds two positive numbers correctly', () => {
      expect(sum(2, 3)).toBe(5);
    });

    test('handles negative numbers', () => {
      expect(sum(-1, -2)).toBe(-3);
    });

    test('handles zero values', () => {
      expect(sum(0, 0)).toBe(0);
    });
  });

  // Test for the sumAndMultiply function
  describe('sumAndMultiply function', () => {
    test('sums and multiplies correctly', () => {
      expect(sumAndMultiply(2, 3, 2)).toBe(10);
    });

    test('handles zero multiplier', () => {
      expect(sumAndMultiply(5, 5, 0)).toBe(0);
    });
  });
}); 