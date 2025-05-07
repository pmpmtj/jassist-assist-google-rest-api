"""
URL routing for the API app.
"""
from django.urls import path, include
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.decorators import permission_classes


@api_view(['GET'])
@permission_classes([AllowAny])
def api_root(request):
    """
    API root endpoint providing documentation.
    """
    return Response({
        'v1': request.build_absolute_uri('v1/'),
        'documentation': 'See README.md file for API documentation',
    })


urlpatterns = [
    # API root
    path('', api_root, name='api_root'),
    
    # API v1 endpoints
    path('v1/', include('jassist.web.api.v1.urls')),
    
    # DRF browsable API auth
    path('auth/', include('rest_framework.urls', namespace='rest_framework')),
] 