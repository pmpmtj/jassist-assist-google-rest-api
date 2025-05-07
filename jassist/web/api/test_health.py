"""
Unit tests for API health endpoint.
"""
import logging
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

logger = logging.getLogger(__name__)


class HealthEndpointTest(APITestCase):
    """Test cases for the health check endpoint."""

    def setUp(self):
        """Set up test environment."""
        logger.debug("Setting up HealthEndpointTest")

    def test_health_endpoint(self):
        """Test that the health endpoint returns the correct response."""
        url = reverse('api_health_check')
        logger.debug(f"Health check URL: {url}")
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(response.data['data']['status'], 'healthy')
        self.assertEqual(response.data['data']['api_version'], 'v1') 