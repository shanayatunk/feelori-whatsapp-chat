# Deployment Guide

This guide covers deploying the Feelori AI WhatsApp Assistant to production environments.

## Pre-Deployment Checklist

### Security Requirements
- [ ] Change all default passwords and API keys
- [ ] Generate secure JWT secrets (minimum 32 characters)
- [ ] Configure proper CORS origins
- [ ] Set up SSL certificates
- [ ] Enable firewall rules
- [ ] Review and update security headers

### Infrastructure Requirements
- [ ] Production MongoDB instance (MongoDB Atlas recommended)
- [ ] Redis cluster or managed Redis service
- [ ] Load balancer (if using multiple instances)
- [ ] Domain name and DNS configuration
- [ ] SSL certificate (Let's Encrypt or commercial)
- [ ] Monitoring and logging infrastructure

### External Service Setup
- [ ] WhatsApp Business API account and verification
- [ ] Shopify private app with required permissions
- [ ] Google Gemini API key with sufficient quota
- [ ] OpenAI API key with sufficient quota
- [ ] Email service for alerts (optional)

## Deployment Options

### Option 1: Docker Deployment (Recommended)

#### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+
- 4GB RAM minimum
- 20GB storage minimum

#### Step 1: Prepare Environment
```bash
# Clone repository
git clone https://github.com/your-username/feelori-ai-assistant.git
cd feelori-ai-assistant

# Create production environment file
cp backend/.env.example backend/.env.prod
```

#### Step 2: Configure Production Environment
Edit `backend/.env.prod`:

```bash
# Database - Use production MongoDB
MONGO_ATLAS_URI=mongodb+srv://user:pass@cluster.mongodb.net/feelori_prod

# WhatsApp Business API - Real credentials
WHATSAPP_ACCESS_TOKEN=your_production_whatsapp_token
WHATSAPP_PHONE_ID=your_production_phone_id
WHATSAPP_VERIFY_TOKEN=your_production_verify_token
WHATSAPP_WEBHOOK_SECRET=your_production_webhook_secret

# Shopify API - Production store
SHOPIFY_STORE_URL=your-production-store.myshopify.com
SHOPIFY_ACCESS_TOKEN=your_production_shopify_token

# AI Services - Production API keys
GEMINI_API_KEY=your_production_gemini_key
OPENAI_API_KEY=your_production_openai_key

# Security - Generate new secure keys
JWT_SECRET_KEY=$(openssl rand -hex 32)
SESSION_SECRET_KEY=$(openssl rand -hex 32)
ADMIN_PASSWORD=your_very_secure_admin_password_with_12plus_chars
API_KEY=$(openssl rand -hex 16)

# Production settings
ENVIRONMENT=production
HTTPS_ONLY=true
CORS_ALLOWED_ORIGINS=https://your-domain.com
ALLOWED_HOSTS=your-domain.com,*.your-domain.com

# Redis - Use production Redis
REDIS_URL=redis://your-redis-host:6379
# For Redis with authentication:
# REDIS_URL=redis://username:password@your-redis-host:6379

# Monitoring (optional)
SENTRY_DSN=your_sentry_dsn
ALERTING_WEBHOOK_URL=your_alerting_webhook_url
```

#### Step 3: Build and Deploy
```bash
# Build production images
docker-compose -f deployment/docker-compose.prod.yml build

# Start services
docker-compose -f deployment/docker-compose.prod.yml up -d

# Check status
docker-compose -f deployment/docker-compose.prod.yml ps
```

#### Step 4: Configure Reverse Proxy
Create nginx configuration:

```nginx
# /etc/nginx/sites-available/feelori-ai
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Increase timeout for AI processing
        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
    }

    # Health checks
    location /health {
        proxy_pass http://localhost:8001;
        access_log off;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/feelori-ai /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### Step 5: Setup SSL with Let's Encrypt
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### Option 2: Manual Deployment

#### Step 1: Server Setup
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3.11 python3.11-venv nodejs npm mongodb redis-server nginx

# Install PM2 for process management
sudo npm install -g pm2

# Create application user
sudo useradd -m -s /bin/bash feelori
sudo usermod -aG sudo feelori
```

#### Step 2: Application Setup
```bash
# Switch to application user
sudo su - feelori

# Clone and setup
git clone https://github.com/your-username/feelori-ai-assistant.git
cd feelori-ai-assistant

# Backend setup
cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Frontend setup
cd ../frontend
npm install
npm run build
```

#### Step 3: Process Management with PM2
Create PM2 ecosystem file (`ecosystem.config.js`):

```javascript
module.exports = {
  apps: [
    {
      name: 'feelori-backend',
      cwd: '/home/feelori/feelori-ai-assistant/backend',
      script: 'venv/bin/gunicorn',
      args: 'app.server:app -w 4 -k uvicorn.workers.UvicornWorker -b 127.0.0.1:8001',
      env: {
        NODE_ENV: 'production',
      },
      error_file: '/var/log/feelori/backend-error.log',
      out_file: '/var/log/feelori/backend-out.log',
      log_file: '/var/log/feelori/backend.log',
      time: true,
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
    },
    {
      name: 'feelori-frontend',
      cwd: '/home/feelori/feelori-ai-assistant/frontend',
      script: 'npx',
      args: 'serve -s build -l 3000',
      error_file: '/var/log/feelori/frontend-error.log',
      out_file: '/var/log/feelori/frontend-out.log',
      log_file: '/var/log/feelori/frontend.log',
      time: true,
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
    }
  ]
};
```

Start services:
```bash
# Create log directory
sudo mkdir -p /var/log/feelori
sudo chown feelori:feelori /var/log/feelori

# Start applications
pm2 start ecosystem.config.js
pm2 save
pm2 startup

# Enable startup on boot
sudo env PATH=$PATH:/usr/bin /usr/lib/node_modules/pm2/bin/pm2 startup systemd -u feelori --hp /home/feelori
```

### Option 3: Kubernetes Deployment

#### Prerequisites
- Kubernetes cluster (1.20+)
- kubectl configured
- Helm 3.0+ (optional but recommended)

#### Step 1: Create Namespace
```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: feelori-ai
```

#### Step 2: ConfigMap and Secrets
```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: feelori-config
  namespace: feelori-ai
data:
  ENVIRONMENT: "production"
  REDIS_URL: "redis://redis:6379"
  CORS_ALLOWED_ORIGINS: "https://your-domain.com"
  ALLOWED_HOSTS: "your-domain.com,*.your-domain.com"
  HTTPS_ONLY: "true"

---
# secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: feelori-secrets
  namespace: feelori-ai
type: Opaque
stringData:
  MONGO_ATLAS_URI: "mongodb+srv://user:pass@cluster.mongodb.net/feelori_prod"
  WHATSAPP_ACCESS_TOKEN: "your_whatsapp_token"
  WHATSAPP_PHONE_ID: "your_phone_id"
  WHATSAPP_VERIFY_TOKEN: "your_verify_token"
  WHATSAPP_WEBHOOK_SECRET: "your_webhook_secret"
  SHOPIFY_STORE_URL: "your-store.myshopify.com"
  SHOPIFY_ACCESS_TOKEN: "your_shopify_token"
  GEMINI_API_KEY: "your_gemini_key"
  OPENAI_API_KEY: "your_openai_key"
  JWT_SECRET_KEY: "your_jwt_secret"
  SESSION_SECRET_KEY: "your_session_secret"
  ADMIN_PASSWORD: "your_admin_password"
  API_KEY: "your_api_key"
```

#### Step 3: Deployments
```yaml
# backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: feelori-backend
  namespace: feelori-ai
spec:
  replicas: 3
  selector:
    matchLabels:
      app: feelori-backend
  template:
    metadata:
      labels:
        app: feelori-backend
    spec:
      containers:
      - name: backend
        image: feelori/backend:latest
        ports:
        - containerPort: 8001
        envFrom:
        - configMapRef:
            name: feelori-config
        - secretRef:
            name: feelori-secrets
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8001
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8001
          initialDelaySeconds: 5
          periodSeconds: 5
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"

---
# frontend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: feelori-frontend
  namespace: feelori-ai
spec:
  replicas: 2
  selector:
    matchLabels:
      app: feelori-frontend
  template:
    metadata:
      labels:
        app: feelori-frontend
    spec:
      containers:
      - name: frontend
        image: feelori/frontend:latest
        ports:
        - containerPort: 3000
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "250m"
```

#### Step 4: Services and Ingress
```yaml
# services.yaml
apiVersion: v1
kind: Service
metadata:
  name: feelori-backend
  namespace: feelori-ai
spec:
  selector:
    app: feelori-backend
  ports:
    - port: 8001
      targetPort: 8001

---
apiVersion: v1
kind: Service
metadata:
  name: feelori-frontend
  namespace: feelori-ai
spec:
  selector:
    app: feelori-frontend
  ports:
    - port: 3000
      targetPort: 3000

---
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: feelori-ingress
  namespace: feelori-ai
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  tls:
  - hosts:
    - your-domain.com
    secretName: feelori-tls
  rules:
  - host: your-domain.com
    http:
      paths:
      - path: /api/
        pathType: Prefix
        backend:
          service:
            name: feelori-backend
            port:
              number: 8001
      - path: /health
        pathType: Prefix
        backend:
          service:
            name: feelori-backend
            port:
              number: 8001
      - path: /
        pathType: Prefix
        backend:
          service:
            name: feelori-frontend
            port:
              number: 3000
```

Deploy to Kubernetes:
```bash
kubectl apply -f namespace.yaml
kubectl apply -f configmap.yaml
kubectl apply -f secret.yaml
kubectl apply -f backend-deployment.yaml
kubectl apply -f frontend-deployment.yaml
kubectl apply -f services.yaml
kubectl apply -f ingress.yaml
```

## Post-Deployment Setup

### WhatsApp Webhook Configuration

1. **Log into WhatsApp Business API Dashboard**
2. **Configure Webhook**:
   - Webhook URL: `https://your-domain.com/api/v1/webhook`
   - Verify Token: Your `WHATSAPP_VERIFY_TOKEN`
3. **Subscribe to Events**:
   - messages
   - message_deliveries
   - message_reads
4. **Test Webhook**:
   ```bash
   curl -X GET "https://your-domain.com/api/v1/webhook?hub.mode=subscribe&hub.challenge=test&hub.verify_token=your_verify_token"
   ```

### Database Setup

#### MongoDB Indexes
```bash
# Connect to MongoDB
mongo your_mongodb_connection_string

# Create indexes for optimal performance
use feelori_assistant

db.customers.createIndex({ "phone_number": 1 }, { unique: true })
db.customers.createIndex({ "created_at": 1 })
db.customers.createIndex({ "conversation_history.timestamp": -1 })
db.security_events.createIndex({ "timestamp": -1, "event_type": 1 })
db.security_events.createIndex({ "ip_address": 1 })
```

#### Initial Data Setup
```javascript
// Create admin user document (if using custom user management)
db.users.insertOne({
  username: "admin",
  role: "admin",
  created_at: new Date(),
  last_login: null,
  active: true
});
```

### SSL Certificate Setup

#### Let's Encrypt (Free)
```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d your-domain.com

# Test renewal
sudo certbot renew --dry-run

# Setup auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

#### Commercial Certificate
```bash
# Generate private key
openssl genrsa -out your-domain.com.key 2048

# Generate CSR
openssl req -new -key your-domain.com.key -out your-domain.com.csr

# Submit CSR to certificate authority
# Download and install certificate files
```

### Monitoring Setup

#### Health Check Monitoring
```bash
# Create monitoring script
cat > /usr/local/bin/feelori-health-check.sh << 'EOF'
#!/bin/bash
HEALTH_URL="https://your-domain.com/health"
WEBHOOK_URL="your-alerting-webhook-url"

if ! curl -f -s "$HEALTH_URL" > /dev/null; then
    curl -X POST "$WEBHOOK_URL" -H "Content-Type: application/json" \
         -d '{"text": "🚨 Feelori AI Assistant health check failed!"}'
fi
EOF

chmod +x /usr/local/bin/feelori-health-check.sh

# Add to crontab
crontab -e
# Add: */5 * * * * /usr/local/bin/feelori-health-check.sh
```

#### Log Monitoring
```bash
# Setup log rotation
cat > /etc/logrotate.d/feelori << 'EOF'
/var/log/feelori/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    copytruncate
}
EOF
```

### Backup Setup

#### Database Backup Script
```bash
#!/bin/bash
# /usr/local/bin/feelori-backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/feelori"
MONGO_URI="your_mongodb_connection_string"

