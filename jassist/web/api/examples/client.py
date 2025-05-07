"""
Example API client demonstrating how to use the API.

This script demonstrates how to authenticate and make requests to the API.
"""
import requests
import json
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API base URL
API_BASE = 'http://localhost:8000/api/v1'

# Session with cookie persistence
session = requests.Session()


def login(username, password):
    """Authenticate with the API using Django's login endpoint."""
    login_url = 'http://localhost:8000/accounts/login/'
    
    # First, get the CSRF token
    response = session.get(login_url)
    if response.status_code != 200:
        logger.error(f"Failed to get login page: {response.status_code}")
        return False
        
    # Extract CSRF token from the cookies
    csrftoken = session.cookies.get('csrftoken')
    if not csrftoken:
        logger.error("CSRF token not found in cookies")
        return False
        
    # Perform login with CSRF token
    login_data = {
        'login': username,
        'password': password,
        'csrfmiddlewaretoken': csrftoken,
    }
    
    headers = {
        'Referer': login_url,
        'X-CSRFToken': csrftoken,
    }
    
    response = session.post(login_url, data=login_data, headers=headers, allow_redirects=True)
    
    if response.url.endswith('login/'):
        logger.error("Login failed")
        return False
        
    logger.info(f"Login successful, redirected to: {response.url}")
    return True


def get_current_user():
    """Get the currently authenticated user's details."""
    url = f"{API_BASE}/user/current/"
    
    response = session.get(url)
    if response.status_code != 200:
        logger.error(f"Failed to get current user: {response.status_code}")
        return None
        
    return response.json()


def get_drive_config():
    """Get the user's Drive configuration."""
    url = f"{API_BASE}/drive/config/"
    
    response = session.get(url)
    if response.status_code != 200:
        logger.error(f"Failed to get drive config: {response.status_code}")
        return None
        
    return response.json()


def update_drive_config(config):
    """Update the user's Drive configuration."""
    url = f"{API_BASE}/drive/config/update/"
    
    headers = {
        'Content-Type': 'application/json',
        'X-CSRFToken': session.cookies.get('csrftoken'),
    }
    
    response = session.post(url, json=config, headers=headers)
    if response.status_code != 200:
        logger.error(f"Failed to update drive config: {response.status_code}")
        return None
        
    return response.json()


def submit_transcription_job(file_id, language='en-US'):
    """Submit a new transcription job."""
    url = f"{API_BASE}/transcription/jobs/"
    
    headers = {
        'Content-Type': 'application/json',
        'X-CSRFToken': session.cookies.get('csrftoken'),
    }
    
    job_data = {
        'file_id': file_id,
        'language': language,
    }
    
    response = session.post(url, json=job_data, headers=headers)
    if response.status_code != 200:
        logger.error(f"Failed to submit transcription job: {response.status_code}")
        return None
        
    return response.json()


def check_job_status(job_id):
    """Check the status of a transcription job."""
    url = f"{API_BASE}/transcription/jobs/{job_id}/"
    
    response = session.get(url)
    if response.status_code != 200:
        logger.error(f"Failed to get job status: {response.status_code}")
        return None
        
    return response.json()


def pretty_print(data):
    """Pretty print JSON data."""
    print(json.dumps(data, indent=2))


def main():
    """Main function demonstrating API usage."""
    # Replace with your credentials
    username = 'yourusername'
    password = 'yourpassword'
    
    # Login
    if not login(username, password):
        return
        
    # Get current user
    user_data = get_current_user()
    if user_data:
        print("\n=== Current User ===")
        pretty_print(user_data)
        
    # Get Drive configuration
    drive_config = get_drive_config()
    if drive_config:
        print("\n=== Drive Configuration ===")
        pretty_print(drive_config)
        
    # Update Drive configuration
    updated_config = {
        'allowed_file_types': ['audio', 'video', 'document', 'image'],
        'max_file_size_mb': 150,
        'auto_download': False,
    }
    
    result = update_drive_config(updated_config)
    if result:
        print("\n=== Updated Drive Configuration ===")
        pretty_print(result)
        
    # Submit a transcription job
    job_result = submit_transcription_job('sample_file_id_123')
    if job_result:
        print("\n=== Transcription Job Submitted ===")
        pretty_print(job_result)
        
        # Get the job ID from the response
        job_id = job_result.get('data', {}).get('job_id')
        if job_id:
            # Check job status
            status_result = check_job_status(job_id)
            if status_result:
                print("\n=== Job Status ===")
                pretty_print(status_result)


if __name__ == "__main__":
    main() 