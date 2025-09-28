from django.db import connection
from django.http import JsonResponse
from django.views import View

class HealthCheckView(View):
    """
    Health check endpoint that verifies the application is running and database is accessible.
    """
    def get(self, request, *args, **kwargs):
        # Check database connection
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                db_status = True
        except Exception:
            db_status = False

        # Prepare response data
        status_code = 200 if db_status else 503
        response_data = {
            'status': 'healthy' if status_code == 200 else 'unhealthy',
            'database': 'connected' if db_status else 'disconnected'
        }

        return JsonResponse(
            response_data,
            status=status_code,
            content_type='application/json'
        )
