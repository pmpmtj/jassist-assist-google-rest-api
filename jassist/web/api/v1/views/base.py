"""
Base views for API v1.
"""
from rest_framework import viewsets, mixins
from rest_framework.views import APIView

from api.common.responses import success_response, error_response
from api.pagination import StandardResultsSetPagination


class BaseAPIView(APIView):
    """
    Base class for all API views with standardized response handling.
    """
    
    def finalize_response(self, request, response, *args, **kwargs):
        """
        Convert standard DRF response into our API response format if needed.
        
        Args:
            request: The HTTP request
            response: The original response
            
        Returns:
            Response: Standardized API response
        """
        # If the response is already in our format, return it as is
        if hasattr(response, 'data') and isinstance(response.data, dict) and 'status' in response.data:
            return super().finalize_response(request, response, *args, **kwargs)
            
        # If it's an error response, format it
        if response.status_code >= 400:
            error_msg = str(response.data) if hasattr(response, 'data') else "An error occurred"
            error_response_obj = error_response(
                message=error_msg,
                error_code="API_ERROR",
                status_code=response.status_code
            )
            return super().finalize_response(request, error_response_obj, *args, **kwargs)
        
        # If it's a success response, format it
        if hasattr(response, 'data'):
            success_response_obj = success_response(
                data=response.data,
                status_code=response.status_code
            )
            return super().finalize_response(request, success_response_obj, *args, **kwargs)
            
        return super().finalize_response(request, response, *args, **kwargs)


class BaseModelViewSet(viewsets.ModelViewSet):
    """
    Base class for all model-based viewsets with standardized response handling.
    """
    pagination_class = StandardResultsSetPagination
    
    def finalize_response(self, request, response, *args, **kwargs):
        """
        Convert standard DRF response into our API response format if needed.
        
        Args:
            request: The HTTP request
            response: The original response
            
        Returns:
            Response: Standardized API response
        """
        # Don't modify pagination responses
        if isinstance(response.data, dict) and 'count' in response.data and 'results' in response.data:
            return super().finalize_response(request, response, *args, **kwargs)
            
        # If the response is already in our format, return it as is
        if hasattr(response, 'data') and isinstance(response.data, dict) and 'status' in response.data:
            return super().finalize_response(request, response, *args, **kwargs)
            
        # If it's an error response, format it
        if response.status_code >= 400:
            error_msg = str(response.data) if hasattr(response, 'data') else "An error occurred"
            error_response_obj = error_response(
                message=error_msg,
                error_code="API_ERROR",
                status_code=response.status_code
            )
            return super().finalize_response(request, error_response_obj, *args, **kwargs)
        
        # If it's a success response, format it
        if hasattr(response, 'data'):
            success_response_obj = success_response(
                data=response.data,
                status_code=response.status_code
            )
            return super().finalize_response(request, success_response_obj, *args, **kwargs)
            
        return super().finalize_response(request, response, *args, **kwargs) 