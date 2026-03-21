import sqlite3
from flask import jsonify
from dash import Dash
from flask_caching import Cache

from callbacks import register_callbacks
from config import DB_PATH, PROJECT_ROOT
from layout import create_layout

ASSET_PATH = PROJECT_ROOT / "assets"

external_stylesheet = [
    {
        "href": "https://fonts.googleapis.com/css2?family=Lato:wght@400;700&display=swap",
        "rel": "stylesheet",
    },
]

app = Dash(
    __name__, assets_folder=str(ASSET_PATH), external_stylesheets=external_stylesheet
)
app.title = "WoW Token Price Dashboard"

# Expose the Flask server for WSGI deployment
server = app.server

# SimpleCache reduces DB load by caching data between interval ticks
cache = Cache(app.server, config={"CACHE_TYPE": "SimpleCache"})

app.layout = create_layout()
register_callbacks(app, cache)


@server.route("/health")
def health():
    """
    Liveness probe consumed by Docker HEALTHCHECK, Kubernetes, or any
    reverse proxy that needs to verify the service is up.

    Returns HTTP 200 when the application is running and the database
    file is accessible; HTTP 503 otherwise.
    """
    db_ok = False
    error = None
    if DB_PATH.exists():
        try:
            with sqlite3.connect(DB_PATH, timeout=2.0) as conn:
                conn.execute("SELECT 1")
            db_ok = True
        except sqlite3.Error as exc:
            error = str(exc)

    payload = {
        "status": "ok" if db_ok else "degraded",
        "db_exists": DB_PATH.exists(),
        "db_readable": db_ok,
    }
    if error:
        payload["error"] = error
    return jsonify(payload), 200 if db_ok else 503


if __name__ == "__main__":
    app.run(debug=False, port=8050)
