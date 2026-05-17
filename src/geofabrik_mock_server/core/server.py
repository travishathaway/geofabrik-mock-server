from pathlib import Path

from flask import Flask, abort, send_file

_CONTENT_TYPES = {
    ".pbf": "application/x-protobuf",
    ".gz": "application/octet-stream",
    ".json": "application/json",
    ".txt": "text/plain",
    ".zip": "application/zip",
}


def _mime_for(path: Path) -> str:
    # Check double extension first (.osc.gz, .osm.pbf)
    suffixes = "".join(path.suffixes)
    for ext, mime in _CONTENT_TYPES.items():
        if suffixes.endswith(ext):
            return mime
    return "application/octet-stream"


def create_app(data_root: Path) -> Flask:
    app = Flask(__name__)

    @app.route("/index-v1.json")
    def index_json():
        index_path = data_root / "index-v1.json"
        if not index_path.exists():
            abort(404)
        return send_file(index_path, mimetype="application/json")

    @app.route("/<path:filepath>")
    def serve_file(filepath: str):
        target = (data_root / filepath).resolve()
        # Guard against path traversal outside data_root
        try:
            target.relative_to(data_root.resolve())
        except ValueError:
            abort(403)
        if not target.exists() or not target.is_file():
            abort(404)
        return send_file(target, mimetype=_mime_for(target))

    return app
