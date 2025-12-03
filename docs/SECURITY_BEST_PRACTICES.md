# BlackBox Security Best Practices

## Overview

This document outlines security best practices for deploying and operating the BlackBox telemetry platform. Following these guidelines will help protect your deployment from common security vulnerabilities.

---

## 1. Environment Variables and Secrets Management

### ✅ DO
- **Use environment variables** for all sensitive configuration
- **Never commit** `.env` files to version control
- **Rotate secrets regularly** (every 90 days minimum)
- **Use unique secrets** for each environment (dev, staging, production)
- **Generate strong secrets** using cryptographically secure random generators

### ❌ DON'T
- Never hardcode API keys, passwords, or tokens in source code
- Never commit secrets to Git history
- Never reuse secrets across environments
- Never share secrets via insecure channels (email, Slack, etc.)

### Implementation

```bash
# Generate secure random secrets
openssl rand -base64 32  # For JWT_SECRET
openssl rand -base64 48  # For DATABASE_PASSWORD

# Use environment variables in docker-compose.yml
environment:
  JWT_SECRET: ${JWT_SECRET}
  DATABASE_URL: ${DATABASE_URL}
  ELEVENLABS_API_KEY: ${ELEVENLABS_API_KEY}
```

### Secret Rotation Checklist

1. Generate new secret
2. Update environment variables in production
3. Restart affected services with zero-downtime deployment
4. Verify services are working with new secrets
5. Invalidate old secrets
6. Document rotation in security log

---

## 2. API Key Management

### Third-Party API Keys

**ElevenLabs API Key:**
- Store in environment variables
- Restrict by IP address if possible
- Monitor usage for anomalies
- Set up billing alerts

**GradientAI / OpenAI API Key:**
- Use separate keys for dev/prod
- Enable rate limiting
- Monitor for unauthorized usage
- Implement cost controls

**DigitalOcean API Token:**
- Use read-only tokens where possible
- Limit scope to required resources
- Store in GitHub Secrets for CI/CD
- Regenerate if compromised

### Rotation Schedule

| Secret Type | Rotation Frequency | Last Rotated |
|-------------|-------------------|--------------|
| JWT Secret | Every 90 days | N/A |
| Database Password | Every 90 days | N/A |
| API Keys | Every 180 days or on breach | N/A |
| DO API Token | Every 180 days | N/A |

---

## 3. Database Security

### PostgreSQL Configuration

```yaml
# Use strong passwords
POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}  # Min 20 characters, random

# Restrict network access
# Only allow connections from backend container
networks:
  - blackbox-network  # Private Docker network

# Enable SSL connections (production)
POSTGRES_SSL_MODE: require
```

### Best Practices

- Use parameterized queries to prevent SQL injection
- Enable connection pooling with limits
- Implement regular backups (automated, encrypted)
- Set up monitoring and alerting
- Use read-only users for reporting
- Enable audit logging for sensitive operations

### Backup Strategy

- **Frequency**: Daily automated backups
- **Retention**: 30 days rolling, 12 months monthly
- **Encryption**: AES-256 encryption at rest
- **Testing**: Monthly restore tests
- **Location**: Off-site backup storage (DigitalOcean Spaces)

---

## 4. JWT Authentication

### Configuration

```javascript
// Backend JWT configuration
JWT_SECRET: process.env.JWT_SECRET  // Min 32 bytes, random
JWT_EXPIRATION: '24h'  // Token expires after 24 hours
JWT_REFRESH_EXPIRATION: '7d'  // Refresh token expires after 7 days
```

### Best Practices

- Use strong, random secrets (min 256 bits)
- Set reasonable expiration times
- Implement token refresh mechanism
- Store tokens securely on client (httpOnly cookies preferred)
- Implement token blacklist for logout
- Use HTTPS only (no HTTP in production)

### Token Validation

All protected endpoints must:
1. Verify JWT signature
2. Check expiration time
3. Validate issuer and audience
4. Check token against blacklist (if implemented)

