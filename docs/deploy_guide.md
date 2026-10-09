# Deployment Guide (Render / Railway / Fly.io)

This guide details public deployment options for deploying the Personal Finance Agent web app with HTTPS.

## Option A: Render (Free Tier)

### 1. Database Setup (Render PostgreSQL)
1. Create a **New PostgreSQL** database instance on Render.
2. Note the Internal Database URL: `postgresql://user:pass@host:5432/dbname`.

### 2. Backend Web Service Deployment
1. Create a **New Web Service** pointing to the `./backend` folder.
2. Build Command: `pip install -r requirements.txt`
3. Start Command: `uvicorn app.main:app --host 0.0.0.0 --port 10000`
4. Set Environment Variables:
   - `DATABASE_URL`: Your Render Postgres URL
   - `SECRET_KEY`: A secure 32-character random string
   - `ENCRYPTION_KEY`: A valid Fernet base64 key
   - `GEMINI_API_KEY`: (Optional) Your Google Gemini API Key

### 3. Frontend Web Service Deployment
1. Create a **New Web Service** pointing to the `./frontend` folder.
2. Build Command: `pip install -r requirements.txt`
3. Start Command: `streamlit run app.py --server.port 10000 --server.address 0.0.0.0`
4. Set Environment Variable:
   - `BACKEND_API_URL`: `https://your-backend-api.onrender.com/api/v1`

---

## Option B: Docker Compose Self-Hosted (VPS / EC2)

```bash
# Clone project repository
git clone https://github.com/your-org/personal-finance-agent.git
cd personal-finance-agent

# Set up environment variables
cp .env.example .env

# Build and launch all services with HTTPS via Nginx
docker-compose up --build -d
```
