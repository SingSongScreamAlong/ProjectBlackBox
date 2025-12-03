# BlackBox Hybrid Cloud System

A comprehensive telemetry and coaching platform for iRacing sim racing, featuring a hybrid cloud architecture with AI-powered driver coaching and voice feedback.

## 🏁 Project Status

**Current Status**: Migration to hybrid cloud architecture **95% complete**
- ✅ Local relay agent WebSocket server validated (port 8765)
- ✅ Driver app enhanced for cloud data transmission
- ✅ Dashboard WebSocket client implemented
- ✅ AI agent and voice services integrated
- ✅ DigitalOcean deployment scripts ready
- ⏳ Cloud backend deployment pending

## 🚀 Features

### **Hybrid Cloud Architecture**
- **Local Driver App**: Low-latency data collection and real-time telemetry
- **Relay Agent**: WebSocket server for data streaming and video encoding
- **DigitalOcean Backend**: Cloud processing, storage, and AI integration
- **Team Dashboard**: Real-time monitoring and multi-driver coordination
- **Secure Communication**: JWT authentication and encrypted WebSocket connections

### **Telemetry & Video**
- Real-time iRacing telemetry data collection and transmission
- Video capture and streaming for driver view analysis
- Multi-driver team support with seamless handoffs
- Optimized for minimal racing performance impact

### **AI Integration**
- **GradientAI**: Advanced driver coaching and performance analysis
- **Real-time Feedback**: Adaptive coaching based on driver skill and situation
- **Voice Integration**: ElevenLabs TTS with natural-sounding coaching
- **Local STT**: Voice command recognition for hands-free operation

## Installation

### Windows (Recommended)

