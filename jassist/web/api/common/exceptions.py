"""
Custom exceptions and exception handling for the API layer.
"""
from rest_framework.views import exception_handler
from rest_framework import status

from .responses import error_response


# Custom API exceptions
class APIException(Exception):
    """Base exception for API-related errors."""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_message = "An unexpected error occurred."
    error_code = "API_ERROR"
    
    def __init__(self, message=None, details=None):
        self.message = message or self.default_message
        self.details = details
        super().__init__(self.message)


class ResourceNotFoundError(APIException):
    """Exception raised when a requested resource is not found."""
    status_code = status.HTTP_404_NOT_FOUND
    default_message = "The requested resource was not found."
    error_code = "RESOURCE_NOT_FOUND"


class ValidationError(APIException):
    """Exception raised for validation errors."""
    status_code = status.HTTP_400_BAD_REQUEST
    default_message = "Invalid input data."
    error_code = "VALIDATION_ERROR"


class AuthenticationError(APIException):
    """Exception raised for authentication failures."""
    status_code = status.HTTP_401_UNAUTHORIZED
    default_message = "Authentication failed."
    error_code = "AUTHENTICATION_ERROR"


class PermissionDeniedError(APIException):
    """Exception raised when a user lacks permission to perform an action."""
    status_code = status.HTTP_403_FORBIDDEN
    default_message = "You do not have permission to perform this action."
    error_code = "PERMISSION_DENIED"


class ServiceUnavailableError(APIException):
    """Exception raised when an external service is unavailable."""
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_message = "The service is currently unavailable."
    error_code = "SERVICE_UNAVAILABLE"


def custom_exception_handler(exc, context):
    """
    Custom exception handler for API views.
    
    Args:
        exc: The raised exception
        context: The exception context
        
    Returns:
        Response: A formatted error response
    """
    # First, handle DRF's built-in exceptions
    response = exception_handler(exc, context)
    
    # If it's a DRF exception (response is not None)
    if response is not None:
        # Extract the error data and format with our standard
        error_data = response.data
        error_message = str(error_data.get('detail', 'An error occurred'))
        
        # Map common DRF exception codes to our error codes
        status_code = response.status_code
        error_code = "API_ERROR"
        
        if status_code == 404:
            error_code = "RESOURCE_NOT_FOUND"
        elif status_code == 400:
            error_code = "VALIDATION_ERROR"
        elif status_code == 401:
            error_code = "AUTHENTICATION_ERROR"
        elif status_code == 403:
            error_code = "PERMISSION_DENIED"
        elif status_code >= 500:
            error_code = "SERVER_ERROR"
            
        return error_response(
            message=error_message,
            error_code=error_code,
            status_code=status_code,
            details=error_data if isinstance(error_data, dict) else None
        )
    
    # Handle our custom API exceptions
    if isinstance(exc, APIException):
        return error_response(
            message=exc.message,
            error_code=exc.error_code,
            status_code=exc.status_code,
            details=exc.details
        )
        
    # For unhandled exceptions, return a generic server error
    return error_response(
        message="An unexpected server error occurred.",
        error_code="SERVER_ERROR",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        details={"exception": str(exc)} if str(exc) else None
    ) 