from django.urls import path
from django.views.generic import TemplateView

from search.views import QueryView
from search.health import HealthCheckView

urlpatterns = [
    # Map the root URL to the map template
    path("", TemplateView.as_view(template_name="map.html"), name='home'),
    
    # Search results view
    path("results/", TemplateView.as_view(template_name="map.html"), name='results'),
    path("results", TemplateView.as_view(template_name="map.html"), name='results-no-slash'),
    
    # Query endpoint
    path("query/", QueryView.as_view(), name='query'),
    path("query", QueryView.as_view(), name='query-no-slash'),
    
    # Health check endpoint
    path("health/", HealthCheckView.as_view(), name='health'),
    path("health", HealthCheckView.as_view(), name='health-no-slash'),
]