---

## 5. WebSocket Security

### Authentication

```javascript
// Authenticate WebSocket connections
socket.on('connection', async (ws, req) => {
  const token = req.headers.authorization?.replace('Bearer ', '');

  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    ws.userId = decoded.userId;
  } catch (error) {
    ws.close(401, 'Unauthorized');
  }
});
```

### Best Practices

- Always use WSS (WebSocket Secure) in production
- Authenticate connections using JWT
- Implement rate limiting per connection
- Validate all incoming messages
- Sanitize data before broadcasting
- Close connections on authentication failure
- Monitor for connection abuse

---

## 6. HTTPS and SSL/TLS

### Certificate Management

- Use Let's Encrypt for free SSL certificates
- Auto-renew certificates (90 days)
- Use strong cipher suites only
- Enable HSTS (HTTP Strict Transport Security)
- Redirect all HTTP to HTTPS

### Nginx Configuration (if using reverse proxy)

```nginx
# Force HTTPS
server {
  listen 80;
  server_name blackbox.example.com;
  return 301 https://$server_name$request_uri;
}

# SSL Configuration
server {
  listen 443 ssl http2;
  server_name blackbox.example.com;

  ssl_certificate /etc/letsencrypt/live/blackbox.example.com/fullchain.pem;
  ssl_certificate_key /etc/letsencrypt/live/blackbox.example.com/privkey.pem;

  # Strong SSL settings
  ssl_protocols TLSv1.2 TLSv1.3;
  ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256';
  ssl_prefer_server_ciphers on;

  # HSTS
  add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
}
```

---

## 7. Input Validation and Sanitization

### Backend Validation

```javascript
// Example: Validate telemetry data
const telemetrySchema = {
  speed: (v) => typeof v === 'number' && v >= 0 && v <= 500,
  rpm: (v) => typeof v === 'number' && v >= 0 && v <= 20000,
  gear: (v) => typeof v === 'number' && v >= -1 && v <= 8,
  throttle: (v) => typeof v === 'number' && v >= 0 && v <= 1,
  brake: (v) => typeof v === 'number' && v >= 0 && v <= 1
};

function validateTelemetry(data) {
  for (const [key, validator] of Object.entries(telemetrySchema)) {
    if (!validator(data[key])) {
      throw new Error(`Invalid ${key}: ${data[key]}`);
    }
  }
  return true;
}
```

### Best Practices

- Validate all user inputs on server-side
- Use whitelists, not blacklists
- Sanitize data before storage
- Escape output to prevent XSS
- Limit request sizes
- Implement rate limiting
- Use parameterized queries for database

---

## 8. Rate Limiting

### API Rate Limits

```javascript
// Express rate limiter
const rateLimit = require('express-rate-limit');

const apiLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // limit each IP to 100 requests per windowMs
  message: 'Too many requests from this IP'
});

app.use('/api/', apiLimiter);

// Stricter limits for auth endpoints
const authLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 5, // 5 login attempts per 15 minutes
  skipSuccessfulRequests: true
});

app.use('/api/auth/login', authLimiter);
```

### WebSocket Rate Limiting

- Limit messages per second per connection
- Limit maximum connections per IP
- Implement exponential backoff for reconnections
- Monitor for DoS patterns

---

## 9. Logging and Monitoring

### What to Log

**DO Log:**
- Authentication attempts (success/failure)
- Authorization failures
- Input validation errors
- Rate limit violations
- System errors and exceptions
- Configuration changes
- Database connection issues

**DON'T Log:**
- Passwords or password hashes
- API keys or tokens
- Credit card numbers
- Personal identification numbers
- Full session tokens

### Monitoring

- Set up alerting for suspicious activity
- Monitor API usage and costs
- Track error rates
- Monitor system resources
- Set up uptime monitoring
- Implement security scanning

---

## 10. Docker Security

### Best Practices

