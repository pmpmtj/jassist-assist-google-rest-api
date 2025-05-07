# JASSIST API

This API provides RESTful endpoints for the Google Drive download and transcription services.

## Features

- Standardized response formatting
- Robust error handling
- Authentication and permission controls
- Request validation
- Pagination for list endpoints
- Versioning support (v1)

## API Endpoints

### Health Check

- `GET /api/v1/health/`: Verify API is operational

### User

- `GET /api/v1/user/current/`: Get current authenticated user information

### Google Drive

- `GET /api/v1/drive/config/`: Get user's Drive configuration
- `POST /api/v1/drive/config/update/`: Update Drive configuration

### Transcription

- `POST /api/v1/transcription/jobs/`: Submit a transcription job
- `GET /api/v1/transcription/jobs/{job_id}/`: Check status of a transcription job
- `GET /api/v1/transcription/results/{job_id}/`: Get transcription results for a completed job

## Authentication

The API uses Django's session authentication. Clients must be authenticated to access protected endpoints.

## Response Format

All API responses follow this structure:

```json
{
  "status": "success",
  "data": {
    // Response payload
  },
  "error": null
}
```

For errors:

```json
{
  "status": "error",
  "data": null,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message",
    "details": {
      // Additional error context
    }
  }
}
```

## Models

### Drive Configuration

The Drive configuration endpoints interact with these models:
- `GlobalDriveConfig`: System-wide settings for file types and behavior
- `UserDriveConfig`: User-specific settings for target folders and scheduling

### Transcription Jobs

Transcription endpoints work with the `TranscriptionJob` model, which tracks:
- Job status (pending, processing, completed, failed)
- File information
- Configuration settings
- Results metadata

## Development

To extend the API:

1. Add new serializers in `api/serializers/`
2. Add new views in `api/v1/views/`
3. Register URL routes in `api/v1/urls.py` 
4. Update models as needed in `download_gdrive/models.py`
5. Create migrations with `python manage.py makemigrations` 