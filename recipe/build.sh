#! /bin/bash

$PYTHON -m pip install . -vv --no-deps --no-build-isolation

# Register regions in the manifest
gms add monaco --date "$GEOFABRIK_MOCK_SERVER_DATE"
gms add andorra --date "$GEOFABRIK_MOCK_SERVER_DATE"
gms add us/wyoming --date "$GEOFABRIK_MOCK_SERVER_DATE"
gms add us/montana --date "$GEOFABRIK_MOCK_SERVER_DATE"
gms add bremen --date "$GEOFABRIK_MOCK_SERVER_DATE"
gms add hamburg --date "$GEOFABRIK_MOCK_SERVER_DATE"

# Fetch PBF snapshots and update diffs into the installed package's data/ directory
gms download --directory "$PREFIX/local/share/geofabrik-mock-server"

# Creating the environment variable configuration
mkdir -p "$PREFIX/etc/conda/env_vars.d"
cat > "$PREFIX/etc/conda/env_vars.d/geofabrik-mock-server.json" << EOF
{
  "GEOFABRIK_MOCK_SERVER_ROOT_DIR": "$PREFIX/local/share/geofabrik-mock-server"
}
EOF
