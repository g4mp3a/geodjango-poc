import json
from typing import Union

from django.core.serializers import serialize
from django.db.models import QuerySet
from django.shortcuts import redirect
from django.views.generic import TemplateView
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from search.models import Business
from search.serializers import BusinessSerializer
from search.search_helper import BusinessSearcher, find_businesses_incrementally, get_businesses_by_city_state

class QueryView(APIView):
    """
    API endpoint that allows searching for businesses.
    """
    permission_classes = [AllowAny]
    serializer_class = BusinessSerializer
    
    def get(self, request):
        """
        Handle GET requests to search for businesses.

        Required query parameters:
        Either lat+lon or state are required
        - lat: Latitude (float)
        - lon: Longitude (float)
        - state: State (string)

        Optional query parameters:
        - radius_km: Radius in kilometers (int)
        - city: City (string)
        """
        lat = request.query_params.get('lat')
        lon = request.query_params.get('lon')
        radius_km = request.query_params.get('radius_km', 1)
        city = request.query_params.get('city')
        state = request.query_params.get('state')

        # Either lat and lon or state are required
        if not ((lat and lon) or state):
            return Response(
                {"error": "Please provide either lat+lon or a [city,] state"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            # Only convert lat/lon if they are provided
            if lat and lon:
                lat = float(lat)
                lon = float(lon)
            
            # Convert radius_km to int with a default of 1 if not provided or invalid
            try:
                radius_km = int(radius_km) if radius_km else 1
                if radius_km < 0:
                    return Response(
                        {"error": "radius_km cannot be negative"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except (ValueError, TypeError):
                radius_km = 1  # Default to 1km if conversion fails

            # If city+state or state are provided, find business by the given criteria
            businesses_city_state = get_businesses_by_city_state(city, state)
            # Find businesses by lat, lon and the supplied search radius or default to 1km
            radius_km, businesses_lat_lon = find_businesses_incrementally(lat, lon, radius_km)
            all_businesses = set(businesses_city_state + businesses_lat_lon)
            
            # Return the search results
            serializer = self.serializer_class(all_businesses, many=True)
            # Build a queryset for GeoJSON serialization
            business_ids = [b.id for b in all_businesses]
            queryset = Business.objects.filter(id__in=business_ids)
            geojson = json.loads(serialize('geojson', queryset))
            return Response({
                'results': serializer.data,
                'search_center': {'lat': lat, 'lng': lon},
                'radius_km': radius_km,
                'geoJSON': geojson,
            }, status=status.HTTP_200_OK)
            
        except ValueError:
            return Response(
                {"error": "Latitude and longitude must be valid numbers. Same for radius_km if provided."},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
