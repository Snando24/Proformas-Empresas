module.exports = {
  testEnvironment: "jsdom",
  roots: ["<rootDir>/tests/javascript"],
  testMatch: ["**/__tests__/**/*.js", "**/?(*.)+(spec|test).js"],
  collectCoverageFrom: [
    "src/**/*.js",
    "!src/**/index.js",
    "!src/**/*.spec.js",
    "!src/**/*.test.js"
  ],
  coveragePathIgnorePatterns: [
    "/node_modules/",
    "/static/",
    "/output/"
  ],
  setupFilesAfterEnv: ["<rootDir>/tests/javascript/jest.setup.js"],
  moduleNameMapper: {
    "\\.(css|less|scss|sass)$": "<rootDir>/tests/javascript/__mocks__/styleMock.js"
  },
  transform: {
    "^.+\\.js$": "babel-jest"
  },
  testTimeout: 10000,
  verbose: true,
  bail: false
};
