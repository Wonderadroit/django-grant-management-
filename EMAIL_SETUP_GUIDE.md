# Email Setup Guide for David Johnson Foundation Grant System

## 🚀 Quick Start - Choose Your Option

### Option 1: Gmail SMTP (Easiest for Testing)
1. **Update your .env file** with your Gmail credentials:
   ```
   EMAIL_HOST_USER=your-email@gmail.com
   EMAIL_HOST_PASSWORD=your-app-password
   ```

2. **Create Gmail App Password** (Required):
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate password for "Mail"
   - Use this password (not your regular Gmail password)

### Option 2: SendGrid (Recommended for Production)
1. **Sign up for SendGrid** (free tier: 100 emails/day)
2. **Get API Key** from SendGrid dashboard
3. **Update .env file**:
   ```
   EMAIL_HOST=smtp.sendgrid.net
   EMAIL_HOST_USER=apikey
   EMAIL_HOST_PASSWORD=your-sendgrid-api-key
   ```

## 📧 Email Templates Created

Your system now has professional HTML email templates for:
- ✅ **Welcome Email** - New user registration
- ✅ **Approval Email** - Grant approved with celebration
- ✅ **Status Update** - Application progress updates  
- ✅ **Rejection Email** - Respectful decline with encouragement

## 🧪 Testing Your Email Setup

Run this command to test your email system:

```bash
# Test welcome email
python manage.py test_email --email your-email@gmail.com --type welcome

# Test all email types
python manage.py test_email --email your-email@gmail.com --type all
```

## 🔧 Current Configuration

Your Django settings are already configured to use:
- Environment variables for email credentials
- HTML email templates with fallback to plain text
- Professional "From" address: David Johnson Foundation <grants@davidjohnsonfoundation.org>

## 🎯 Integration Points

The email system automatically triggers when:
- New user registers (welcome email)
- Admin approves/rejects applications (approval/rejection emails)
- Application status changes (status update emails)

## 🌟 Professional Features

✅ **Responsive Design** - Emails look great on mobile and desktop
✅ **Brand Consistent** - Uses your foundation's colors and styling
✅ **Clear CTAs** - Dashboard and action buttons included
✅ **Fallback Text** - Plain text versions for all emails
✅ **Error Handling** - Graceful failure with logging

## 📱 Next Steps

1. **Set up your email credentials** in the .env file
2. **Test the system** with the test command
3. **Customize templates** if needed (optional)
4. **Consider SMS integration** for critical updates (Twilio)
5. **Set up email analytics** (SendGrid provides great stats)

## 🔒 Security Notes

- Never commit email credentials to git
- Use App Passwords for Gmail (not your main password)
- Consider dedicated email domain for production
- Monitor email delivery rates and spam scores

## 💡 Pro Tips

- **Gmail limits**: 500 emails/day max
- **SendGrid**: Better deliverability and analytics
- **Custom domain**: More professional (grants@yourdomain.org)
- **Email scheduling**: Consider automated reminders for deadlines

Your email system is now ready! 🎉