import json
import base64
import zipfile
from typing import Optional, Dict, Any
from pathlib import Path

from dash import Dash

from .callbacks import setup_callbacks
from .layout import create_layout


class ProtSpace:
    """Main application class for ProtSpace."""

    def __init__(self, pdb_zip: Optional[str] = None, default_json_file: Optional[str] = None):
        self.pdb_zip = pdb_zip
        self.default_json_data = None
        self.pdb_files_data = {}
        if default_json_file:
            with open(default_json_file, 'r') as f:
                self.default_json_data = json.load(f)
        if self.pdb_zip:
            self.load_pdb_files_from_zip(self.pdb_zip)

    def load_pdb_files_from_zip(self, zip_path):
        """Load PDB files from a ZIP archive and store them in pdb_files_data."""
        pdb_files = {}
        try:
            with zipfile.ZipFile(zip_path, 'r') as z:
                for file in z.namelist():
                    if file.endswith('.pdb') or file.endswith('.cif'):
                        with z.open(file) as f:
                            content = f.read()
                            pdb_files[Path(file).stem.replace(".", "_")] = base64.b64encode(content).decode('utf-8')
            self.pdb_files_data = pdb_files
        except Exception as e:
            print(f"Error loading PDB ZIP: {e}")

    def create_app(self):
        """Create and configure the Dash app."""
        app = Dash(__name__, suppress_callback_exceptions=True)
        app.title = "ProtSpace"
        app.layout = create_layout(self)
        setup_callbacks(app)
        return app

    def get_default_json_data(self) -> Optional[Dict[str, Any]]:
        """Return the default JSON data if available."""
        return self.default_json_data

    def get_pdb_files_data(self) -> Dict[str, str]:
        """Return the PDB files data."""
        return self.pdb_files_data

    def run_server(
        self, port: int = 8050, debug: bool = False, quiet: bool = True
    ) -> None:
        """Run the Dash server."""
        app = self.create_app()
        app.run_server(debug=debug, port=port)