mkdir -p $BACKUP_DIR

# MongoDB backup
mongodump --uri="$MONGO_URI" --out="$BACKUP_DIR/mongo_$DATE"

# Compress backup
tar -czf "$BACKUP_DIR/feelori_backup_$DATE.tar.gz" "$BACKUP_DIR/mongo_$DATE"

# Remove uncompressed files
rm -rf "$BACKUP_DIR/mongo_$DATE"

# Keep only last 7 days
find $BACKUP_DIR -name "feelori_backup_*.tar.gz" -mtime +7 -delete

# Upload to cloud storage (optional)
# aws s3 cp "$BACKUP_DIR/feelori_backup_$DATE.tar.gz" s3://your-backup-bucket/
```

Setup automated backups:
```bash
chmod +x /usr/local/bin/feelori-backup.sh

# Add to crontab for daily backup at 2 AM
crontab -e
# Add: 0 2 * * * /usr/local/bin/feelori-backup.sh
```

## Security Hardening

### System Security
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Configure firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# Disable root login
sudo sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sudo systemctl restart sshd

# Setup fail2ban
sudo apt install fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### Application Security
1. **Environment Variables**: Never commit `.env` files to version control
2. **API Keys**: Rotate API keys regularly
3. **Database Security**: Use strong passwords and limit connections
4. **Network Security**: Use VPC/private networks when possible
5. **Regular Updates**: Keep all dependencies updated

### Security Monitoring
```bash
# Monitor failed login attempts
sudo tail -f /var/log/auth.log | grep "Failed password"

