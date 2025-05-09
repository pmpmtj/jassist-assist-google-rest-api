# JAssist Project Structure

```
jassist-assist-google-rest-api/
│
├── .venv/                       # Virtual environment
│
├── jassist/                     # Main project package
│   ├── __init__.py
│   │
│   └── web/                     # Web application
│       ├── api/                 # API endpoints
│       │   ├── common/
│       │   ├── examples/
│       │   ├── pagination/
│       │   ├── permissions/
│       │   ├── serializers/
│       │   ├── tests/
│       │   └── v1/
│       │       └── views/
│       │
│       ├── classification/      # Classification module
│       │   ├── management/
│       │   │   └── commands/
│       │   └── migrations/
│       │
│       ├── credentials/         # User credentials
│       │   └── users/
│       │
│       ├── diary_project/       # Diary module
│       │
│       ├── download_gdrive/     # Google Drive integration
│       │   ├── management/
│       │   │   └── commands/
│       │   ├── migrations/
│       │   ├── services/
│       │   │   ├── download/
│       │   │   └── transcription/
│       │   ├── templates/
│       │   ├── tests/
│       │   └── utils/
│       │
│       ├── jassist_app/         # Main app
│       │   ├── management/
│       │   │   └── commands/
│       │   ├── migrations/
│       │   ├── services/
│       │   └── templates/
│       │
│       ├── logs/                # Log files
│       │   └── transcription_metrics/
│       │
│       ├── manual_entries/      # Manual entries module
│       │   ├── migrations/      # Database migrations
│       │   ├── templates/       # UI templates
│       │   │   └── manual_entries/
│       │   │       ├── create_entry.html
│       │   │       ├── edit_entry.html
│       │   │       └── list_entries.html
│       │   ├── admin.py         # Admin interface
│       │   ├── apps.py          # App configuration
│       │   ├── forms.py         # Form definitions
│       │   ├── models.py        # Data models
│       │   ├── urls.py          # URL routing
│       │   └── views.py         # View controllers
│       │
│       ├── media/               # User uploaded content
│       │   ├── downloads/
│       │   │   └── drive/
│       │   └── transcriptions/
│       │
│       ├── static/              # Static files
│       │
│       ├── staticfiles/         # Collected static files
│       │   ├── account/
│       │   └── admin/
│       │
│       ├── utils/               # Utility modules
│       │
│       ├── favicon.ico          # Favicon for the web application
│       ├── manage.py            # Django management script
│       ├── run_tests.py         # Test runner
│       └── tests_readme.md      # Testing documentation
│
├── .gitignore                   # Git ignore file
├── api_layer_development_plan.md # API development documentation
├── database_migration_steps.txt # Database migration guide
├── README.md                    # Project documentation
└── requirements.txt             # Python dependencies
```

## Key Components

- **API Layer**: RESTful API endpoints with versioning
- **Classification Module**: For data classification tasks
- **Download GDrive**: Integration with Google Drive for downloading and processing files
- **Manual Entries**: Module for user-created text entries with classification
- **Transcription**: Services for audio/video transcription
- **User Management**: Credential handling and user authentication
- **Utilities**: Common utility functions used across the application 