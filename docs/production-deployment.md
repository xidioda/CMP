# CMP Production Deployment Guide

This guide provides comprehensive instructions for deploying the CMP (Company Management Platform) application to a production environment.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Security Configuration](#security-configuration)
4. [Deployment Options](#deployment-options)
5. [Monitoring and Logging](#monitoring-and-logging)
6. [Backup and Recovery](#backup-and-recovery)
7. [Troubleshooting](#troubleshooting)
8. [Maintenance](#maintenance)

## Prerequisites

### System Requirements

- **Operating System**: Ubuntu 20.04+ / CentOS 8+ / RHEL 8+
- **CPU**: 2+ cores (4+ recommended for production)
- **RAM**: 4GB minimum (8GB+ recommended)
- **Storage**: 20GB minimum (100GB+ for production with logs/backups)
- **Network**: HTTPS/SSL certificate for production domain

### Software Dependencies

- **Docker**: 20.10+ ([Installation Guide](https://docs.docker.com/engine/install/))
- **Docker Compose**: 2.0+ ([Installation Guide](https://docs.docker.com/compose/install/))
- **Git**: For cloning the repository
- **OpenSSL**: For SSL certificate management

### Domain and DNS

- Registered domain name pointing to your server
- SSL certificate (Let's Encrypt recommended for free certificates)

## Environment Setup

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/cmp.git
cd cmp
```

### 2. Configure Environment Variables

Copy the example environment file and configure it:

```bash
cp .env.example .env
```

Edit `.env` with your production values:

```bash
nano .env
```

**Critical Configuration Items:**

```bash
# Application
DEBUG=false
ENVIRONMENT=production
SECRET_KEY=your-super-secure-secret-key-here-minimum-32-chars
ALLOWED_HOSTS=your-domain.com,www.your-domain.com

# Database
DATABASE_URL=postgresql://cmp_user:secure_password@db:5432/cmp_prod
DB_PASSWORD=secure_database_password

# Authentication
JWT_SECRET_KEY=your-jwt-secret-minimum-64-characters-long

# API Integrations
ZOHO_CLIENT_ID=your_zoho_client_id
ZOHO_CLIENT_SECRET=your_zoho_client_secret
ZOHO_ORGANIZATION_ID=your_zoho_org_id

# Security
CORS_ORIGINS=https://your-domain.com
SESSION_COOKIE_SECURE=true
SSL_REDIRECT=true
```

### 3. SSL Certificate Setup

#### Option A: Let's Encrypt (Recommended)

```bash
# Install Certbot
sudo apt-get update
sudo apt-get install certbot

# Generate certificate
sudo certbot certonly --standalone -d your-domain.com

# Copy certificates to project
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ssl/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem ssl/key.pem
sudo chown $(whoami):$(whoami) ssl/*.pem
```

#### Option B: Self-Signed (Development Only)

```bash
mkdir -p ssl
openssl req -x509 -newkey rsa:4096 -keyout ssl/key.pem -out ssl/cert.pem -days 365 -nodes
```

## Security Configuration

### 1. Firewall Setup

```bash
# Ubuntu/Debian
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# CentOS/RHEL
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

### 2. Docker Security

Ensure Docker daemon is configured securely:

```bash
# Add current user to docker group
sudo usermod -aG docker $USER

# Restart and re-login
sudo systemctl restart docker
```

### 3. File Permissions

```bash
# Set proper file permissions
chmod 600 .env
chmod 600 ssl/*.pem
chmod +x scripts/deployment/*.sh
```

## Deployment Options

### Option 1: Automated Deployment (Recommended)

Use the provided deployment script:

```bash
./scripts/deployment/deploy.sh
```

This script will:
- Check prerequisites
- Validate configuration
- Set up SSL certificates
- Create necessary directories
- Build and start services
- Run database migrations
- Perform health checks
- Create initial backup

### Option 2: Manual Deployment

If you prefer manual control:

```bash
# 1. Create directories
mkdir -p local_storage/{bank_statements,invoices,ml_models}
mkdir -p logs backups

# 2. Build and start services
docker-compose build --no-cache
docker-compose up -d

# 3. Wait for services to be ready
docker-compose ps

# 4. Run database migrations
docker-compose exec app python -c "from cmp.db import init_db; init_db()"

# 5. Verify deployment
curl -f http://localhost:8000/health
```

### Option 3: CI/CD Deployment

The project includes GitHub Actions workflows for automated deployment:

1. **Push to main branch** triggers the production deployment
2. **Pull requests** trigger testing and security scans
3. **Scheduled runs** check for dependency updates

Configure these secrets in your GitHub repository:
- `GITHUB_TOKEN` (automatically provided)
- Any additional deployment secrets

## Monitoring and Logging

### 1. Enable Monitoring (Optional)

Add to your `.env`:

```bash
PROMETHEUS_ENABLED=true
GRAFANA_ENABLED=true
```

Access monitoring:
- **Prometheus**: http://your-domain.com:9090
- **Grafana**: http://your-domain.com:3000

### 2. Log Management

View application logs:

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f app

# Application logs
tail -f logs/cmp.log
```

### 3. Health Monitoring

The application provides health endpoints:
- **Basic Health**: `/health`
- **Detailed Health**: `/health/detailed`
- **Database Health**: `/health/db`

## Backup and Recovery

### 1. Automated Backups

Backups are configured in `docker-compose.yml` and run daily at 2 AM.

### 2. Manual Backup

```bash
# Database backup
docker-compose exec db pg_dump -U cmp_user cmp_prod > backups/manual_backup_$(date +%Y%m%d_%H%M%S).sql

# File system backup
tar -czf backups/files_backup_$(date +%Y%m%d_%H%M%S).tar.gz local_storage/
```

### 3. Recovery

```bash
# Restore database
docker-compose exec -T db psql -U cmp_user cmp_prod < backups/backup_file.sql

# Restore files
tar -xzf backups/files_backup.tar.gz
```

## Troubleshooting

### Common Issues

#### 1. Application Won't Start

```bash
# Check container status
docker-compose ps

# Check logs
docker-compose logs app

# Common fixes
docker-compose restart app
```

#### 2. Database Connection Issues

```bash
# Check database status
docker-compose logs db

# Verify database is ready
docker-compose exec db pg_isready -U cmp_user

# Reset database
docker-compose down -v
docker-compose up -d
```

#### 3. SSL Certificate Issues

```bash
# Check certificate validity
openssl x509 -in ssl/cert.pem -text -noout

# Renew Let's Encrypt certificate
sudo certbot renew
```

#### 4. Permission Issues

```bash
# Fix file permissions
sudo chown -R $(whoami):$(whoami) local_storage/
sudo chown -R $(whoami):$(whoami) logs/
```

### Performance Issues

1. **Monitor resource usage**:
   ```bash
   docker stats
   ```

2. **Check database performance**:
   ```bash
   docker-compose exec db psql -U cmp_user cmp_prod -c "SELECT * FROM pg_stat_activity;"
   ```

3. **Review application logs for slow queries**:
   ```bash
   grep "slow" logs/cmp.log
   ```

## Maintenance

### 1. Regular Updates

```bash
# Update application
git pull origin main
docker-compose build --no-cache
docker-compose up -d

# Update dependencies (automated via GitHub Actions)
```

### 2. Log Rotation

Configure log rotation to prevent disk space issues:

```bash
# Add to crontab
0 0 * * * find /path/to/cmp/logs -name "*.log" -mtime +30 -delete
```

### 3. Certificate Renewal

For Let's Encrypt certificates:

```bash
# Add to crontab for automatic renewal
0 0 1 * * sudo certbot renew --quiet
```

### 4. Database Maintenance

```bash
# Vacuum database monthly
0 0 1 * * docker-compose exec db psql -U cmp_user cmp_prod -c "VACUUM ANALYZE;"
```

### 5. Security Updates

- Monitor security advisories for dependencies
- Review GitHub Dependabot alerts
- Apply security patches promptly
- Regularly review access logs

## Production Checklist

Before going live, ensure:

- [ ] All environment variables configured
- [ ] SSL certificates installed and valid
- [ ] Firewall configured properly
- [ ] Backups working and tested
- [ ] Monitoring enabled
- [ ] Log rotation configured
- [ ] Health checks passing
- [ ] Security scan results reviewed
- [ ] Load testing completed
- [ ] Recovery procedures tested
- [ ] Team trained on operations

## Support

For additional support:

1. **Documentation**: Check `docs/` directory
2. **Issues**: Create GitHub issues for bugs
3. **Logs**: Always include relevant logs when reporting issues
4. **Community**: Check existing issues and discussions

---

**Last Updated**: $(date)
**Version**: 1.0
**Environment**: Production