// Local only: service-security's test setup (tests.initializer.ts) always creates a
// message-broker topic, and no broker runs locally. This keeps the workspace's Jest
// config and swaps that setup for the environment one. Run it from the workspace
// (`npm test -w services/service-security -- --config <this file>`); CI keeps the full setup.
const cfg = require(process.cwd() + '/jest.config.js');

module.exports = {
  ...cfg,
  rootDir: process.cwd(),
  setupFilesAfterEnv: ['<rootDir>/src/lib/initializers/env.initializer.ts'],
};