1. Download the latest Windows installer (.exe) from the [Releases](https://github.com/SingSongScreamAlong/blackboxdriverapp/releases) page
2. Run the installer and follow the prompts
3. Launch the BlackBox Driver App from your Start menu

### Building from Source

#### Prerequisites

- **Driver App**: [Node.js](https://nodejs.org/) (v16+), npm, Electron
- **Relay Agent**: Python 3.8+, pip, virtual environment
- **Dashboard**: Node.js, npm, React, TypeScript
- **Windows Required**: iRacing only runs on Windows

#### Build Steps

1. Clone this repository
   ```bash
   git clone https://github.com/SingSongScreamAlong/blackboxdriverapp.git
   cd blackboxdriverapp
   ```

2. **Driver App Setup**:
   ```bash
   cd driver_app
   npm install
   npm run build
   npm start
   ```

3. **Relay Agent Setup**:
   ```bash
   cd relay_agent
   python -m venv relay_agent_venv
   source relay_agent_venv/bin/activate  # Windows: relay_agent_venv\Scripts\activate
   pip install -r requirements.txt
   python agent_main.py
   ```

4. **Dashboard Setup**:
   ```bash
   cd dashboard
   npm install
   npm start
   ```

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Driver App    │───▶│   Relay Agent   │───▶│ DigitalOcean    │
│   (Electron)    │    │   (Python)      │    │   Backend       │
│                 │    │                 │    │                 │
│ • iRacing SDK   │    │ • WebSocket     │    │ • AI Agent      │
│ • Video Capture │    │ • Video Encode  │    │ • Voice Service │
│ • Local STT     │    │ • Telemetry     │    │ • Data Storage  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                ▲
                                │
                       ┌─────────────────┐
                       │   Dashboard     │
                       │   (React)       │
                       │                 │
                       │ • Team Monitor  │
                       │ • WebSocket UI  │
                       │ • Multi-Driver  │
                       └─────────────────┘
```

## Usage

### Local Development Setup

1. **Start Relay Agent**: `python relay_agent/agent_main.py`
2. **Start Dashboard**: `npm start` (in dashboard directory)
3. **Start Driver App**: `npm start` (in driver_app directory)
4. **Launch iRacing**: The system will automatically detect and begin data collection

### Production Deployment

1. **Deploy to DigitalOcean**: Use `deployment/digitalocean/hybrid-deploy.sh`
2. **Configure DNS**: Point your domain to the DigitalOcean droplet
3. **Update Configuration**: Set API keys and endpoints in config files
4. **Test End-to-End**: Run `npm run validate:hybrid-cloud` in dashboard

## Configuration

**⚠️ Security Notice**: Never commit sensitive credentials to version control. Always use environment variables for API keys, passwords, and secrets. See `docs/SECURITY_BEST_PRACTICES.md` for detailed security guidelines.

### Environment Variables

1. **Copy environment templates**:
   ```bash
   cp .env.example .env
   cp deployment/digitalocean/.env.example deployment/digitalocean/.env
   ```

2. **Fill in your credentials**:
   - `OPENAI_API_KEY` or `GRADIENT_AI_API_KEY`
   - `ELEVENLABS_API_KEY`
   - `JWT_SECRET` (generate with: `openssl rand -base64 32`)
   - `POSTGRES_PASSWORD` (generate with: `openssl rand -base64 32`)
   - `DATABASE_URL`

### Driver App (`driver_app/src/config/AppConfig.ts`)
- **Relay Agent URL**: WebSocket connection to local relay agent
- **Cloud Backend**: DigitalOcean backend endpoint
- **AI Settings**: GradientAI API configuration
- **Voice Settings**: ElevenLabs TTS and local STT options

### Relay Agent (`relay_agent/config/config.json`)
- **WebSocket Port**: Default 8765 for local connections
- **Backend URL**: DigitalOcean cloud backend endpoint
- **API Key**: Authentication for cloud services (use environment variables)
- **Video Settings**: Encoding and streaming parameters

## Development

### Project Structure

```
ProjectBlackBox/
├── driver_app/          # Electron app for Windows
│   ├── src/services/    # Core services (iRacing, WebSocket, AI, Voice)
│   └── dist/           # Built application
├── relay_agent/         # Python WebSocket server
│   ├── backend/        # Telemetry server and video encoding
│   └── config/         # Configuration files
├── dashboard/          # React team monitoring UI
│   ├── src/components/ # UI components and WebSocket client
│   └── scripts/        # Validation and testing scripts
├── deployment/         # DigitalOcean deployment scripts
│   └── digitalocean/   # Docker, CI/CD, and infrastructure
└── docs/              # Documentation and migration guides
```

### Deployment & CI/CD

- **GitHub Actions**: Automated Windows builds (`.github/workflows/`)
- **DigitalOcean**: Cloud backend deployment scripts
- **Docker**: Containerized services for production
- **Hybrid Validation**: End-to-end testing scripts

## Testing & Validation

### Hybrid Cloud Validator
```bash
cd dashboard
npm run validate:hybrid-cloud
```

### Component Testing
- **Driver App**: `npm test` (unit tests in `src/services/__tests__/`)
- **Relay Agent**: `cd relay_agent && python -m pytest`
- **Dashboard**: `cd dashboard && npm test` (React component tests)

## Security

Security is a top priority for BlackBox. Please review our comprehensive security documentation:

- **[Security Best Practices](docs/SECURITY_BEST_PRACTICES.md)** - Complete security guidelines
- **Environment Variables** - Use `.env.example` files as templates (never commit `.env` files)
- **API Key Management** - Rotate keys regularly, use unique keys per environment
- **JWT Secrets** - Generate strong random secrets (min 32 bytes)
- **Database Security** - Use strong passwords, enable SSL, implement backups
- **SSL/TLS** - Always use HTTPS in production

### Reporting Security Issues

If you discover a security vulnerability, please email security@blackbox.example.com. Do not create public GitHub issues for security vulnerabilities.

## Contributing

See `docs/hybrid_cloud_deployment_guide.md` for detailed setup instructions and `docs/hybrid_cloud_migration_plan.md` for architecture details.

## License

MIT
