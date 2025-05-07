"""
Pagination classes for API result sets.
"""
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class BasePagination(PageNumberPagination):
    """
    Base pagination class with enhanced metadata.
    """
    
    def get_paginated_response(self, data):
        """
        Return a paginated response with enhanced metadata.
        
        Args:
            data: The paginated data
            
        Returns:
            Response: DRF response with pagination metadata
        """
        return Response({
            'count': self.page.paginator.count,
            'total_pages': self.page.paginator.num_pages,
            'current_page': self.page.number,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data
        })


class StandardResultsSetPagination(BasePagination):
    """
    Standard pagination for most API endpoints.
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class LargeResultsSetPagination(BasePagination):
    """
    Pagination for larger result sets.
    """
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 500 