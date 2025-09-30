from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.db import connection
from django.db.models import QuerySet

import bisect
from search.models import Business
from .constants import RADIUS_INCREMENTS_KM
from typing import List, Optional, Sequence, Union, Tuple


class BusinessSearcher:
    """
    A class to handle business search operations with configurable search parameters.
    
    Attributes:
        radius_increments_km: List of radius values (in kilometers) to use for incremental search
    """
    
    def __init__(self, radius_increments_km: Optional[Sequence[Union[int, float]]] = None):
        """
        Initialize the BusinessSearcher with optional custom radius increments.
        
        Args:
            radius_increments_km: List of radius values in kilometers for incremental search.
                                 Defaults to [1, 5, 10, 25, 50, 100] km.
        """
        self.radius_increments_km = list(radius_increments_km) if radius_increments_km else RADIUS_INCREMENTS_KM
    
    def find_businesses_incrementally(self, start_lat: float, start_lon: float, query_radius_km: int) -> Tuple[int, List[Business]]:
        """
        Search for businesses, incrementally increasing the search radius starting from the given query radius.
        Radius increments are taken from the radius_increments_km list.
        Assume radius is an int and is in kilometers and lat, lon are in WGS84.
        
        Args:
            start_lat: Starting latitude (WGS84)
            start_lon: Starting longitude (WGS84)
            query_radius_km: Query radius in kilometers
            
        Returns:
            Tuple[int, List[Business]: List of found Business objects, or empty list if none found and the radius used
        """
        # If both lat and lon are not provided, return an empty list
        if not start_lat or not start_lon:
            return 0, []

        if query_radius_km and query_radius_km > 1:
            # Find the index of the first radius increment greater than the query radius to create a list of radii to search
            # insert_idx = bisect.bisect_right(self.radius_increments_km, query_radius_km)
            # radii_km = [query_radius_km] + self.radius_increments_km[insert_idx:]
            # I misunderstood the requirements ^.
            # I think I need to increment the search radius by radius_increments_km each time no businesses are found.
            radii_km = [query_radius_km]
            for increment in self.radius_increments_km:
                radii_km.append(radii_km[0] + increment) # Could also do radii_km.append(radii_km[-1] + increment)
        else:
            radii_km = self.radius_increments_km

        for radius_km in radii_km:
            businesses = self._find_businesses_within_radius(start_lat, start_lon, radius_km)
            if businesses:
                print(f"Found {len(businesses)} businesses within {radius_km} km.")
                return radius_km, businesses
        # Found no businesses
        return 0, []
    
    def _find_businesses_within_radius(self, lat: float, lon: float, radius_km: int) -> List[Business]:
        """
        Find businesses within a specific radius of a point.
        Assumes radius is an int and is in kilometers and lat, lon are in WGS84.
        
        Args:
            lat: Center point latitude (WGS84)
            lon: Center point longitude (WGS84)
            radius_km: Search radius in kilometers
            
        Returns:
            List[Business]: List of businesses within the radius
        """

        # Working with spatialite and django is painful!! BEWARE of taking this on short notice... chutzpah!
        # Fix that seems to work w/o errors: Use the django geodjango orm instead of raw sql. However, not sure if its
        # really returning all the businesses correctly. Need to build a test case to verify this.
        # Learnt about geodjango orm functions.
        # Another option would be to use a raw query and have it return the business ids only and then use the django
        # orm to get the business objects.
        # While I need to write tests to verify correctness, I'm going with the geodjango orm approach for now.
        # This coz manual tests showed both the approaches returning the same number of businesses.

        # Get biz ids only and use django orm to get the biz objects.
        # 1 = calculate in meters (spheroid)
        # query = """
        # SELECT id FROM (
        #     SELECT
        #         id,
        #         ST_Distance(
        #             location,
        #             MakePoint(%s, %s, 4326),
        #             1
        #         ) AS distance_meters
        #     FROM
        #         search_business
        # ) AS subquery
        # WHERE distance_meters <= %s
        # ORDER BY distance_meters;
        # """
        # radius_meters = radius_km * 1000
        # cursor = connection.cursor()
        # cursor.execute(query, (lon, lat, radius_meters))
        # business_ids = [row[0] for row in cursor.fetchall()]
        # return list(Business.objects.filter(id__in=business_ids))

        # Get biz objects using geodjango orm.
        # Also, dont really need the `distance_meters` field in the result set. Removing it will make this
        # query faster. However, for now keeping it since I am still working through things.
        point = Point(lon, lat, srid=4326)
        businesses = Business.objects.filter(
            location__distance_lte=(
                point,
                D(km=radius_km)
            )
        ).annotate(
            distance_meters=Distance('location', point)
        ).order_by('distance_meters')

        return list(businesses)

        # Error: checking Geometry returned from GEOS C function "GEOSWKBReader_readHEX_r" : nightmare # 4
        # Even using AsBinary and GeomFromWKB so Django's ORM can handle the geometry returned from SpatiaLite
        # did not work.
        # 1 = calculate in meters (spheroid)
        # query = """
        # WITH distance_cte AS (
        #     SELECT
        #         id, name, city, state,
        #         AsBinary(location) as location_wkb,
        #         ST_Distance(
        #             location,
        #             MakePoint(%s, %s, 4326),
        #             1
        #         ) AS distance_meters
        #     FROM
        #         search_business
        # )
        # SELECT
        #     id, name, city, state,
        #     GeomFromWKB(location_wkb, 4326) as location,
        #     distance_meters
        # FROM distance_cte
        # WHERE distance_meters <= %s
        # ORDER BY distance_meters;
        # """
        # # Convert km to meters for the query
        # radius_meters = radius_km * 1000
        # # SpatiaLite uses X,Y (longitude,latitude) order for coordinates!!
        # return self._execute_sql_query(query, (lon, lat, radius_meters))
    
    def find_businesses_by_location(self, city: str, state: str) -> List[Business]:
        """
        Find all businesses in a specific city and state.
        
        Args:
            city: City name (case-insensitive)
            state: State code (case-insensitive, e.g., 'CA' for California)
            
        Returns:
            List[Business]: List of businesses in the specified city and state
        """
        if not city or not state:
            return []
            
        query = """
        SELECT *
        FROM search_business
        WHERE LOWER(city) = LOWER(%s)
        AND LOWER(state) = LOWER(%s)
        ORDER BY name
        """
        
        return self._execute_sql_query(query, (city.strip(), state.strip()))

    @staticmethod
    def _execute_sql_query(query: str, params: tuple = None) -> List[Business]:
        """
        Execute a parameterized SQL query and return Business objects.
        Assumes the query is a SELECT statement that returns Business objects.
        Assumes that the query is parameterized with %s placeholders.
        Assumes that the number of parameters matches the number of placeholders.
        Assumes that the number of results returned is fairly small. Worry about perf enhancements later.
        
        Args:
            query: The SQL query with %s placeholders
            params: Tuple of parameters to substitute into the query
            
        Returns:
            List[Business]: List of Business objects from the query results
        """
        # Assumes that the number of results returned is fairly small. Worry about perf enhancements later.
        return list(Business.objects.raw(query, params or ()))

    # So I notice that this pulls a few results from outside the state as well.
    # Not sure if this is expected behavior in spatialite.
    # Revisit this later - not a P0 or P1.
    def get_businesses_by_city_state(self, city: str, state: str) -> List[Business]:
        """
        Get businesses by city and state.

        Args:
            city: City name (case-insensitive)
            state: State code (case-insensitive, e.g., 'CA' for California)

        Returns:
            QuerySet[Business]: QuerySet of Business objects in the specified city and state
        """
        if not state:
            # print("Please specify a state")
            return []

        queryset = Business.objects.all()
        if state:
            queryset = queryset.filter(state=state)
        if city:
            queryset = queryset.filter(city=city)

        # Assumes that the number of results returned is fairly small. Worry about perf enhancements later.
        return list(queryset)

# Easier to type!
find_businesses_incrementally = BusinessSearcher().find_businesses_incrementally
find_businesses_by_location = BusinessSearcher().find_businesses_by_location
get_businesses_by_city_state = BusinessSearcher().get_businesses_by_city_state

