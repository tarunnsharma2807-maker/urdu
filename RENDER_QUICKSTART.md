# Render Deployment Quick Start

## Step 1: Prepare Your Repository
```bash
# Ensure everything is committed and pushed to GitHub
git status
git add .
git commit -m "Setup for Render deployment"
git push origin main
```

## Step 2: Connect to Render

1. Go to [https://render.com](https://render.com) and sign in
2. Click "New +" in the top right
3. Select "Blueprint"
4. Connect your GitHub account and authorize Render
5. Select your repository (`urdu`)
6. Click "Connect"

## Step 3: Review and Configure

Render will automatically detect the `render.yaml` file:
- **Backend Service**: Python FastAPI on `urdu-backend.onrender.com`
- **Frontend Service**: React app on `urdu-frontend.onrender.com`

## Step 4: Set Environment Variables

In the Render Dashboard, go to your services and set these variables:

### For Backend Service (`urdu-backend`):
- `MONGO_URL` → Your MongoDB connection string
- `DB_NAME` → `urdu` (or your database name)
- `EMERGENT_LLM_KEY` → Your API key

### For Frontend Service (`urdu-frontend`):
- `REACT_APP_API_URL` → `https://urdu-backend.onrender.com`

## Step 5: Deploy

1. Click "Deploy" to start the deployment
2. Monitor the build logs in the Render dashboard
3. Once successful, your services will be live!

## Accessing Your App

- **Frontend**: https://urdu-frontend.onrender.com
- **Backend API**: https://urdu-backend.onrender.com/api
- **Backend Docs**: https://urdu-backend.onrender.com/docs (FastAPI Swagger UI)

## Monitoring

- Check logs in the Render dashboard under "Logs" tab for each service
- Monitor resource usage under "Metrics"
- Set up alerts for deployment failures in Render settings

## Common Issues

| Issue | Solution |
|-------|----------|
| Build fails | Check build logs for missing dependencies |
| Frontend can't reach backend | Verify `REACT_APP_API_URL` is set to backend service URL |
| 502 Bad Gateway | Backend may still be starting, wait 2-3 minutes |
| Database connection error | Check `MONGO_URL` is correct and allows connections from Render |

## Updating Your App

1. Make changes locally
2. Commit and push to GitHub
3. Render automatically redeploys on push (if auto-deploy is enabled)

## Free Tier Limitations

- Services spin down after 15 minutes of inactivity
- Limited to 3 concurrent services on free tier
- For production, upgrade to a paid plan

## Next Steps

- Set up automatic deployments from GitHub
- Configure custom domains
- Set up database backups
- Monitor logs and performance metrics
