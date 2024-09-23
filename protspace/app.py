import json
from typing import Optional, Dict, Any

from dash import Dash

from .callbacks import setup_callbacks
from .layout import create_layout


class ProtSpace:
    """Main application class for ProtSpace."""

    def __init__(self, pdb_dir: Optional[str] = None, default_json_file: Optional[str] = None):
        self.pdb_dir = pdb_dir
        self.default_json_data = None
        if default_json_file:
            with open(default_json_file, 'r') as f:
                self.default_json_data = json.load(f)

    def create_app(self):
        """Create and configure the Dash app."""
        app = Dash(__name__, suppress_callback_exceptions=True)
        app.title = "ProtSpace"
        app.layout = create_layout(self)
        setup_callbacks(app, self)
        return app

    def get_default_json_data(self) -> Optional[Dict[str, Any]]:
        """Return the default JSON data if available."""
        return self.default_json_data

    def run_server(
        self, port: int = 8050, debug: bool = False, quiet: bool = True
    ) -> None:
        """Run the Dash server."""
        app = self.create_app()
        app.run_server(debug=debug, port=port)
