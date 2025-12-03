# BlackBox Commercial Deployment Guide

## Overview

This guide explains how to deploy BlackBox as a **commercial SaaS product** where customers download a Windows app and connect to your cloud infrastructure.

---

## Architecture

### **Production Architecture:**
```
┌─────────────────────────────────────────────────────────────┐
│                    CUSTOMER'S PC                            │
│                                                             │
│  ┌────────────────────────────────────────────┐            │
│  │   BlackBox Desktop App (Electron)          │            │
│  │   - Collects iRacing telemetry             │            │
│  │   - Captures video                         │            │
│  │   - Connects to YOUR cloud via WSS         │            │
│  └────────────────────────────────────────────┘            │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           │ HTTPS/WSS
                           │
┌──────────────────────────┴──────────────────────────────────┐
│              YOUR DIGITALOCEAN CLOUD                        │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │   Backend    │  │   Database   │  │  Video Relay    │  │
│  │   API        │  │  PostgreSQL  │  │  Agent          │  │
│  │   Port 3000  │  │  TimescaleDB │  │  (Cloud-based)  │  │
│  └──────────────┘  └──────────────┘  └─────────────────┘  │
│         │                  │                   │           │
│  ┌──────┴──────────────────┴───────────────────┴────────┐  │
│  │              AI & Voice Services                      │  │
│  │  - GradientAI (coaching)                             │  │
│  │  - ElevenLabs (voice)                                │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Web Dashboard (React)                         │  │
│  │         https://dashboard.yourcompany.com             │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Cloud Infrastructure Deployment

### Prerequisites

1. **DigitalOcean Account**
   - Sign up at digitalocean.com
   - Add payment method
   - Get API token from: API → Tokens → Generate New Token

2. **Domain Name**
   - Purchase domain (e.g., `blackboxracing.com`)
   - Point nameservers to DigitalOcean

3. **API Keys**
   - OpenAI or GradientAI API key
   - ElevenLabs API key

### 1.1 Configure Environment

```bash
cd deployment/digitalocean
cp .env.example .env
```

Edit `.env`:
```bash
# DigitalOcean
DO_API_TOKEN=dop_v1_xxxxxxxxxxxx
DO_REGION=nyc3
DOMAIN=blackboxracing.com
SUBDOMAIN=api

# Database
POSTGRES_DB=blackbox_prod
POSTGRES_USER=blackbox_admin
POSTGRES_PASSWORD=$(openssl rand -base64 32)

# Security
JWT_SECRET=$(openssl rand -base64 32)

# API Keys (for backend services)
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxx
ELEVENLABS_API_KEY=xxxxxxxxxxxxxxx
GRADIENT_AI_API_KEY=xxxxxxxxxxxxxxx

# Application URLs (will be generated after deployment)
API_URL=https://api.blackboxracing.com
DASHBOARD_URL=https://dashboard.blackboxracing.com
```

### 1.2 Deploy to DigitalOcean

```bash
# Install doctl (DigitalOcean CLI)
# macOS
brew install doctl

# Windows
# Download from: https://github.com/digitalocean/doctl/releases

# Linux
cd ~
wget https://github.com/digitalocean/doctl/releases/download/v1.98.1/doctl-1.98.1-linux-amd64.tar.gz
tar xf doctl-*.tar.gz
sudo mv doctl /usr/local/bin

# Authenticate
doctl auth init
# Enter your DO_API_TOKEN

# Deploy infrastructure
./hybrid-deploy.sh
```

This will deploy:
- Backend API (Node.js + Express)
- PostgreSQL database
- Redis cache
- Video relay agent (cloud-based)
- AI agent
- Web dashboard
- Load balancer
- SSL certificates

### 1.3 Configure DNS

```bash
# Get your app IP
doctl apps list

# Configure DNS records
./configure-dns.sh blackboxracing.com

# This creates:
# api.blackboxracing.com → Backend API
# dashboard.blackboxracing.com → Web Dashboard
# ws.blackboxracing.com → WebSocket endpoint
```

### 1.4 Verify Deployment

```bash
# Check API health
curl https://api.blackboxracing.com/health

# Should return:
# {"status":"ok","version":"1.0.0","db":"connected"}

