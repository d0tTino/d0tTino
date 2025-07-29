const nextJest = require('next/jest');

const createJestConfig = nextJest({
  dir: './',
});

const customJestConfig = {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  moduleNameMapper: {
    '^@tauri-apps/api/tauri$': '<rootDir>/test/__mocks__/tauri.js',
    '^@tauri-apps/api/event$': '<rootDir>/test/__mocks__/event.js'
  },
};

module.exports = createJestConfig(customJestConfig);