# Monitor application logs for suspicious activity
sudo tail -f /var/log/feelori/backend.log | grep -i "error\|warning"

# Check SSL certificate expiration
echo | openssl s_client -servername your-domain.com -connect your-domain.com:443 2>/dev/null | openssl x509 -noout -dates
```

## Performance Optimization

### Database Optimization
```javascript
// MongoDB performance settings
use feelori_assistant

// Check index usage
db.customers.aggregate([{$indexStats: {}}])

// Monitor slow queries
db.setProfilingLevel(2, { slowms: 100 })
db.system.profile.find().limit(5).sort({ ts: -1 }).pretty()
```

### Caching Configuration
```bash
# Redis configuration for production
cat > /etc/redis/redis-feelori.conf << 'EOF'
bind 127.0.0.1
port 6379
timeout 300
keepalive 60
maxmemory 1gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
EOF
```

### Load Balancing
If using multiple instances:

```nginx
# Nginx upstream configuration
upstream feelori_backend {
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
    server 127.0.0.1:8003;
}

upstream feelori_frontend {
    server 127.0.0.1:3000;
    server 127.0.0.1:3001;
}

# Use in server block
location /api/ {
    proxy_pass http://feelori_backend;
    # ... other proxy settings
}

location / {
    proxy_pass http://feelori_frontend;
    # ... other proxy settings
}
```

## Troubleshooting Deployment Issues

### Common Issues

#### 1. SSL Certificate Issues
```bash
# Check certificate status
sudo certbot certificates

