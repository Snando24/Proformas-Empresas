/**
 * Jest setup file for JavaScript tests
 * Runs before all tests
 */

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};

global.localStorage = localStorageMock;

// Mock fetch API
global.fetch = jest.fn();

// Mock window.alert
global.alert = jest.fn();

// Mock window.confirm
global.confirm = jest.fn(() => true);

// Setup common test utilities
beforeEach(() => {
  jest.clearAllMocks();
  localStorage.getItem.mockClear();
  localStorage.setItem.mockClear();
  fetch.mockClear();
});
