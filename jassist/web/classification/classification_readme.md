# Classification Module

## Overview

The Classification module leverages OpenAI's Assistant API to automatically categorize transcription content into predefined categories. It provides an efficient way to organize and manage transcribed text by identifying its content type (diary entries, calendar events, meeting notes, etc.).

## Features

- **OpenAI Assistant Integration**: Uses OpenAI's powerful AI models for accurate content classification
- **Batch Processing**: Efficiently process multiple transcriptions in managed batches
- **Cost Tracking**: Monitors API usage and associated costs
- **Dry Run Mode**: Test classification without making actual database changes
- **Persistent Configuration**: Stores configurations and prompts in the database for easy management

## System Architecture

The classification system consists of the following components:

- **Models**:
  - `ClassificationConfig`: Configuration for OpenAI Assistant (model, parameters, IDs)
  - `ClassificationPrompt`: Prompt templates for different classification tasks
  - `ClassificationMetrics`: Usage metrics and cost tracking
  - `TranscriptionClassificationBatch`: Batch processing management

- **Core Components**:
  - `ClassificationAdapter`: Interface to OpenAI Assistant API
  - `ClassificationProcessor`: Main processing logic

## Configuration

The system uses database-stored configuration instead of file-based settings:

- **Assistant Configuration**: Model parameters, API keys, and response settings
- **Prompt Templates**: Customizable prompts that guide the AI in classification tasks

### Migration from Files to Database

If you have existing configuration files, use the migration command to transfer settings to the database:

```bash
python manage.py migrate_classification_config
```

Options:
- `--config-only`: Only migrate configuration, not prompts
- `--prompts-only`: Only migrate prompts, not configuration
- `--keep-files`: Keep original configuration files after migration

## Command Line Usage

### Process Transcription Classification

Process transcriptions through the classification system:

```bash
python manage.py process_transcription_classification
```

This command processes unlabeled transcriptions by default.

#### Command Options:

- `--job-id=ID`: Process only a specific transcription job
- `--job-ids ID1 ID2...`: Process specific job IDs
- `--force`: Process all completed jobs, even if already labeled
- `--dry-run`: Run without updating the database (testing)
- `--limit=N`: Maximum number of records to process
- `--batch-size=N`: Number of records to process in each batch (default: 20)

### Examples:

```bash
# Process all unlabeled transcriptions
python manage.py process_transcription_classification

# Process only a specific job
python manage.py process_transcription_classification --job-id=123

# Dry run with limited number of records
python manage.py process_transcription_classification --dry-run --limit=10

# Process specific jobs in force mode
python manage.py process_transcription_classification --job-ids 123 456 789 --force
```

## Cost Awareness

The classification system includes several features to help manage and monitor API costs:

### Cost Tracking

- Each classification request records token usage and estimated cost
- Metrics are stored in the `ClassificationMetrics` model
- Batch processing tracks aggregate costs

### Cost Management Strategies

1. **Dry Run Mode**: Test classification without making API calls that incur costs
   ```bash
   python manage.py process_transcription_classification --dry-run
   ```

2. **Batch Size Optimization**: Adjust batch size to optimize API usage
   ```bash
   python manage.py process_transcription_classification --batch-size=20
   ```

3. **Selective Processing**: Process only specific jobs instead of all at once
   ```bash
   python manage.py process_transcription_classification --job-ids 123 456
   ```

4. **Limiting Records**: Set a maximum number of records to process
   ```bash
   python manage.py process_transcription_classification --limit=50
   ```

### Viewing Cost Metrics

Cost metrics are available through the Django admin interface under the "Classification Metrics" section.

## Troubleshooting

### Common Issues

1. **API Key Issues**: Ensure your OpenAI API key is correctly set in the configuration
2. **Processing Failures**: Check the logs for specific error messages
3. **Rate Limiting**: The system includes automatic retries for rate limiting errors

### Logging

The classification system logs detailed information to:
- Console output
- `logs/classification.log`

Adjust log levels in Django settings if needed.

## Technical References

- API Documentation: See the Django REST framework API documentation
- OpenAI Assistant API: [OpenAI Documentation](https://platform.openai.com/docs)
