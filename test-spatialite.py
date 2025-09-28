import sqlite3
import os

from dotenv import load_dotenv

load_dotenv()
# Set the path to the SpatiaLite extension using the environment variable
# This example assumes the variable is already set.
# On macOS, the path is often `/usr/local/lib/mod_spatialite.dylib`
spatialite_path = os.getenv('SPATIALITE_LIBRARY_PATH')

if not spatialite_path:
    raise RuntimeError("SPATIALITE_LIBRARY_PATH environment variable is not set.")

# Create a connection to an in-memory SQLite database
conn = sqlite3.connect(":memory:")

# Enable extension loading
conn.enable_load_extension(True)

try:
    # Load the SpatiaLite extension
    conn.execute("SELECT load_extension(?)", (spatialite_path,))

    # Check the SpatiaLite version to confirm it's loaded
    version_result = conn.execute("SELECT spatialite_version()").fetchone()
    print(f"SpatiaLite loaded successfully. Version: {version_result[0]}")

    # Initialize spatial metadata for the database
    conn.execute("SELECT InitSpatialMetadata(1)")

    # Execute a spatial function to confirm functionality
    point_wkt = "POINT(10 20)"
    test_query = conn.execute(
        "SELECT ST_AsText(GeomFromText(?, 4326))",
        (point_wkt,)
    ).fetchone()

    assert test_query[0] == point_wkt, "Spatial function failed to return expected result."
    print(f"Spatial function test passed. Output: {test_query[0]}")

except sqlite3.OperationalError as e:
    print(f"Error loading SpatiaLite: {e}")
finally:
    conn.close()

