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
    db_ok = DB_PATH.exists()
    payload = {"status": "ok" if db_ok else "degraded", "db_exists": db_ok}
    status_code = 200 if db_ok else 503
    return jsonify(payload), status_code


if __name__ == "__main__":
    app.run(debug=False, port=8050)
