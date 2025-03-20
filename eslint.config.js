module.exports = {
  // Indicates that this is the root ESLint configuration (no need to look in parent folders)
  root: true,

  // Defines the environments that your project will run in (makes browser and Node.js globals available)
  env: {
    browser: true,
    node: true,
    es2021: true,
  },

  // A set of base configurations and recommended rules
  extends: [
    "eslint:recommended",         // Basic ESLint recommended rules
    "plugin:react/recommended",   // React-specific linting rules
  ],

  // Specifies the ESLint parser settings
  parserOptions: {
    ecmaVersion: 2021,     // Allows for parsing modern ECMAScript features
    sourceType: "module",  // Allows for the use of imports
    ecmaFeatures: {
      jsx: true,           // Enable JSX parsing
    },
  },

  // Additional plugins
  plugins: [
    "react",
  ],

  // Custom rules (override or add new ones as needed)
  rules: {
    // Example: turn off prop-types requirement if you're using TypeScript
    "react/prop-types": "off",

    // Example: warn on console logs to help clean up debugging
    "no-console": ["warn", { allow: ["warn", "error"] }],

    // Add or update rules to fit your team's needs
  },

  // Helps ESLint locate the correct React version for linting
  settings: {
    react: {
      version: "detect",
    },
  },
};
