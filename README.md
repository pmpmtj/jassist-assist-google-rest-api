# JASSIST Google Drive Integration

A Django application for downloading files from Google Drive and transcribing audio files using OpenAI's Whisper API.

## Features

- Google Drive integration for downloading files
- Audio transcription using OpenAI's Whisper API
- User-specific configurations
- RESTful API for programmatic access
- Background processing for long-running tasks
- Detailed logging and metrics collection

## Setup

### Prerequisites

- Python 3.8+
- PostgreSQL database
- Google Cloud Platform account with Drive API enabled
- OpenAI API key (for transcription features)

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/jassist-google-drive.git
   cd jassist-google-drive
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv .venv
   # On Windows
   .venv\Scripts\activate
   # On Linux/Mac
   source .venv/bin/activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Configure environment variables (create a `.env` file in the project root):
   ```
   DEBUG=True
   SECRET_KEY=your-secret-key
   DATABASE_URL=postgres://user:password@localhost:5432/jassist
   GOOGLE_CLIENT_ID=your-google-client-id
   GOOGLE_CLIENT_SECRET=your-google-client-secret
   ```

5. Run database migrations:
   ```
   python manage.py migrate auth
   python manage.py migrate sites
   python manage.py migrate
   ```

6. Create a superuser:
   ```
   python manage.py createsuperuser
   ```

7. Set up Google Authentication:
   ```
   python manage.py fix_google_auth
   ```

8. Run the development server:
   ```
   python manage.py runserver
   ```

## API Documentation

The application provides a RESTful API for programmatic access to the Google Drive download and transcription features.

### Authentication

All API endpoints require authentication. The API uses Django's session authentication.

### API Endpoints

#### Health Check

- `GET /api/v1/health/`: Verify API is operational

#### User

- `GET /api/v1/user/current/`: Get current authenticated user information

#### Google Drive

- `GET /api/v1/drive/config/`: Get user's Drive configuration
- `POST /api/v1/drive/config/update/`: Update Drive configuration
- `POST /api/v1/drive/download/`: Download a specific file from Google Drive
- `GET /api/v1/drive/download/{download_id}/status/`: Check status of a download
- `GET /api/v1/drive/history/`: Get download history

#### Transcription

- `POST /api/v1/transcription/jobs/`: Submit a transcription job
- `GET /api/v1/transcription/jobs/{job_id}/`: Check status of a transcription job
- `GET /api/v1/transcription/results/{job_id}/`: Get transcription results for a completed job

### Example API Usage

#### Download a file from Google Drive

```python
import requests

# Assuming you're already authenticated
response = requests.post(
    'http://localhost:8000/api/v1/drive/download/',
    json={'file_id': 'your-google-drive-file-id'}
)
data = response.json()

if data['status'] == 'success':
    download_id = data['data']['download_id']
    print(f"Download started with ID: {download_id}")
else:
    print(f"Error: {data['error']['message']}")
```

#### Submit a transcription job

```python
import requests

# Assuming you're already authenticated
response = requests.post(
    'http://localhost:8000/api/v1/transcription/jobs/',
    json={
        'file_id': 'your-google-drive-file-id',
        'language': 'en',
        'model': 'whisper-1'
    }
)
data = response.json()

if data['status'] == 'success':
    job_id = data['data']['id']
    print(f"Transcription job submitted with ID: {job_id}")
else:
    print(f"Error: {data['error']['message']}")
```

## Administration

The application provides a Django admin interface for managing user configurations and monitoring jobs.

1. Access the admin interface at `http://localhost:8000/admin/`
2. Log in with your superuser credentials
3. From here you can manage:
   - Global Drive configurations
   - User Drive configurations
   - Download records
   - Transcription configurations
   - Transcription jobs

## Troubleshooting

### Google Authentication Issues

If you encounter issues with Google authentication:

1. Ensure your Google Cloud project has the Drive API enabled
2. Verify that your redirect URIs are correctly configured in the Google Cloud Console
3. Check that the GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables are correctly set

### Database Connection Issues

If you have trouble connecting to the database:

1. Verify that PostgreSQL is running
2. Check that the DATABASE_URL environment variable is correctly formatted
3. Ensure the database user has the necessary permissions

## License

This project is licensed under the MIT License - see the LICENSE file for details. 