```dockerfile
# Use specific version tags, not 'latest'
FROM node:18-alpine

# Run as non-root user
USER node

# Only copy necessary files
COPY --chown=node:node package*.json ./
COPY --chown=node:node src ./src

# Set read-only root filesystem
# (in docker-compose.yml)
read_only: true
```

### Docker Compose Security

```yaml
services:
  backend:
    # Drop unnecessary capabilities
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE

    # Use read-only root filesystem where possible
    read_only: true
    tmpfs:
      - /tmp

    # Limit resources
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 512M
```

---

## 11. Dependency Management

### Regular Updates

```bash
# Check for outdated packages
npm outdated

# Update dependencies
npm update

# Audit for vulnerabilities
npm audit
npm audit fix
```

### Best Practices

- Review dependencies before adding
- Keep dependencies up to date
- Use `npm audit` regularly
- Pin major versions in package.json
- Use lock files (package-lock.json)
- Remove unused dependencies
- Monitor security advisories

---

## 12. Incident Response Plan

### If a Security Breach Occurs

1. **Immediate Response** (within 1 hour)
   - Isolate affected systems
   - Change all credentials
   - Enable enhanced logging
   - Notify team leads

2. **Investigation** (within 24 hours)
   - Review access logs
   - Identify breach vector
   - Assess data exposure
   - Document findings

3. **Remediation** (within 48 hours)
   - Patch vulnerabilities
   - Restore from clean backups if needed
   - Deploy fixes
   - Verify security

4. **Post-Incident** (within 1 week)
   - Conduct post-mortem
   - Update security procedures
   - Notify affected users if required
   - Implement preventive measures

### Emergency Contacts

- **Security Lead**: [TBD]
- **System Admin**: [TBD]
- **Legal Contact**: [TBD]

---

## 13. Security Checklist for Production Deployment

### Pre-Deployment

- [ ] All API keys moved to environment variables
- [ ] Strong, unique secrets generated for production
- [ ] SSL/TLS certificates configured
- [ ] HTTPS enforced (HTTP redirects to HTTPS)
- [ ] Database passwords changed from defaults
- [ ] JWT secrets are unique and strong (>32 bytes)
- [ ] Rate limiting configured
- [ ] Input validation implemented
- [ ] Audit logging enabled
- [ ] Backup strategy implemented
- [ ] Monitoring and alerting configured
- [ ] Security scanning completed
- [ ] Dependency audit passed (`npm audit`)
- [ ] Docker images scanned for vulnerabilities
- [ ] Access controls reviewed
- [ ] Incident response plan documented

### Post-Deployment

- [ ] Verify HTTPS is working
- [ ] Test authentication and authorization
- [ ] Verify rate limiting is active
- [ ] Check logs for errors
- [ ] Monitor resource usage
- [ ] Test backup restoration
- [ ] Verify alerting works
- [ ] Document production configuration

---

## 14. Compliance and Privacy

### Data Protection

- Implement data retention policies
- Allow users to delete their data
- Encrypt sensitive data at rest
- Use HTTPS for data in transit
- Document data collection practices
- Obtain user consent where required

### GDPR Considerations (if applicable)

- Implement right to access
- Implement right to deletion
- Implement right to data portability
- Document data processing activities
- Implement data breach notification

---

## 15. Additional Resources

### Security Tools

- **OWASP ZAP**: Web application security scanner
- **npm audit**: Dependency vulnerability scanner
- **Snyk**: Continuous security monitoring
- **Let's Encrypt**: Free SSL certificates
- **Fail2Ban**: Intrusion prevention
- **ModSecurity**: Web application firewall

### Learning Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Node.js Security Best Practices](https://nodejs.org/en/docs/guides/security/)
- [Docker Security Best Practices](https://docs.docker.com/engine/security/)
- [PostgreSQL Security](https://www.postgresql.org/docs/current/security.html)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-03 | Initial security best practices documentation |

---

**Last Updated**: December 3, 2025
**Maintainer**: BlackBox Security Team
**Review Schedule**: Quarterly
