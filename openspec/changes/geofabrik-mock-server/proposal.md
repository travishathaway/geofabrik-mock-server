# Proposal: Geofabrik Mock Server

## Problem

Testing OSM data pipelines (osm2pgsql, pyosmium, osmium-tool) requires downloading real data from Geofabrik, which is slow, network-dependent, and pulls large files. There is no local mock that replicates Geofabrik's HTTP interface for PBF downloads and update replication feeds.

## Solution

Build a conda-installable CLI tool (`gms`) that:
1. Lets developers declare which Geofabrik regions they want to mock (committed to git)
2. Downloads the actual data during package build (not stored in git)
3. Serves the data over HTTP at URLs identical to Geofabrik's, so existing tools work with zero reconfiguration beyond pointing at `localhost`

The key capability is mocking the **update replication feed**: by specifying a past date when adding a region, the tool downloads update diffs from that date to today, enabling full end-to-end testing of the "apply incremental updates" workflow.

## Goals

- `gms add <region> [--date YYYY-MM-DD]`: register a region in the mock manifest
- `gms remove <region>`: remove a region from the manifest
- `gms download`: fetch PBF + update diffs from Geofabrik (run during conda build or local dev)
- `gms serve [--port N]`: serve mock data at Geofabrik-equivalent URL paths

## Non-Goals

- Mocking shapefile, history, or taginfo endpoints
- Storing actual OSM data in git
- Mutating/generating synthetic PBF content (real files from Geofabrik are used)

## Tech Stack

- Python ≥ 3.10, Click (CLI), Flask (HTTP server), requests (downloads)
- Pixi/conda-forge for packaging
- Data stored as Python package data (`importlib.resources`) so it's accessible post-install
