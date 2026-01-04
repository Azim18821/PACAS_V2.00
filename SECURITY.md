# PACAS Security & Deployment Guide

## 🔒 Security Features Implemented

### 1. Rate Limiting
- **Global Limits**: 200 requests/day, 50 requests/hour per IP
- **Search Endpoint**: 10 requests/minute per IP
- **Next Page**: 20 requests/minute per IP
- **Combined Search**: 5 requests/minute per IP (most expensive)
- **Cleanup**: 1 request/hour per IP

### 2. ScraperAPI Usage Monitoring
- Daily limit: 1,000 requests (configurable via `MAX_REQUESTS_PER_DAY`)
- Hourly limit: 100 requests (configurable via `MAX_REQUESTS_PER_HOUR`)
- Automatic tracking and blocking when limits exceeded
- Combined searches count as 2 requests

### 3. Input Sanitization
- Location strings sanitized to remove special characters
- Maximum length limits enforced
- Price range validation (max £50M)
- Prevention of excessively wide price ranges

### 4. CORS Configuration
- Configurable allowed origins via `ALLOWED_ORIGINS` env variable
- Default: `*` (development only)
- Production: Set specific domains (comma-separated)

### 5. Database Protection
- Automatic cleanup of expired cache (>24 hours)
- Manual cleanup endpoint: `POST /api/cleanup`
- Prevents database bloat
- Cache hit rate optimization

## 📊 API Endpoints

### Public Endpoints
- `GET /` - Homepage (no rate limit)
- `GET /api/health` - Health check & usage stats (no rate limit)

### Protected Endpoints
- `POST /api/search` - Search properties (10/min)
- `POST /api/search/next-page` - Load next page (20/min)
- `POST /api/search/combined` - Multi-site search (5/min)
- `POST /api/cleanup` - Trigger cleanup (1/hour)

## 🚀 Production Deployment Checklist

### 1. Environment Variables (.env)
```bash
# Required
SCRAPER_API_KEY=your_actual_key_here

# Security (IMPORTANT!)
ALLOWED_ORIGINS=https://yourapp.com,https://www.yourapp.com
MAX_REQUESTS_PER_DAY=1000
MAX_REQUESTS_PER_HOUR=100

# Flask
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=False  # MUST be False in production
```

### 2. Security Hardening
- [ ] Set `FLASK_DEBUG=False`
- [ ] Configure specific `ALLOWED_ORIGINS` (remove `*`)
- [ ] Set appropriate rate limits for your use case
- [ ] Use HTTPS only (set up SSL certificate)
- [ ] Enable firewall rules
- [ ] Use a production WSGI server (Gunicorn/uWSGI)

### 3. Database Maintenance
```bash
# Run daily via cron job
python cleanup_database.py
```

Add to crontab:
```bash
# Run database cleanup daily at 3 AM
0 3 * * * cd /path/to/PACAS_V2.00 && python cleanup_database.py >> logs/cleanup.log 2>&1
```

### 4. Monitoring & Logging
- Check logs regularly: `tail -f logs/app.log`
- Monitor ScraperAPI usage: `GET /api/health`
- Set up alerts for rate limit violations
- Track database size growth

### 5. Production Server Setup

#### Using Gunicorn (Recommended)
```bash
pip install gunicorn

# Start server
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:5000

# With systemd service
sudo nano /etc/systemd/system/pacas.service
```

Example systemd service:
```ini
[Unit]
Description=PACAS Property Search API
After=network.target

[Service]
User=www-data
WorkingDirectory=/path/to/PACAS_V2.00
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:5000

[Install]
WantedBy=multi-user.target
```

#### Using Nginx Reverse Proxy
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

## 🔐 Additional Security Recommendations

### 1. Add Authentication (Future Enhancement)
```python
# Consider implementing:
- JWT tokens for API access
- User registration/login
- API keys per user
- Usage quotas per user
```

### 2. Add Request Logging
```python
# Log all requests with:
- IP address
- Timestamp
- Parameters
- Response time
- Success/failure
```

### 3. Add IP Blacklisting
```python
# Block abusive IPs automatically:
- Track failed requests
- Implement temporary bans
- Whitelist trusted IPs
```

### 4. Add Honeypot Endpoints
```python
# Detect bots and scrapers:
- Hidden endpoints that trigger alerts
- Track suspicious patterns
```

## 📈 Cost Management

### ScraperAPI Cost Estimation
- Free tier: 1,000 requests/month
- With current limits (1,000/day): ~$30-50/month
- Combined searches use 2x credits

### Optimization Tips
1. Rely heavily on 24-hour cache
2. Encourage users to refine searches (fewer results = better UX)
3. Monitor `/api/health` daily usage
4. Adjust limits based on usage patterns

## 🛡️ Security Testing

### Test Rate Limiting
```bash
# Test with curl
for i in {1..15}; do curl -X POST http://localhost:5000/api/search -H "Content-Type: application/json" -d '{"site":"zoopla","location":"Manchester"}'; sleep 1; done
```

### Test Input Sanitization
```bash
# Try injection attacks
curl -X POST http://localhost:5000/api/search \
  -H "Content-Type: application/json" \
  -d '{"site":"zoopla","location":"<script>alert(1)</script>"}'
```

### Check Health Status
```bash
curl http://localhost:5000/api/health
```

## 📞 Incident Response

If rate limits are being hit frequently:
1. Check `/api/health` for usage stats
2. Review logs for patterns: `grep "rate limit" logs/app.log`
3. Identify abusive IPs
4. Adjust limits if legitimate traffic
5. Block IPs in firewall if malicious

## 🔄 Updates & Maintenance

### Weekly
- Review logs for errors
- Check ScraperAPI credit usage
- Monitor database size

### Monthly
- Update dependencies: `pip install --upgrade -r requirements.txt`
- Review and adjust rate limits
- Analyze cache hit rates
- Test all endpoints

### Quarterly
- Security audit
- Update proxy rotation if needed
- Review and optimize database queries
- Update documentation

## 📚 Additional Resources

- [Flask Security Best Practices](https://flask.palletsprojects.com/en/2.3.x/security/)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [ScraperAPI Documentation](https://www.scraperapi.com/documentation/)
