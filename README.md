# geofabrik-mock-sever

Mock server for serving Geofabrik structured data.

### Installation

With pixi (make sure you're using `gis-forge` and `conda-forge` channels):

```
pixi add geofabrik-mock-server
```

### Usage

```bash
Usage: gms [OPTIONS] COMMAND [ARGS]...

  Geofabrik Mock Server — serve a local mock of download.geofabrik.de.

Options:
  --help  Show this message and exit.

Commands:
  add       Add a region to the mock manifest.
  download  Download PBF and update diffs for all manifest regions.
  remove    Remove a region from the mock manifest.
  serve     Serve the mock Geofabrik data over HTTP.
```
