## Official Email Address Update - David Johnson Foundation

**Date**: October 6, 2025
**Update**: Changed official foundation email address

### Previous Email Addresses
- `grants@davejohnsonfoundation.org` 
- `support@davidjohnsonfoundation.org`
- `noreply@davidjohnsonfoundation.org`

### New Official Email Address
**`grantdavejohnsonfoundation@gmail.com`**

### Files Updated
The following files were updated to reflect the new official email address:

#### Configuration Files
- `core/settings.py` - DEFAULT_FROM_EMAIL setting
- `.env` - DEFAULT_FROM_EMAIL configuration
- `core/settings_production.py` - Production email settings

#### Templates - User Interface
- `core/templates/includes/sidenav.html` - Contact support link
- `grants/templates/grants/status.html` - Support contact information
- `core/templates/landing.html` - Main landing page contact info
- `grants/templates/grants/already_applied.html` - Contact information
- `grants/templates/grants/dashboard.html` - Support links
- `grants/templates/grants/approval.html` - Email contact links
- `grants/templates/grants/eligibility.html` - Contact email
- `grants/templates/grants/wait.html` - Contact information
- `core/templates/landing_clean.html` - Contact information
- `core/templates/accounts/password_change.html` - Support email

#### Email Templates
- `core/templates/email/base_email.html` - Email footer
- `core/templates/email/approval_email.html` - Approval notifications
- `core/templates/email/rejection_email.html` - Rejection notifications
- `templates/emails/submission.html` - Submission confirmations
- `templates/emails/approval.html` - Approval notifications

#### Management Commands
- `grants/management/commands/auto_approve.py` - Contact information

### Impact
- All automated emails will now be sent from `grantdavejohnsonfoundation@gmail.com`
- All contact links throughout the application now point to the new email
- Users will see the new email address in all communications
- Support and contact information updated consistently across the platform

### Next Steps for Admin
1. Ensure the new Gmail account is set up and accessible
2. Update email hosting/SMTP configuration if needed
3. Test email sending functionality
4. Update any external documentation or marketing materials
5. Inform team members of the new official email address

### Email Configuration
The system is configured to use the email address specified in the `DEFAULT_FROM_EMAIL` environment variable, which is now set to:
```
DEFAULT_FROM_EMAIL=Dave Johnson Foundation <grantdavejohnsonfoundation@gmail.com>
```

This ensures all system-generated emails will use the new official address with proper branding.