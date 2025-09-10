# 🚀 Stardust.ai Chatbot Deployment Guide

This guide covers multiple deployment options for the Stardust.ai Chatbot, from simple cloud platforms to advanced containerized deployments.

## 📋 Prerequisites

- Python 3.8+ installed
- Git installed
- OpenAI API key
- (Optional) Other API keys (Bing, Google, etc.)

## 🌐 Cloud Deployment Options

### 1. Streamlit Cloud (Recommended for Quick Start)

**One-Click Deployment:**

[![Deploy to Streamlit Cloud](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/)

**Manual Setup:**

1. **Fork the repository** on GitHub
2. **Go to [Streamlit Cloud](https://share.streamlit.io/)**
3. **Click "New app"**
4. **Configure deployment:**
   - Repository: `your-username/chatbot`
   - Branch: `main`
   - Main file: `app.py`
   - App URL: `your-app-name`

5. **Add secrets** in Streamlit Cloud dashboard:
   ```toml
   openai-key = "your-openai-api-key"
   debug = false
   streaming = true
   ```

6. **Deploy!** Your app will be available at `https://your-app-name.streamlit.app`

### 2. Hugging Face Spaces

1. **Create a new Space** on [Hugging Face](https://huggingface.co/new-space)
2. **Choose Streamlit SDK**
3. **Upload your files** or connect to GitHub
4. **Configure secrets** in Space settings
5. **Deploy!**

### 3. Heroku

1. **Install Heroku CLI**
2. **Login to Heroku:**
   ```bash
   heroku login
   ```

3. **Create Heroku app:**
   ```bash
   heroku create your-app-name
   ```

4. **Set environment variables:**
   ```bash
   heroku config:set OPENAI_API_KEY=your-api-key
   heroku config:set DEBUG=false
   heroku config:set STREAMING=true
   ```

5. **Deploy:**
   ```bash
   git push heroku main
   ```

### 4. Railway

1. **Connect GitHub repository** to [Railway](https://railway.app/)
2. **Set environment variables** in Railway dashboard
3. **Deploy automatically** on git push

### 5. Render

1. **Connect GitHub repository** to [Render](https://render.com/)
2. **Create new Web Service**
3. **Configure:**
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0`
4. **Set environment variables**
5. **Deploy!**

## 🐳 Docker Deployment

### Local Docker

1. **Build the image:**
   ```bash
   docker build -t stardust-chatbot .
   ```

2. **Run the container:**
   ```bash
   docker run -p 8501:8501 \
     -e OPENAI_API_KEY=your-api-key \
     stardust-chatbot
   ```

3. **Access at:** `http://localhost:8501`

### Docker Compose

1. **Create `.env` file:**
   ```env
   OPENAI_API_KEY=your-openai-api-key
   BING_COOKIE=your-bing-cookie
   GOOGLE_API_KEY=your-google-api-key
   ```

2. **Run with Docker Compose:**
   ```bash
   docker-compose up -d
   ```

3. **Access at:** `http://localhost:8501`

### Docker Hub Deployment

1. **Build and tag image:**
   ```bash
   docker build -t your-username/stardust-chatbot .
   ```

2. **Push to Docker Hub:**
   ```bash
   docker push your-username/stardust-chatbot
   ```

3. **Deploy anywhere** using the image:
   ```bash
   docker run -p 8501:8501 \
     -e OPENAI_API_KEY=your-api-key \
     your-username/stardust-chatbot
   ```

## ☁️ Cloud Platform Deployment

### AWS

#### Using AWS App Runner

1. **Create App Runner service**
2. **Connect to GitHub repository**
3. **Configure build settings:**
   - Build command: `pip install -r requirements.txt`
   - Start command: `streamlit run app.py --server.port=8080 --server.address=0.0.0.0`
4. **Set environment variables**
5. **Deploy!**

#### Using AWS ECS with Fargate

1. **Create ECS cluster**
2. **Create task definition** with your Docker image
3. **Create service** and configure load balancer
4. **Set up auto-scaling**

### Google Cloud Platform

#### Using Cloud Run

1. **Build and push image:**
   ```bash
   gcloud builds submit --tag gcr.io/PROJECT-ID/stardust-chatbot
   ```

2. **Deploy to Cloud Run:**
   ```bash
   gcloud run deploy --image gcr.io/PROJECT-ID/stardust-chatbot \
     --platform managed --region us-central1 \
     --allow-unauthenticated
   ```

### Microsoft Azure

#### Using Container Instances

1. **Create container group:**
   ```bash
   az container create \
     --resource-group myResourceGroup \
     --name stardust-chatbot \
     --image your-username/stardust-chatbot \
     --ports 8501 \
     --environment-variables OPENAI_API_KEY=your-api-key
   ```

## 🔧 Environment Configuration

### Required Environment Variables

```bash
# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key

# Optional API Keys
BING_COOKIE=your-bing-cookie
GOOGLE_API_KEY=your-google-api-key

# Application Settings
DEBUG=false
STREAMING=true
PORT=8501

# Database (Optional)
DATABASE_URL=sqlite:///data/chatbot.db

# Analytics (Optional)
SENTRY_DSN=your-sentry-dsn
ANALYTICS_ENABLED=true
```

### Streamlit Secrets Configuration

Create `.streamlit/secrets.toml`:

```toml
# OpenAI Configuration
openai-key = "your-openai-api-key"

# Debug Settings
debug = false
streaming = true

# Optional API Keys
bing-cookie = "your-bing-cookie"
google-api-key = "your-google-api-key"

# Database Configuration
database-url = "sqlite:///data/chatbot.db"

# Analytics Configuration
analytics-enabled = true
sentry-dsn = "your-sentry-dsn"
```

## 📊 Monitoring and Analytics

### Health Checks

The application includes health check endpoints:

- **Health Check:** `/_stcore/health`
- **Metrics:** `/metrics` (if enabled)

### Performance Monitoring

1. **Enable Sentry** for error tracking
2. **Use built-in analytics** dashboard
3. **Monitor response times** and usage metrics

### Logging

Configure logging levels:

```python
import logging
logging.basicConfig(level=logging.INFO)
```

## 🔒 Security Considerations

### API Key Security

- **Never commit API keys** to version control
- **Use environment variables** or secrets management
- **Rotate keys regularly**
- **Use least privilege principle**

### Network Security

- **Use HTTPS** in production
- **Configure CORS** properly
- **Implement rate limiting**
- **Use firewall rules**

### Data Protection

- **Encrypt sensitive data**
- **Implement data retention policies**
- **Use secure database connections**
- **Regular security audits**

## 🚀 Production Optimization

### Performance Tuning

1. **Enable caching:**
   ```python
   from tools.performance import cache_manager
   cache_manager.set("key", "value", ttl=3600)
   ```

2. **Use async processing:**
   ```python
   from tools.performance import async_processor
   results = await async_processor.process_multiple_requests(requests)
   ```

3. **Optimize database queries**
4. **Use CDN for static assets**
5. **Implement connection pooling**

### Scaling Considerations

- **Horizontal scaling** with load balancers
- **Database scaling** with read replicas
- **Caching layers** (Redis, Memcached)
- **Auto-scaling** based on metrics

## 🔄 CI/CD Pipeline

### GitHub Actions

The repository includes GitHub Actions for:

- **Automated testing**
- **Docker image building**
- **Deployment to multiple platforms**
- **Security scanning**

### Deployment Pipeline

1. **Code push** triggers CI/CD
2. **Run tests** and quality checks
3. **Build Docker image**
4. **Deploy to staging**
5. **Run integration tests**
6. **Deploy to production**

## 📝 Troubleshooting

### Common Issues

#### 1. API Key Not Working

```bash
# Check environment variable
echo $OPENAI_API_KEY

# Verify in Streamlit secrets
st.secrets["openai-key"]
```

#### 2. Port Issues

```bash
# Check if port is available
netstat -tulpn | grep :8501

# Use different port
streamlit run app.py --server.port=8502
```

#### 3. Memory Issues

```bash
# Increase memory limit
docker run -m 2g stardust-chatbot

# Monitor memory usage
docker stats
```

#### 4. Database Issues

```bash
# Check database file permissions
ls -la data/

# Recreate database
rm data/chatbot.db
python -c "from tools.analytics import init_analytics_db; init_analytics_db()"
```

### Debug Mode

Enable debug mode for troubleshooting:

```bash
export DEBUG=true
streamlit run app.py
```

### Logs

Check application logs:

```bash
# Docker logs
docker logs container-name

# Streamlit logs
streamlit run app.py --logger.level=debug
```

## 📞 Support

For deployment support:

- **GitHub Issues:** [Create an issue](https://github.com/your-username/chatbot/issues)
- **Documentation:** [Read the docs](https://docs.stardust.ai)
- **Community:** [Join Discord](https://discord.gg/stardust-ai)
- **Email:** support@stardust.ai

## 🎉 Success!

Once deployed, your Stardust.ai Chatbot will be available at your chosen URL with all features enabled:

- ✅ **AI Chat** with multiple models
- ✅ **Document Processing** with RAG
- ✅ **Analytics Dashboard**
- ✅ **Theme Customization**
- ✅ **Mobile Optimization**
- ✅ **Performance Monitoring**

**Happy Deploying! 🚀**
