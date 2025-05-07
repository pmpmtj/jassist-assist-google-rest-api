"""
Base serializers for the API.
These provide common functionality for all serializers in the system.
"""
from rest_framework import serializers
from rest_framework.serializers import ValidationError

from api.common.exceptions import ValidationError as APIValidationError


class BaseSerializer(serializers.Serializer):
    """
    Base serializer class with enhanced validation and error handling.
    """
    def validate(self, attrs):
        """
        Provides standard validation error handling.
        
        Args:
            attrs: Validated fields
            
        Returns:
            dict: Validated data
        """
        try:
            return super().validate(attrs)
        except ValidationError as e:
            # Convert DRF validation errors to our custom format
            raise APIValidationError(
                message="Validation failed",
                details=e.detail
            )
    
    def to_internal_value(self, data):
        """
        Convert input data to Python types.
        
        Args:
            data: Input data
            
        Returns:
            dict: Converted data
        """
        try:
            return super().to_internal_value(data)
        except ValidationError as e:
            # Convert DRF validation errors to our custom format
            raise APIValidationError(
                message="Invalid input data",
                details=e.detail
            )


class BaseModelSerializer(serializers.ModelSerializer):
    """
    Base model serializer with enhanced validation and error handling.
    """
    def validate(self, attrs):
        """
        Provides standard validation error handling.
        
        Args:
            attrs: Validated fields
            
        Returns:
            dict: Validated data
        """
        try:
            return super().validate(attrs)
        except ValidationError as e:
            # Convert DRF validation errors to our custom format
            raise APIValidationError(
                message="Validation failed",
                details=e.detail
            )
    
    def to_internal_value(self, data):
        """
        Convert input data to Python types.
        
        Args:
            data: Input data
            
        Returns:
            dict: Converted data
        """
        try:
            return super().to_internal_value(data)
        except ValidationError as e:
            # Convert DRF validation errors to our custom format
            raise APIValidationError(
                message="Invalid input data",
                details=e.detail
            ) 