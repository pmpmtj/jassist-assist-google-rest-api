"""
Standard API response formatting utilities.
Provides consistent response structure across all API endpoints.
"""
from rest_framework.response import Response
from rest_framework import status


class APIResponse(Response):
    """
    Custom API response class providing standardized response format.
    All API responses will follow this structure:
    {
        "status": "success" | "error",
        "data": { ... } | null,
        "error": {
            "code": "ERROR_CODE",
            "message": "Human readable message",
            "details": { ... } | null
        } | null
    }
    """
    def __init__(self, data=None, message=None, status=None, error_code=None, 
                 error_details=None, headers=None):
        """
        Initialize API response with standard format.
        
        Args:
            data: The response payload (for success responses)
            message: Optional message string
            status: HTTP status code
            error_code: String code for error responses
            error_details: Additional error context (for error responses)
            headers: Optional HTTP headers
        """
        response_status = "success"
        response_data = {
            "status": response_status,
            "data": data,
            "error": None
        }

        # Handle error responses
        if status is not None and status >= 400:
            response_status = "error"
            response_data["status"] = response_status
            response_data["data"] = None
            response_data["error"] = {
                "code": error_code or "UNKNOWN_ERROR",
                "message": message or "An unexpected error occurred",
                "details": error_details
            }
        elif message:
            # For success responses with messages, include in data
            if response_data["data"] is None:
                response_data["data"] = {"message": message}
            elif isinstance(response_data["data"], dict):
                response_data["data"]["message"] = message

        super().__init__(data=response_data, status=status, headers=headers)


def success_response(data=None, message=None, status_code=status.HTTP_200_OK, headers=None):
    """
    Create a standardized success response.
    
    Args:
        data: The response payload
        message: Optional success message
        status_code: HTTP status code (default: 200)
        headers: Optional HTTP headers
        
    Returns:
        APIResponse: A standardized success response
    """
    return APIResponse(data=data, message=message, status=status_code, headers=headers)


def error_response(message, error_code, status_code=status.HTTP_400_BAD_REQUEST, 
                   details=None, headers=None):
    """
    Create a standardized error response.
    
    Args:
        message: Human-readable error message
        error_code: Machine-readable error code string
        status_code: HTTP status code (default: 400)
        details: Additional error context
        headers: Optional HTTP headers
        
    Returns:
        APIResponse: A standardized error response
    """
    return APIResponse(
        message=message,
        status=status_code,
        error_code=error_code,
        error_details=details,
        headers=headers
    ) 