from dash import Dash
from pathlib import Path
from flask_caching import Cache
from layout import create_layout
from callbacks import register_callbacks

# Define the project root and assets directory for portable file referencing.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSET_PATH = PROJECT_ROOT / "assets"

# Configure external stylesheets.
external_stylesheet = [
    {
        "href": (
            "https://fonts.googleapis.com/css2?family=Lato:wght@400;700&display=swap"
        ),
        "rel": "stylesheet",
    },
]

# Initialize the Dash app, explicitly defining the custom assets folder and stylesheets.
app = Dash(__name__, assets_folder=ASSET_PATH, external_stylesheets=external_stylesheet)
app.title = "WoW Token Price"

# Expose the underlying Flask server for WSGI deployment.
server = app.server

# Initialize Flask-Caching with SimpleCache to optimize API response times.
cache = Cache(app.server, config={"CACHE_TYPE": "SimpleCache"})

# Load and assign the application's visual structure.
app.layout = create_layout()

# Register interaction logic and pass the cache instance to the callback handlers.
register_callbacks(app, cache)

# Start the application server if this script is executed directly.
if __name__ == "__main__":
    app.run(debug=False, port=8050)
