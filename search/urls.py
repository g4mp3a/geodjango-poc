from django.urls import path
from django.views.generic import TemplateView

from search.views import SearchResultsMapView, QueryView
from search.health import HealthCheckView

urlpatterns = [
    # Map the root URL to the map template
    path("", TemplateView.as_view(template_name="map.html"), name='home'),
    
    # Search results view
    path("results/", SearchResultsMapView.as_view(), name='results'),
    path("results", SearchResultsMapView.as_view(), name='results-no-slash'),
    
    # Query endpoint
    path("query/", QueryView.as_view(), name='query'),
    path("query", QueryView.as_view(), name='query-no-slash'),
    
    # Health check endpoint
    path("health/", HealthCheckView.as_view(), name='health'),
    path("health", HealthCheckView.as_view(), name='health-no-slash'),
]
