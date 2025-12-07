# Vercel Deployment Guide for ChainChart

This guide will help you deploy ChainChart to Vercel. Since your app has both a Next.js frontend and a FastAPI backend, we'll use a hybrid approach.

## Architecture Overview

- **Frontend**: Next.js app in `chain-chart-ui/` → Deploy directly to Vercel
- **Backend**: FastAPI → Convert to Vercel Serverless Functions OR deploy separately

## Option 1: Full Vercel Deployment (Recommended)

Deploy both frontend and backend to Vercel using serverless functions.

### Step 1: Prepare the Project Structure

1. **Move to the frontend directory**:
   ```bash
   cd chain-chart-ui
   ```

2. **Create API routes** in `chain-chart-ui/app/api/` to replace FastAPI endpoints

### Step 2: Create Vercel Configuration

Create `chain-chart-ui/vercel.json`:

```json
{
  "buildCommand": "npm run build",
  "devCommand": "npm run dev",
  "installCommand": "npm install",
  "framework": "nextjs",
  "functions": {
    "app/api/**/*.ts": {
      "runtime": "python3.9"
    }
  },
  "env": {
    "NEXT_PUBLIC_API_URL": "/api"
  }
}
```

### Step 3: Convert FastAPI Endpoints to Next.js API Routes

Since Vercel doesn't support FastAPI directly, you'll need to convert key endpoints to Next.js API routes. The main endpoints you need:

- `/api/export-contract` - Contract generation
- `/api/deploy-contract` - Contract deployment  
- `/api/contract/latest` - Get latest contract

### Step 4: Set Environment Variables in Vercel

Go to your Vercel project settings and add:

**Required:**
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_SERVICE_ROLE_KEY` - Your Supabase service role key
- `NEXT_PUBLIC_SUPABASE_URL` - Same as above (for frontend)
- `NEXT_PUBLIC_SUPABASE_ANON_KEY` - Your Supabase anon key

**Optional (for contract compilation):**
- `NEO_RPC_URL` - Neo blockchain RPC endpoint
- `NEO_PRIVATE_KEY` - Private key for deployments (keep secret!)

### Step 5: Deploy

```bash
cd chain-chart-ui
vercel
```

## Option 2: Frontend on Vercel + Backend on Separate Service (Easier)

Deploy frontend to Vercel, backend to Railway/Render/Fly.io.

### Step 1: Deploy Frontend to Vercel

1. **Navigate to frontend**:
   ```bash
   cd chain-chart-ui
   ```

2. **Update API URL** in `.env.local`:
   ```env
   NEXT_PUBLIC_API_URL=https://your-backend-url.railway.app
   ```

3. **Deploy to Vercel**:
   ```bash
   vercel
   ```

### Step 2: Deploy Backend Separately

**Option A: Railway (Recommended for Python)**
1. Create `Procfile`:
   ```
   web: uvicorn api_server:app --host 0.0.0.0 --port $PORT
   ```

2. Create `requirements.txt` (see below)

3. Push to Railway:
   ```bash
   railway init
   railway up
   ```

**Option B: Render**
1. Create `render.yaml`:
   ```yaml
   services:
     - type: web
       name: chainchart-api
       env: python
       buildCommand: pip install -r requirements.txt
       startCommand: uvicorn api_server:app --host 0.0.0.0 --port $PORT
   ```

## Required Files

### 1. `chain-chart-ui/vercel.json`

```json
{
  "buildCommand": "npm run build",
  "devCommand": "npm run dev",
  "installCommand": "npm install",
  "framework": "nextjs",
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "/api/:path*"
    }
  ]
}
```

### 2. `requirements.txt` (for backend if deploying separately)

```
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-dotenv==1.0.0
supabase==2.0.0
pydantic==2.5.0
```

### 3. `.vercelignore` (optional)

```
node_modules
.next
.env.local
generated_contracts
__pycache__
*.pyc
```

## Environment Variables Setup

### In Vercel Dashboard:

1. Go to your project → Settings → Environment Variables
2. Add these variables:

**Frontend (Public):**
- `NEXT_PUBLIC_API_URL` - Your backend API URL
- `NEXT_PUBLIC_SUPABASE_URL` - Supabase project URL
- `NEXT_PUBLIC_SUPABASE_ANON_KEY` - Supabase anon key

**Backend (if using serverless functions):**
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_SERVICE_ROLE_KEY` - Supabase service role key
- `NEO_RPC_URL` - Neo RPC endpoint (optional)
- `NEO_PRIVATE_KEY` - Private key (keep secret!)

## Important Considerations

### 1. File System Limitations
Vercel serverless functions have a read-only filesystem (except `/tmp`). Since you're now using Supabase for storage, this should be fine!

### 2. Contract Compilation
The Neo compiler (`nccs`) might not work in serverless functions. Options:
- Pre-compile contracts before deployment
- Use a separate compilation service
- Skip compilation and let users compile locally

### 3. Timeout Limits
Vercel serverless functions have timeout limits:
- Hobby: 10 seconds
- Pro: 60 seconds
- Enterprise: 900 seconds

Contract compilation might exceed these limits. Consider:
- Moving compilation to a background job
- Using a separate service for compilation

### 4. CORS Configuration
Update CORS in your backend to allow your Vercel domain:

```python
allow_origins=[
    "https://your-app.vercel.app",
    "https://*.vercel.app",  # Preview deployments
]
```

## Quick Start (Recommended: Option 2)

1. **Deploy frontend to Vercel**:
   ```bash
   cd chain-chart-ui
   vercel
   ```

2. **Deploy backend to Railway**:
   ```bash
   # Create Procfile
   echo "web: uvicorn api_server:app --host 0.0.0.0 --port \$PORT" > Procfile
   
   # Create requirements.txt (see above)
   
   # Deploy
   railway init
   railway up
   ```

3. **Update frontend API URL**:
   - In Vercel dashboard, set `NEXT_PUBLIC_API_URL` to your Railway backend URL

4. **Set environment variables** in both services

## Testing Deployment

1. Visit your Vercel deployment URL
2. Test contract generation
3. Check Supabase to verify contracts are being saved
4. Test contract deployment (if configured)

## Troubleshooting

### Issue: API calls failing
- Check `NEXT_PUBLIC_API_URL` is set correctly
- Verify CORS is configured on backend
- Check browser console for errors

### Issue: Supabase connection failing
- Verify environment variables are set
- Check Supabase project is active
- Verify RLS policies allow access

### Issue: Contract compilation failing
- Neo compiler might not be available in serverless
- Consider using a separate compilation service
- Or skip compilation and return C# code only

## Next Steps

1. Set up custom domain (optional)
2. Configure CI/CD for automatic deployments
3. Set up monitoring and error tracking
4. Optimize for production (caching, CDN, etc.)

