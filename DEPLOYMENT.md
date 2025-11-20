# AYITI AI - Production Deployment Guide

Complete guide for deploying AYITI AI to production.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Server Requirements](#server-requirements)
3. [Deployment Options](#deployment-options)
4. [Docker Deployment](#docker-deployment)
5. [Manual Deployment](#manual-deployment)
6. [Security Configuration](#security-configuration)
7. [Monitoring & Maintenance](#monitoring--maintenance)
8. [Scaling](#scaling)
9. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required
- Ubuntu 20.04+ or Debian 11+ server
- Python 3.8 or higher
- 2GB+ RAM minimum (4GB+ recommended)
- 10GB+ disk space
- SSL certificate (Let's Encrypt recommended)
- Domain name (e.g., api.ayitiai.ht)

### API Keys
- DeepSeek API key ([get one here](https://platform.deepseek.com))
- Optional: Redis for distributed caching

---

## Server Requirements

### Minimum Specifications
- **CPU**: 2 cores
- **RAM**: 2GB
- **Storage**: 10GB SSD
- **Network**: 100 Mbps

### Recommended for Production
- **CPU**: 4 cores
- **RAM**: 8GB
- **Storage**: 50GB SSD
- **Network**: 1 Gbps
- **Load Balancer**: For high availability

---

## Deployment Options

### Option 1: Docker (Recommended)
- Easiest to deploy and maintain
- Consistent across environments
- Easy to scale with Docker Compose or Kubernetes

### Option 2: Manual Installation
- More control over configuration
- Better for custom setups
- Requires more maintenance

### Option 3: Cloud Platform
- **Heroku**: Easy deployment, auto-scaling
- **AWS ECS/Fargate**: Production-grade, scalable
- **Google Cloud Run**: Serverless, pay-per-use
- **DigitalOcean App Platform**: Simple, affordable

---

## Docker Deployment

### Step 1: Clone Repository

```bash
git clone https://github.com/YOUR-ORG/ayitiai.git
cd ayitiai
```

### Step 2: Configure Environment

```bash
cp .env.example .env
nano .env
```

Update these critical values:
```bash
DEEPSEEK_API_KEY=your_actual_api_key_here
SECRET_KEY=your_generated_secret_key_here
DEBUG_MODE=false
API_HOST=0.0.0.0
API_PORT=8000
```

Generate a secure secret key:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Step 3: Build and Run

```bash
# Build image
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f app

# Check status
docker-compose ps
```

### Step 4: Initialize Knowledge Bases

```bash
# Run initialization inside container
docker-compose exec app python scripts/init_all_kb.py
```

### Step 5: Verify Deployment

```bash
# Health check
curl http://localhost:8000/health

# System stats
curl http://localhost:8000/api/v1/stats/overview

# Test query
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"message": "Kijan pou m plante bannann?"}'
```

---

## Manual Deployment

### Step 1: System Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3-pip python3-venv nginx certbot python3-certbot-nginx

# Create application user
sudo useradd -m -s /bin/bash ayitiai
sudo su - ayitiai
```

### Step 2: Application Setup

```bash
# Clone repository
git clone https://github.com/YOUR-ORG/ayitiai.git
cd ayitiai

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 3: Configure Environment

```bash
cp .env.example .env
nano .env
```

Set production values:
```bash
DEEPSEEK_API_KEY=your_key
SECRET_KEY=your_secret
DEBUG_MODE=false
VECTOR_DB_PATH=/home/ayitiai/ayitiai/data/vector_db
COST_LIMIT_DAILY=100.00
```

### Step 4: Initialize Knowledge Bases

```bash
python scripts/init_all_kb.py
```

### Step 5: Setup Systemd Service

```bash
# Exit ayitiai user
exit

# Create service file
sudo nano /etc/systemd/system/ayitiai.service
```

Use the provided `ayitiai.service` file (see below).

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable ayitiai
sudo systemctl start ayitiai
sudo systemctl status ayitiai
```

### Step 6: Configure Nginx

```bash
sudo nano /etc/nginx/sites-available/ayitiai
```

Use the provided `nginx.conf` (see below).

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/ayitiai /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Step 7: Setup SSL

```bash
# Get Let's Encrypt certificate
sudo certbot --nginx -d api.ayitiai.ht

# Auto-renewal is configured automatically
sudo certbot renew --dry-run
```

---

## Security Configuration

### 1. Firewall Setup

```bash
# Allow SSH, HTTP, HTTPS
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 2. Rate Limiting

Nginx configuration already includes rate limiting:
- 10 requests/second per IP
- Burst of 20 requests
- Prevents abuse and DDoS

### 3. API Key Protection

```bash
# Restrict .env file permissions
chmod 600 .env

# Never commit .env to git
# Already in .gitignore
```

### 4. CORS Configuration

Update `api/app.py` for production:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Specific domains only
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

### 5. Security Headers

Nginx configuration includes:
- X-Frame-Options
- X-Content-Type-Options
- X-XSS-Protection
- Strict-Transport-Security (HSTS)

---

## Monitoring & Maintenance

### 1. Application Logs

```bash
# Systemd logs
sudo journalctl -u ayitiai -f

# Docker logs
docker-compose logs -f

# Application logs
tail -f /home/ayitiai/ayitiai/logs/app.log
```

### 2. Performance Monitoring

```bash
# Check system stats
curl http://localhost:8000/api/v1/stats/overview

# Monitor with watch
watch -n 5 'curl -s http://localhost:8000/api/v1/stats/performance | jq'
```

### 3. Database Backup

```bash
# Backup vector database
tar -czf vector_db_backup_$(date +%Y%m%d).tar.gz data/vector_db/

# Backup to S3 (if using AWS)
aws s3 cp vector_db_backup_*.tar.gz s3://your-backup-bucket/
```

### 4. Log Rotation

```bash
sudo nano /etc/logrotate.d/ayitiai
```

```
/home/ayitiai/ayitiai/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 ayitiai ayitiai
    sharedscripts
    postrotate
        systemctl reload ayitiai > /dev/null 2>&1 || true
    endscript
}
```

### 5. Automated Maintenance

Create cron jobs:
```bash
crontab -e
```

```cron
# Cleanup expired cache daily at 2 AM
0 2 * * * curl -X POST http://localhost:8000/api/v1/admin/cache/cleanup

# Cleanup expired conversations daily at 3 AM
0 3 * * * curl -X POST http://localhost:8000/api/v1/admin/conversations/cleanup

# Backup database weekly on Sunday at 1 AM
0 1 * * 0 cd /home/ayitiai/ayitiai && tar -czf backups/vector_db_$(date +\%Y\%m\%d).tar.gz data/vector_db/
```

---

## Scaling

### Horizontal Scaling

#### 1. Load Balancer Setup

```nginx
upstream ayitiai_backend {
    least_conn;
    server 10.0.1.10:8000;
    server 10.0.1.11:8000;
    server 10.0.1.12:8000;
}

server {
    listen 80;
    server_name api.ayitiai.ht;

    location / {
        proxy_pass http://ayitiai_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

#### 2. Shared Vector Database

Use network-mounted storage:
```bash
# NFS mount on all servers
sudo mount -t nfs 10.0.1.100:/vector_db /home/ayitiai/ayitiai/data/vector_db
```

#### 3. Redis for Shared Caching

Update `.env`:
```bash
REDIS_HOST=your-redis-server.com
REDIS_PORT=6379
CACHE_BACKEND=redis
```

### Vertical Scaling

```bash
# Increase workers in systemd service
# Edit: /etc/systemd/system/ayitiai.service
ExecStart=/home/ayitiai/ayitiai/venv/bin/uvicorn api.app:app --host 0.0.0.0 --port 8000 --workers 4

sudo systemctl daemon-reload
sudo systemctl restart ayitiai
```

### Auto-Scaling (Cloud)

**AWS Auto Scaling Group**:
- Min instances: 2
- Max instances: 10
- Target CPU: 70%
- Scale-up: +2 instances when CPU > 70% for 5 min
- Scale-down: -1 instance when CPU < 30% for 10 min

---

## Troubleshooting

### Issue: Service Won't Start

```bash
# Check logs
sudo journalctl -u ayitiai -n 50

# Check permissions
ls -la /home/ayitiai/ayitiai/

# Verify environment
cd /home/ayitiai/ayitiai
source venv/bin/activate
python -c "from core.config_manager import settings; print(settings.deepseek_api_key[:10])"
```

### Issue: High Memory Usage

```bash
# Monitor memory
free -h
htop

# Reduce cache size in .env
CACHE_MAX_SIZE=500  # Reduce from 1000

# Restart service
sudo systemctl restart ayitiai
```

### Issue: Slow Response Times

```bash
# Check performance stats
curl http://localhost:8000/api/v1/stats/performance

# Check cache hit rate
curl http://localhost:8000/api/v1/stats/cache

# Review slow queries
sudo journalctl -u ayitiai | grep "processed in"
```

### Issue: Cost Limit Reached

```bash
# Check current costs
curl http://localhost:8000/api/v1/stats/cost

# Increase limit in .env
COST_LIMIT_DAILY=200.00

# Or wait for daily reset
# Costs reset at midnight UTC
```

---

## Health Checks

### Basic Health Check

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "AYITI AI"
}
```

### Comprehensive Health Check

```bash
#!/bin/bash
# health-check.sh

API_URL="http://localhost:8000"

# Test health endpoint
health=$(curl -s $API_URL/health | jq -r '.status')
if [ "$health" != "healthy" ]; then
    echo "CRITICAL: Health check failed"
    exit 2
fi

# Test query endpoint
query_test=$(curl -s -X POST $API_URL/api/v1/query \
    -H "Content-Type: application/json" \
    -d '{"message": "test"}' | jq -r '.response')

if [ -z "$query_test" ]; then
    echo "WARNING: Query endpoint not responding"
    exit 1
fi

# Check cost limits
cost=$(curl -s $API_URL/api/v1/stats/cost | jq -r '.daily_cost')
limit=$(curl -s $API_URL/api/v1/stats/cost | jq -r '.limit')

if (( $(echo "$cost > $limit * 0.9" | bc -l) )); then
    echo "WARNING: Cost at 90% of daily limit"
fi

echo "OK: All health checks passed"
exit 0
```

---

## Production Checklist

Before going live:

- [ ] DeepSeek API key configured
- [ ] Secret key generated and set
- [ ] DEBUG_MODE=false
- [ ] SSL certificate installed
- [ ] Firewall configured
- [ ] All 6 knowledge bases initialized
- [ ] Nginx reverse proxy configured
- [ ] Systemd service enabled
- [ ] Log rotation configured
- [ ] Backup strategy implemented
- [ ] Monitoring setup (optional: Prometheus, Grafana)
- [ ] Rate limiting configured
- [ ] CORS properly restricted
- [ ] Health checks passing
- [ ] Load testing completed
- [ ] Documentation reviewed

---

## Support & Resources

- **Documentation**: See README.md and QUICKSTART.md
- **API Docs**: https://api.ayitiai.ht/docs
- **Issues**: https://github.com/YOUR-ORG/ayitiai/issues
- **Community**: [Discord/Slack channel]

---

## License

[Your License Here]

---

**Ready to Help Haiti! 🇭🇹**
