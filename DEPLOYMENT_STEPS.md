# Deployment Steps for Dave Johnson Foundation Grant Portal

## Current Status
- Service name updated to: `davejohnsongrant`
- Expected URL: `https://davejohnsongrant.onrender.com`
- All files committed and pushed to GitHub

## Steps to Deploy

### Option 1: New Blueprint Deployment (Recommended)
1. **Go to Render Dashboard**: https://dashboard.render.com
2. **Create New Service**:
   - Click "New +" button
   - Select "Blueprint"
3. **Connect Repository**:
   - Connect your GitHub account if not already connected
   - Select repository: `django-grant-management-`
   - Branch: `master`
4. **Deploy**:
   - Render will read the `render.yaml` file
   - It will create both database and web service automatically
   - Service name will be `davejohnsongrant`

### Option 2: Update Existing Service
If you already have a service running:
1. Go to your existing service dashboard
2. Click on "Settings"
3. Update service name from `django-grant-app` to `davejohnsongrant`
4. Save changes

## Expected Results
- **New URL**: `https://davejohnsongrant.onrender.com`
- **Admin Panel**: `https://davejohnsongrant.onrender.com/djf-admin-portal/`
- **User Registration**: `https://davejohnsongrant.onrender.com/accounts/signup/`

## Environment Variables (Automatically Set)
- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: Auto-generated Django secret key
- `DEBUG`: false
- `ALLOWED_HOSTS`: "*"
- `DEFAULT_FROM_EMAIL`: "Dave Johnson Foundation <grantdavejohnsonfoundation@gmail.com>"

## After Deployment
1. **Test the application**: Visit the new URL
2. **Access admin panel**: Go to `/djf-admin-portal/`
3. **Change admin password**: Login with admin/admin123 and change password immediately
4. **Test grant application**: Create a test application to verify functionality

## Troubleshooting
- If build fails, check the build logs in Render dashboard
- If database connection fails, verify the DATABASE_URL environment variable
- If static files don't load, check WhiteNoise configuration

## Notes
- The old `django-grant-app` service can be deleted after confirming the new one works
- Free tier services may take 30-60 seconds to spin up when idle
- Database is persistent and will retain data between deployments