# Check dashboard
# Visit: https://dashboard.blackboxracing.com
```

---

## Phase 2: Windows Desktop App Build

### 2.1 Configure Desktop App for Production

Edit `src/config/AppConfig.ts`:

```typescript
export class AppConfig {
  // Production cloud endpoint (NOT local relay)
  public static readonly CLOUD_BACKEND_URL = 'https://api.blackboxracing.com';
  public static readonly CLOUD_WS_URL = 'wss://ws.blackboxracing.com';

  // Remove local relay agent references for production builds
  public static readonly USE_LOCAL_RELAY = false;

  // License validation endpoint
  public static readonly LICENSE_VALIDATION_URL = 'https://api.blackboxracing.com/license/validate';
}
```

### 2.2 Add License Key System

Create `src/services/LicenseService.ts`:

```typescript
import axios from 'axios';
import { AppConfig } from '../config/AppConfig';

export class LicenseService {
  private licenseKey: string | null = null;
  private isValid: boolean = false;

  async validateLicense(key: string): Promise<boolean> {
    try {
      const response = await axios.post(
        AppConfig.LICENSE_VALIDATION_URL,
        { licenseKey: key },
        { timeout: 5000 }
      );

      this.isValid = response.data.valid;
      if (this.isValid) {
        this.licenseKey = key;
        // Store locally (encrypted)
        this.storeLicense(key);
      }
      return this.isValid;
    } catch (error) {
      console.error('License validation failed:', error);
      return false;
    }
  }

  private storeLicense(key: string): void {
    // Store encrypted license key in local storage
    // Implementation depends on your encryption preference
  }
}
```

### 2.3 Build Windows Installer

```bash
# Install dependencies
npm install

# Build application
npm run build

# Create Windows installer
npm run make

# Output: out/make/squirrel.windows/x64/BlackBox-Setup-1.0.0.exe
```

### 2.4 Code Sign the Installer (Professional)

```bash
# Get code signing certificate from:
# - DigiCert
# - Sectigo
# - GoDaddy

# Sign the installer (Windows)
signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com out/make/squirrel.windows/x64/BlackBox-Setup-1.0.0.exe

# Verify signature
signtool verify /pa out/make/squirrel.windows/x64/BlackBox-Setup-1.0.0.exe
```

---

## Phase 3: Distribution

### 3.1 Create Download Portal

Host installer on your website:
- `https://blackboxracing.com/download`
- Include license key input
- Customer dashboard for license management

### 3.2 Auto-Update System

The app includes auto-update via electron-updater:

1. Upload new releases to DigitalOcean Spaces:
```bash
# Create Spaces bucket
doctl compute space create blackbox-releases --region nyc3

# Upload new version
aws s3 cp out/make/squirrel.windows/x64/ s3://blackbox-releases/releases/windows/ --recursive
```

2. App checks for updates on startup:
```typescript
// In main.ts
import { autoUpdater } from 'electron-updater';

autoUpdater.setFeedURL({
  provider: 'generic',
  url: 'https://blackbox-releases.nyc3.digitaloceanspaces.com/releases/windows'
});

autoUpdater.checkForUpdatesAndNotify();
```

---

## Phase 4: User Onboarding Flow

### Customer Experience:

1. **Visit Website**: `https://blackboxracing.com`
2. **Purchase License**: Credit card payment (Stripe/PayPal)
3. **Receive License Key**: Email + customer dashboard
4. **Download Installer**: BlackBox-Setup-1.0.0.exe
5. **Install App**: Double-click installer
6. **Enter License Key**: On first run
7. **Start Racing**: iRacing auto-detected

---

## Phase 5: Backend Services

### 5.1 License Management API

Add to backend (`deployment/digitalocean/backend-engine/`):

```javascript
// routes/license.js
router.post('/license/validate', async (req, res) => {
  const { licenseKey } = req.body;

  // Check database for valid license
  const license = await License.findOne({
    where: { key: licenseKey, status: 'active' }
  });

  if (license) {
    // Update last used timestamp
    license.lastUsed = new Date();
    await license.save();

    res.json({
      valid: true,
      features: license.features,
      expiresAt: license.expiresAt
    });
  } else {
    res.json({ valid: false });
  }
});
```

