# This "normal" image includes GDAL and its common dependencies.
# Using slim is a nightmare thanks to version mismatches
# and/or missing dependencies in ghcr.io/osgeo/gdal:alpine-slim-3.11.4
FROM ghcr.io/osgeo/gdal:alpine-normal-3.11.4

# Must explicitly set the `SPATIALITE_LIBRARY_PATH` environment variable
# coz its not set by default and Django can not automatically find it in this image
# Also, the image contains the 8.1.0 version of the library as verified by:
# docker run --rm ghcr.io/osgeo/gdal:alpine-normal-3.11.4 find / -name 'mod_spatialite.so*' 2>/dev/null || echo 'mod_spatialite.so not found'
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PYTHONFAULTHANDLER=1 \
    SPATIALITE_LIBRARY_PATH=/usr/lib/mod_spatialite.so.8.1.0 \
    GDAL_LIBRARY_PATH=/usr/lib/libgdal.so.37.3.11.4 \
    GEOS_LIBRARY_PATH=/usr/lib/libgeos_c.so.1.19.0

# Debug output for spatialite library path
#RUN echo "*****" && \
#    echo "Spatialite library path: $SPATIALITE_LIBRARY_PATH" && \
#    echo "*****"
# Arguments for user and group names
ARG APP_USER=myuser
ARG APP_GROUP=mygroup
ARG APP_UID=1000
ARG APP_GID=1000

# Install basic deps
RUN apk add --no-cache python3 py3-pip python3-dev curl

# Create a non-root system user.
RUN addgroup -g $APP_GID $APP_GROUP && \
    adduser -S -u $APP_UID -G $APP_GROUP $APP_USER

## Need a venv
#RUN python3 -m venv /venv && \
#    . /venv/bin/activate
#ENV PATH="/venv/bin:$PATH"

WORKDIR /app

# Leverage cache
COPY requirements.txt ./
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt

# Copy the entrypoint script and the application code.
COPY --chown=$APP_USER:$APP_GROUP entrypoint.sh ./
COPY --chown=$APP_USER:$APP_GROUP . .
RUN mkdir -p /app/db && \
    chown -R $APP_USER:$APP_GROUP /app/db

# Delete the .env file to prevent it from being loaded at runtime as it contains local dev setup paths
RUN rm -f .env

# Run collectstatic to gather all static assets.
# Run this as the root user since it's a build step.
USER root
RUN python3 manage.py collectstatic --noinput

# Switch to the non-root user for security.
USER $APP_USER

# Health check, assuming your application serves on port 8000.
# The `curl` command was installed above for this purpose.
# Setting the interval to 300s (5 minutes) as its good enough for a poc and also avoids false positives
HEALTHCHECK --interval=300s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Expose the port your application listens on.
EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
