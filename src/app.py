from dash import Dash
from pathlib import Path
from flask_caching import Cache
from layout import create_layout
from callbacks import register_callbacks

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSET_PATH = PROJECT_ROOT / "assets"

# External stylesheet configuration for the 'Lato' font.
external_stylesheet = [
    {
        "href": (
            "https://fonts.googleapis.com/css2?family=Lato:wght@400;700&display=swap"
        ),
        "rel": "stylesheet",
    },
]

# Initialize the Dash application with asset and external stylesheet configuration.
app = Dash(__name__, assets_folder=ASSET_PATH, external_stylesheets=external_stylesheet)
app.title = "WoW Token Price"

# Initialize a simple in-memory cache for data and API responses.
cache = Cache(app.server, config={"CACHE_TYPE": "SimpleCache"})

# Set the application layout.
app.layout = create_layout()
# Register all necessary callbacks (connects inputs to outputs).
register_callbacks(app, cache)