### 5.2 User Dashboard

Add customer portal to dashboard:
- License status
- Usage statistics
- Billing information
- Download installer
- Support tickets

---

## Cost Breakdown (Monthly)

### DigitalOcean Infrastructure

| Service | Specs | Cost |
|---------|-------|------|
| **App Platform (Backend)** | Professional | $12/month |
| **Database** | 1GB RAM, 10GB SSD | $15/month |
| **Spaces (Storage)** | 250GB + CDN | $5/month |
| **Load Balancer** | SSL + HA | $12/month |
| **Container Registry** | 5 repos | $5/month |
| **Bandwidth** | 1TB included | Free |
| **Backups** | Automated daily | $3/month |
| **Total Infrastructure** | | **$52/month** |

### API Costs (Per User)

| Service | Usage | Cost |
|---------|-------|------|
| **GradientAI** | ~100 requests/session | $0.02-0.10/session |
| **ElevenLabs** | Voice coaching | $0.01-0.05/session |
| **Total per user/session** | | **$0.03-0.15** |

### Pricing Recommendations

For a commercial product:
- **Monthly Subscription**: $19.99-49.99/month
- **Annual Subscription**: $199-499/year (save 17%)
- **Team License** (5 drivers): $149.99/month
- **Enterprise**: Custom pricing

With 100 active users:
- **Revenue**: $1,999-4,999/month
- **Infrastructure**: $52/month
- **API Costs**: $300-1,500/month
- **Profit Margin**: 60-85%

---

## Phase 6: Monitoring & Support

### 6.1 Setup Monitoring

```bash
# Install monitoring
doctl apps create --spec monitoring-app-spec.yaml

# Configure alerts
# - API downtime → PagerDuty
# - Database issues → Email
# - High error rates → Slack
```

### 6.2 Customer Support

- Support email: support@blackboxracing.com
- Knowledge base: help.blackboxracing.com
- Live chat: Intercom/Zendesk
- Status page: status.blackboxracing.com

---

## Phase 7: Legal & Compliance

### Required Documents

1. **Terms of Service**
2. **Privacy Policy** (GDPR compliant)
3. **End User License Agreement (EULA)**
4. **Refund Policy**
5. **Data Processing Agreement (DPA)**

### Data Protection

- Encrypt telemetry data at rest
- HTTPS/WSS for all connections
- User consent for data collection
- Data export/deletion on request
- GDPR compliance (if EU customers)

---

## Deployment Checklist

### Pre-Launch

- [ ] DigitalOcean infrastructure deployed
- [ ] DNS configured and propagated
- [ ] SSL certificates active
- [ ] Database migrations run
- [ ] License system implemented
- [ ] Windows installer built and signed
- [ ] Auto-update system configured
- [ ] Payment processing integrated
- [ ] Customer dashboard functional
- [ ] Support system ready

### Testing

- [ ] End-to-end testing (development)
- [ ] Load testing (100+ concurrent users)
- [ ] Security audit completed
- [ ] Penetration testing passed
- [ ] Beta user testing completed

### Launch

- [ ] Marketing website live
- [ ] App Store/download page ready
- [ ] Initial customer support trained
- [ ] Monitoring and alerts active
- [ ] Backup and disaster recovery tested
- [ ] Legal documents published

---

## Post-Launch Operations

### Daily Tasks
- Monitor error rates
- Check support tickets
- Review system health

### Weekly Tasks
- Review usage analytics
- Update documentation
- Deploy bug fixes

### Monthly Tasks
- Review infrastructure costs
- Plan feature releases
- Security updates
- Customer feedback review

---

## Scaling Plan

### When you reach 500 users:
- Upgrade database to 4GB RAM
- Add second backend instance
- Enable CDN for dashboard
- Cost: ~$150/month

### When you reach 2,000 users:
- Kubernetes cluster
- Multiple availability zones
- Dedicated video processing
- Cost: ~$500/month

---

## Support Contacts

- **DigitalOcean Support**: https://cloud.digitalocean.com/support
- **Deployment Issues**: See troubleshooting guide
- **Code Issues**: GitHub Issues

---

**Ready to deploy your commercial product!**

Next step: Run `./hybrid-deploy.sh` to deploy to production.
