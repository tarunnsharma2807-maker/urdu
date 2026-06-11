# Deployment Checklist

## Pre-Deployment Setup

### Local Testing
- [ ] Backend runs locally: `cd backend && uvicorn server:app --reload`
- [ ] Frontend runs locally: `cd frontend && npm start`
- [ ] Frontend can communicate with backend API
- [ ] All tests pass: `cd tests && pytest backend_test.py`
- [ ] No sensitive data hardcoded (check .env files are in .gitignore)

### Code Preparation
- [ ] All code committed to git
- [ ] No uncommitted changes: `git status` shows clean working tree
- [ ] Code pushed to GitHub main/master branch
- [ ] `.env` files are in `.gitignore`
- [ ] `.env.example` files document required variables

### Environment Variables
- [ ] Backend `.env` file created with all required variables:
  - [ ] `MONGO_URL`
  - [ ] `DB_NAME`
  - [ ] `EMERGENT_LLM_KEY`
- [ ] Frontend `.env` file created:
  - [ ] `REACT_APP_API_URL` (local value for testing)
- [ ] All secrets are in environment variables, not in code

### Database
- [ ] MongoDB Atlas account created (or other MongoDB provider)
- [ ] Database cluster configured
- [ ] Database user created with strong password
- [ ] IP whitelist allows connection from Render (0.0.0.0/0)
- [ ] MongoDB connection string verified locally

### Render Setup
- [ ] Render.com account created
- [ ] GitHub account connected to Render
- [ ] Repository is public or Render has access (private repo)

## Deployment Steps

### Initial Deployment
- [ ] Push all changes to GitHub: `git push origin main`
- [ ] Go to [Render Dashboard](https://dashboard.render.com)
- [ ] Create new Blueprint
- [ ] Select GitHub repository
- [ ] Authorize Render to access your repos
- [ ] Review `render.yaml` configuration
- [ ] Add environment variables for backend service
- [ ] Add environment variables for frontend service
- [ ] Click "Deploy"
- [ ] Wait for both services to build and start

### Post-Deployment Verification
- [ ] Backend service is running (check Render dashboard)
- [ ] Frontend service is running (check Render dashboard)
- [ ] Access frontend URL in browser: https://urdu-frontend.onrender.com
- [ ] Frontend loads without errors
- [ ] Backend API responds: https://urdu-backend.onrender.com/docs
- [ ] Frontend can connect to backend API
- [ ] Database operations work (login, data retrieval, etc.)
- [ ] Check server logs for any errors
- [ ] Monitor resource usage (CPU, memory)

### Optional Customization
- [ ] Set up custom domain (if available)
- [ ] Configure auto-deployment on GitHub push
- [ ] Set up monitoring and alerts
- [ ] Enable auto-redeploy on git push
- [ ] Configure database backups

## Troubleshooting Checklist

If something goes wrong:

### Frontend Issues
- [ ] Check frontend build logs in Render dashboard
- [ ] Verify `REACT_APP_API_URL` is set correctly
- [ ] Check browser console for errors
- [ ] Verify CORS is configured in backend
- [ ] Check that backend URL is reachable
- [ ] Review frontend logs: `npm run build` locally to replicate

### Backend Issues
- [ ] Check backend build logs in Render dashboard
- [ ] Verify all environment variables are set
- [ ] Test MongoDB connection string locally
- [ ] Check that MongoDB allows connections from Render
- [ ] Review Python dependencies in `requirements.txt`
- [ ] Check server logs for startup errors
- [ ] Verify port 8000 is available

### Database Connection Issues
- [ ] MongoDB connection string format is correct
- [ ] Database user password doesn't contain special characters (URL encode if needed)
- [ ] IP whitelist includes Render region (or 0.0.0.0/0)
- [ ] Database exists with correct name
- [ ] Test connection string locally first

### Deployment Failures
- [ ] Check git history: `git log --oneline`
- [ ] Ensure no breaking changes in recent commits
- [ ] Verify `render.yaml` is in root directory
- [ ] Check that all required files are committed
- [ ] Review Render documentation for service-specific issues

## Ongoing Maintenance

- [ ] Monitor application logs regularly
- [ ] Check performance metrics in Render dashboard
- [ ] Set up alerting for errors/crashes
- [ ] Keep dependencies updated: `npm audit`, `pip list --outdated`
- [ ] Regular database backups (if not automated)
- [ ] Monitor costs (free tier has limitations)

## Useful Commands

```bash
# Local testing
cd backend && uvicorn server:app --reload
cd frontend && npm start

# Build locally
cd frontend && npm run build

# Test backend
cd tests && pytest backend_test.py

# View git status
git status
git log --oneline

# Access Render logs (via dashboard)
# https://dashboard.render.com → Select service → Logs
```

## Documentation Links

- [Render Documentation](https://render.com/docs)
- [Render Blueprint Spec](https://render.com/docs/blueprint-spec)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [React Deployment](https://create-react-app.dev/deployment/)
- [MongoDB Connection String](https://docs.mongodb.com/manual/reference/connection-string/)

---

**Last Updated**: June 2026
**Project**: Urdu Learning Platform
