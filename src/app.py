from dash import Dash
from flask_caching import Cache
from layout import create_layout
from callbacks import register_callbacks
from config import PROJECT_ROOT

ASSET_PATH = PROJECT_ROOT / "assets"

external_stylesheet = [
    {
        "href": "https://fonts.googleapis.com/css2?family=Lato:wght@400;700&display=swap",
        "rel": "stylesheet",
    },
]

app = Dash(__name__, assets_folder=str(ASSET_PATH), external_stylesheets=external_stylesheet)
app.title = "WoW Token Price Dashboard"

# Expose the Flask server for WSGI deployment
server = app.server

# SimpleCache reduces DB load by caching data between interval ticks
cache = Cache(app.server, config={"CACHE_TYPE": "SimpleCache"})

app.layout = create_layout()
register_callbacks(app, cache)

if __name__ == "__main__":
    app.run(debug=False, port=8050)
