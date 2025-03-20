/**
 * Example data processing module 
 * with both synchronous and asynchronous functions
 */

// Example data for testing
const sampleData = [
  { id: 1, name: 'Item 1', value: 10, active: true },
  { id: 2, name: 'Item 2', value: 20, active: false },
  { id: 3, name: 'Item 3', value: 30, active: true },
  { id: 4, name: 'Item 4', value: 40, active: false },
  { id: 5, name: 'Item 5', value: 50, active: true },
];

/**
 * Filters an array of items by their active status
 */
export function filterActiveItems(items) {
  return items.filter(item => item.active);
}

/**
 * Calculates the sum of values for all items
 */
export function calculateTotalValue(items) {
  return items.reduce((total, item) => total + item.value, 0);
}

/**
 * Simulates an API call that fetches data
 */
export function fetchData() {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve([...sampleData]);
    }, 100);
  });
}

/**
 * Process data - combines multiple operations
 */
export async function processData() {
  // Use 'this' to refer to the module exports, making it mockable
  const data = await fetchData();
  const activeItems = filterActiveItems(data);
  const totalValue = calculateTotalValue(activeItems);
  
  return {
    allItems: data,
    activeItems,
    activeCount: activeItems.length,
    totalValue,
    averageValue: totalValue / activeItems.length
  };
}

// Export the sample data for testing
export { sampleData }; 