# JAssist App - Core Authentication & User Interface

## Overview
The JAssist app serves as the core authentication and user interface layer for the entire JAssist multi-user application. It implements secure Google OAuth authentication, enforces authentication policies, and provides the foundational UI templates and navigation structure used throughout the application.

## Key Features
- Single Sign-On using Google OAuth 2.0
- Secure credential storage for each user
- Enforced Google-only authentication policy
- Responsive Bootstrap-based UI template system
- Streamlined user flows from login to logout

## UI/UX Design

### Template Structure
The app follows a hierarchical template structure:
- **base.html**: Master template with common UI elements
  - Navigation bar (responsive)
  - Footer
  - CSS & JavaScript includes
  - Bootstrap 5 framework integration
  - FontAwesome and Bootstrap Icons integration
- **login.html**: Branded Google authentication page
- **success.html**: Post-login landing page

### UI Components
- **Navigation Bar**: Responsive top navigation with conditional rendering based on authentication status
- **Bootstrap Cards**: Content is presented in clean card-based layouts
- **Icons**: FontAwesome and Bootstrap Icons provide visual cues
- **Responsive Design**: Mobile-friendly layout that adapts to different screen sizes

### Color Scheme & Design Language
- Primary color: Bootstrap primary blue for brand elements
- Clean, minimalist design with appropriate whitespace
- Consistent typography and spacing
- Clear visual hierarchy

## User Authentication Flow

### Login Process
1. User visits the root URL (`/`)
2. If not authenticated:
   - User is presented with the login page
   - "Sign in with Google" button is prominently displayed
3. If authenticated:
   - User is automatically redirected to the success page

### Authentication Implementation
- **Google OAuth**: Implemented using django-allauth
- **Forced Google Auth**: Custom adapters prevent non-Google authentication
- **Token Management**: OAuth tokens are securely stored for each user
- **Scope Control**: Appropriate scopes are requested from Google

### Authentication Security
- **Token Storage**: Credentials stored in user-specific JSON files
- **Adapter-Level Restrictions**: Prevents direct signup without Google
- **Provider Validation**: Blocks non-Google authentication attempts 

## URL Structure
- `/`: Main login page
- `/success/`: Post-login landing page
- `/accounts/google/login/`: Google OAuth entry point (provided by allauth)
- `/accounts/logout/`: Logout URL

## Integration with Other Apps

### Integration Points
- **Base Templates**: Other apps extend base.html for consistent UI
- **Navigation Bar**: Provides links to other app components (like Google Drive)
- **Authentication Layer**: Provides authentication for all other components

### Access Control
- Protected views use Django's `@login_required` decorator
- Template conditionals display different content based on authentication status
- URLs defined in main project settings route through appropriate apps

## Configuration System

### Authentication Settings
Key settings in the project's configuration:
- Custom authentication adapters:
  - `NoSignupAccountAdapter`: Prevents direct signup
  - `GoogleOnlySocialAccountAdapter`: Restricts to Google auth only
- Google OAuth scopes:
  - profile
  - email
  - Google Drive access
  - Google Calendar access
  - Gmail send capability

### Credential Management
- User credentials stored in `credentials/users/{user_id}.json`
- Token refresh handled automatically
- Scopes are stored with tokens

## Development and Customization

### Template Customization
All templates can be customized by:
- Overriding blocks in the base template
- Modifying CSS styles
- Adding JavaScript functionality

### Adding New Features
To extend the UI:
1. Create new templates that extend base.html
2. Add new views in views.py
3. Register new URL patterns in urls.py

### Navigation Expansion
To add new navigation elements:
1. Modify the navigation section in base.html
2. Add new links, ensuring proper authentication checks

## Technical Requirements
- Django web framework
- django-allauth for OAuth support
- Bootstrap 5 for responsive UI
- PostgreSQL database
- django-crispy-forms with bootstrap5 pack

## Security Considerations
- Authentication is enforced at multiple levels
- Google scopes are carefully selected for minimum necessary access
- Token storage follows security best practices
- All authentication routes are properly protected

## User Experience Flow

1. **Initial Access**
   - User navigates to the application
   - Presented with clean login page with Google button

2. **Authentication**
   - User clicks Google sign-in
   - Redirected to Google for authentication
   - Grants permission for required scopes
   - Redirected back to application

3. **Post-Login**
   - User lands on success page
   - Navigation bar shows available app sections
   - User can navigate to other parts of the application

4. **Using the Application**
   - Consistent UI experience across different components
   - Shared navigation and styling
   - Clear path back to main dashboard

5. **Logout**
   - User clicks logout in navigation bar
   - Session terminated
   - Redirected to login page 