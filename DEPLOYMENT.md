# TaskWall Deployment Guide

This guide covers deployment options for TaskWall in different environments.

## Quick Start (Docker Compose)

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- 2GB RAM minimum
- 5GB disk space

### 1. Clone and Start

```bash
git clone <repository> taskwall
cd taskwall
docker-compose up -d
```

### 2. Access Application

- **Frontend**: http://localhost:3000
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### 3. Configure (Optional)

Go to Settings in the web interface to:
- Add Gemini API key for AI parsing
- Configure backup intervals
- Customize modules and colors

## Production Deployment

### Automated Build

Use the production build script for optimized deployment:

```bash
./scripts/build-production.sh
```

This creates a `build/` directory with:
- Optimized Docker images
- Deployment configuration
- Quick start script
- Build report

### Manual Build

```bash
# Build optimized images
docker-compose build --parallel

# Start in production mode
docker-compose up -d --force-recreate
```

### Reverse Proxy Setup (Nginx)

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # API
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### SSL/HTTPS Setup

```bash
# Using Let's Encrypt with Certbot
sudo certbot --nginx -d your-domain.com
```

## Environment Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | SQLite database path | `sqlite:///data/taskwall.db` |
| `GEMINI_API_KEY` | Google Gemini API key | None (optional) |
| `TZ` | Timezone | `Asia/Shanghai` |

### Port Configuration

Edit `docker-compose.yml` to change ports:

```yaml
services:
  web:
    ports:
      - "8080:80"  # Change frontend port
  api:
    ports:
      - "9000:8000"  # Change API port
```

## Data Management

### Backup

Backups are created automatically every 4 hours in `./data/backup/`:
- JSON format for data restoration
- Markdown format for human reading

Manual backup:
```bash
curl -X POST http://localhost:8000/backup/create
```

### Restore

1. Stop the application
2. Replace database file
3. Restart the application

```bash
docker-compose down
cp backup/taskwall_backup_YYYYMMDD_HHMMSS.json data/taskwall.db
docker-compose up -d
```

### Data Migration

Export from one instance:
```bash
curl http://localhost:8000/export/json > export.json
```

Import to another instance:
```bash
# Copy export.json to new instance
# Import functionality can be added as needed
```

## Monitoring

### Health Checks

All services include health checks:
- Backend: `GET /health`
- Frontend: HTTP 200 response
- Database: Automatic connection testing

### Logs

View logs:
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f web
```

### Resource Usage

Monitor resource usage:
```bash
docker stats
```

Expected usage:
- Backend: 100-200MB RAM
- Frontend: 50-100MB RAM
- Database: 10-50MB disk (grows with data)

## Scaling

### Horizontal Scaling

Currently supports single-instance deployment. For multi-instance:
1. Use external database (PostgreSQL/MySQL)
2. Share file storage
3. Load balancer configuration

### Performance Optimization

1. **Enable gzip compression** in reverse proxy
2. **Configure caching** for static assets
3. **Use CDN** for global distribution
4. **Monitor database** performance

## Security

### Network Security

- Use HTTPS in production
- Configure firewall rules
- Use VPN for admin access

### Application Security

- Regular updates of dependencies
- API rate limiting (configure in reverse proxy)
- Regular backup verification

### Database Security

- SQLite file permissions (600)
- Regular backup encryption
- Monitor access logs

## Troubleshooting

### Common Issues

**Port already in use:**
```bash
# Check what's using the port
sudo netstat -tulpn | grep :3000
# Change port in docker-compose.yml
```

**Permission denied:**
```bash
# Fix data directory permissions
sudo chown -R $(id -u):$(id -g) data/
```

**Out of disk space:**
```bash
# Clean old Docker images
docker system prune -a
# Archive old backups
mv data/backup/old/* /archive/
```

**Database locked:**
```bash
# Stop all instances
docker-compose down
# Wait 30 seconds
sleep 30
# Restart
docker-compose up -d
```

### Performance Issues

**Slow loading:**
1. Check Docker resource limits
2. Verify database size
3. Monitor network connectivity

**High memory usage:**
1. Check for memory leaks in logs
2. Restart services periodically
3. Monitor task count and complexity

### Debug Mode

Enable debug logging:
```yaml
# In docker-compose.yml
services:
  api:
    environment:
      - LOG_LEVEL=debug
```

## Support

For issues and questions:
1. Check logs: `docker-compose logs`
2. Verify configuration
3. Review this deployment guide
4. Create issue with logs and configuration details