# Renew certificate manually
sudo certbot renew --force-renewal -d your-domain.com

# Check nginx SSL configuration
sudo nginx -t
```

#### 2. Database Connection Issues
```bash
# Test MongoDB connection
mongo your_mongodb_connection_string --eval "db.adminCommand('ping')"

# Check MongoDB logs
sudo tail -f /var/log/mongodb/mongod.log
```

#### 3. Redis Connection Issues
```bash
# Test Redis connection
redis-cli -h your-redis-host ping

# Check Redis logs
sudo tail -f /var/log/redis/redis-server.log
```

#### 4. Application Not Starting
```bash
# Check PM2 status
pm2 status
pm2 logs feelori-backend
pm2 logs feelori-frontend

# For Docker deployment
docker-compose -f deployment/docker-compose.prod.yml logs -f

# For Kubernetes deployment
kubectl logs -n feelori-ai deployment/feelori-backend
kubectl logs -n feelori-ai deployment/feelori-frontend
```

#### 5. WhatsApp Webhook Not Working
```bash
# Test webhook endpoint
curl -X GET "https://your-domain.com/api/v1/webhook?hub.mode=subscribe&hub.challenge=test&hub.verify_token=your_token"

# Check webhook logs
tail -f /var/log/feelori/backend.log | grep webhook

# Test from external server
curl -X POST "https://your-domain.com/api/v1/webhook" \
  -H "Content-Type: application/json" \
  -d '{"test": "message"}'
```

### Deployment Rollback

#### Docker Rollback
```bash
# Keep previous image tagged
docker tag feelori/backend:latest feelori/backend:previous

# Rollback to previous version
docker-compose -f deployment/docker-compose.prod.yml down
docker tag feelori/backend:previous feelori/backend:latest
docker-compose -f deployment/docker-compose.prod.yml up -d
```

#### Kubernetes Rollback
```bash
# Rollback deployment
kubectl rollout undo deployment/feelori-backend -n feelori-ai
kubectl rollout undo deployment/feelori-frontend -n feelori-ai

# Check rollout status
kubectl rollout status deployment/feelori-backend -n feelori-ai
```

---

*For additional support, contact: support@feelori.com*