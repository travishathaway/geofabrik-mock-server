#! /bin/sh

$PYTHON -m pip install . -vv --no-deps --no-build-isolation

# Register regions in the manifest
gms add monaco --date "$GMS_DATE"
gms add andorra --date "$GMS_DATE"

# Fetch PBF snapshots and update diffs into the installed package's data/ directory
gms download
