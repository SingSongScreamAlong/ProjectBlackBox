# BlackBox Driver App Development Guide

This guide provides instructions for setting up and developing the BlackBox Driver App.

## Development Environment Setup

### Prerequisites
- Node.js 16+ and npm 8+
- TypeScript 4.5+
- Electron 22+
- Git

### Initial Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/your-org/blackbox.git
   cd blackbox/driver_app
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

4. For testing with a mock backend:
   ```bash
   # In a separate terminal
   cd mock_server
   npm install
   npm start
   ```

## Project Structure

```
driver_app/
├── src/                  # Source code
│   ├── adapters/         # Simulator adapters (iRacing, Assetto Corsa, etc.)
│   ├── api/              # API interfaces for service boundaries
│   ├── config/           # Configuration management
│   ├── models/           # Data models and interfaces
│   ├── services/         # Core services (telemetry, data transmission, etc.)
│   ├── types/            # TypeScript type definitions
│   ├── utils/            # Utility functions
│   ├── main.ts           # Main Electron process
│   └── preload.ts        # Electron preload script
├── resources/            # Static resources (icons, images, etc.)
├── mock_server/          # Mock backend server for development
├── deployment/           # Deployment configurations and scripts
├── tests/                # Test files
├── package.json          # Project dependencies and scripts
└── tsconfig.json         # TypeScript configuration
```

## Development Workflow

### 1. Feature Development

1. Create a feature branch from `develop`:
   ```bash
   git checkout develop
   git pull
   git checkout -b feature/your-feature-name
   ```

2. Implement your feature, following the modular architecture:
   - Add new adapters in `src/adapters/`
   - Define API interfaces in `src/api/`
   - Create data models in `src/models/`
   - Implement services in `src/services/`

3. Run the application in development mode:
   ```bash
   npm run dev
   ```

4. Write tests for your feature:
   ```bash
   # Create test files in tests/ directory
   npm test
   ```

5. Commit your changes:
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

### 2. Code Quality

- Run linting:
  ```bash
  npm run lint
  ```

- Run TypeScript type checking:
  ```bash
  npm run type-check
  ```

- Format code:
  ```bash
  npm run format
  ```

### 3. Testing

- Run unit tests:
  ```bash
  npm test
  ```

- Run integration tests:
  ```bash
  npm run test:integration
  ```

- Run end-to-end tests:
  ```bash
  npm run test:e2e
  ```

### 4. Pull Request

1. Push your feature branch:
   ```bash
   git push origin feature/your-feature-name
   ```

2. Create a pull request to the `develop` branch
3. Ensure CI checks pass
4. Request code review
5. Address feedback and make necessary changes
6. Merge to `develop` once approved

## API Integration

### Connecting to BlackBox Core

The Driver App communicates with BlackBox Core using WebSockets and REST APIs:

1. WebSocket connection for real-time telemetry:
   ```typescript
   // Example in src/services/DataTransmissionService.ts
   this.socket = io(this.serverUrl, {
     reconnection: true,
     reconnectionAttempts: Infinity,
     reconnectionDelay: 1000,
     reconnectionDelayMax: 5000,
     timeout: 20000,
   });
   ```

2. REST API for configuration and authentication:
   ```typescript
   // Example API call
   async function fetchConfig() {
     const response = await fetch(`${serverUrl}/api/v1/system/config`);
     return response.json();
   }
   ```

### Simulator Adapters

To add support for a new simulator:

1. Create a new adapter in `src/adapters/` that implements the `SimAdapter` interface
2. Register the adapter in `src/services/TelemetryService.ts`

## Building and Packaging

- Build TypeScript:
  ```bash
  npm run build
  ```

- Package the application:
  ```bash
  npm run package
  ```

- Create installers:
  ```bash
  npm run make
  ```

## Debugging

- Enable debug logging:
  ```bash
  # Windows
  set DEBUG=blackbox:*
  # macOS/Linux
  export DEBUG=blackbox:*
  
  npm run dev
  ```

- Debug Electron main process:
  ```bash
  npm run debug:main
  ```

## Contributing Guidelines

1. Follow the TypeScript coding style
2. Write meaningful commit messages following Conventional Commits
3. Include tests for new features
4. Update documentation for API changes
5. Keep pull requests focused on a single feature or bug fix

## Resources

- [Electron Documentation](https://www.electronjs.org/docs)
- [TypeScript Documentation](https://www.typescriptlang.org/docs)
- [Socket.IO Documentation](https://socket.io/docs/v4)
- [iRacing SDK Documentation](https://github.com/iRacing/irsdk-node)
