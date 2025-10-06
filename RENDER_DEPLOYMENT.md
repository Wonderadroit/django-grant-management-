# Deploying Django Grant Management System to Render

This guide will walk you through deploying your Django grant management application to Render.

## Prerequisites

1. A [Render account](https://render.com) (free tier available)
2. Your Django project pushed to a Git repository (GitHub, GitLab, or Bitbucket)
3. All the configuration files created in this project

## Files Added for Deployment

The following files have been created/modified for Render deployment:

- `requirements.txt` - Updated with production dependencies
- `build.sh` - Build script for Render deployment
- `render.yaml` - Service configuration for automatic deployment
- `core/settings.py` - Updated for production environment

## Step-by-Step Deployment Guide

### 1. Prepare Your Repository

Make sure all files are committed to your Git repository:

```bash
git add .
git commit -m "Add Render deployment configuration"
git push origin main
```

### 2. Create a Render Account

1. Go to [render.com](https://render.com)
2. Sign up for a free account
3. Connect your GitHub, GitLab, or Bitbucket account

### 3. Deploy Using render.yaml (Recommended)

1. In your Render dashboard, click "New" → "Blueprint"
2. Connect your repository
3. Render will automatically detect the `render.yaml` file
4. Click "Apply" to create the services

### 4. Alternative: Manual Deployment

If you prefer manual setup:

#### Create Database Service
1. Click "New" → "PostgreSQL"
2. Name: `django-grant-db`
3. Database Name: `django_grant_db`
4. User: `django_grant_user`
5. Plan: Free
6. Click "Create Database"

#### Create Web Service
1. Click "New" → "Web Service"
2. Connect your repository
3. Configure the service:
   - **Name**: `django-grant-app`
   - **Runtime**: `Python 3`
   - **Build Command**: `./build.sh`
   - **Start Command**: `gunicorn core.wsgi:application`
   - **Plan**: Free

### 5. Configure Environment Variables

Add these environment variables in your web service settings:

#### Required Variables:
```
DATABASE_URL=<automatically set by Render when you connect the database>
SECRET_KEY=<generate a strong secret key>
DEBUG=false
ALLOWED_HOSTS=*
WEB_CONCURRENCY=4
```

#### Email Configuration (Optional):
```
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=true
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=Dave Johnson Foundation <grantdavejohnsonfoundation@gmail.com>
```

### 6. Connect Database to Web Service

1. In your web service settings, go to "Environment"
2. Add a new environment variable:
   - **Key**: `DATABASE_URL`
   - **Value**: Select "From Database" → choose your PostgreSQL database

### 7. Deploy

1. Click "Create Web Service" or "Deploy"
2. Render will build and deploy your application
3. The build process will:
   - Install dependencies from `requirements.txt`
   - Run database migrations
   - Collect static files
   - Create a superuser account (admin/admin123)

## Post-Deployment Setup

### 1. Access Your Application

Once deployment is complete, you'll get a URL like:
`https://your-app-name.onrender.com`

### 2. Update CSRF Settings

Add your Render URL to the environment variables:
```
RENDER_EXTERNAL_URL=https://your-app-name.onrender.com
```

### 3. Create Admin Account (if needed)

The build script automatically creates an admin user:
- **Username**: admin
- **Password**: admin123
- **Email**: admin@example.com

**⚠️ Important**: Change this password immediately after deployment!

### 4. Configure Domain (Optional)

1. In Render dashboard, go to your web service
2. Click "Settings" → "Custom Domains"
3. Add your custom domain if you have one

## Environment Variables Reference

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Yes | Auto-generated |
| `SECRET_KEY` | Django secret key | Yes | - |
| `DEBUG` | Debug mode | No | false |
| `ALLOWED_HOSTS` | Allowed hosts | No | * |
| `WEB_CONCURRENCY` | Gunicorn workers | No | 4 |
| `EMAIL_BACKEND` | Email backend | No | console |
| `EMAIL_HOST` | SMTP host | No | - |
| `EMAIL_PORT` | SMTP port | No | 587 |
| `EMAIL_USE_TLS` | Use TLS | No | true |
| `EMAIL_HOST_USER` | SMTP username | No | - |
| `EMAIL_HOST_PASSWORD` | SMTP password | No | - |
| `DEFAULT_FROM_EMAIL` | Default from email | No | Set in code |

## Monitoring and Maintenance

### 1. View Logs

- In Render dashboard, go to your web service
- Click "Logs" to view application logs
- Use logs to debug any issues

### 2. Redeploy

- Push changes to your Git repository
- Render will automatically redeploy
- Or manually trigger deployment in dashboard

### 3. Database Backups

- Render automatically backs up your PostgreSQL database
- You can create manual backups in the database dashboard

## Troubleshooting

### Common Issues:

1. **Build Failures**
   - Check logs in Render dashboard
   - Ensure all dependencies are in `requirements.txt`
   - Verify `build.sh` has execute permissions

2. **Static Files Not Loading**
   - Ensure WhiteNoise is properly configured
   - Check `STATIC_ROOT` and `STATICFILES_DIRS` settings

3. **Database Connection Issues**
   - Verify `DATABASE_URL` is set correctly
   - Ensure database service is running

4. **CSRF Errors**
   - Add your Render URL to `CSRF_TRUSTED_ORIGINS`
   - Set `RENDER_EXTERNAL_URL` environment variable

### Support

For issues specific to this Django application:
1. Check the application logs in Render
2. Ensure all environment variables are set correctly
3. Verify database migrations have run successfully

For Render platform issues:
- Visit [Render's documentation](https://render.com/docs)
- Contact Render support

## Security Notes

1. **Change default admin password** immediately after deployment
2. **Use strong SECRET_KEY** - never commit it to version control
3. **Configure proper email settings** for production notifications
4. **Set up proper logging** for production monitoring
5. **Enable HTTPS** (Render provides this automatically)

## Cost Considerations

- **Free Tier**: Includes 750 hours/month, sleeps after 15 minutes of inactivity
- **Paid Plans**: Starting at $7/month for always-on services
- **Database**: Free PostgreSQL has 1GB storage limit

Your Django grant management system is now ready for production use on Render!