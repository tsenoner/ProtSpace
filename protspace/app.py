import os
import sys
from pathlib import Path
from typing import Dict, Optional

from dash import Dash

from .callbacks import setup_callbacks
from .data_loader import JsonReader
from .data_processing import prepare_dataframe
from .layout import create_layout
from .plotting import create_2d_plot, create_3d_plot, save_plot


class ProtSpace:
    def __init__(self, json_file: str, pdb_dir: Optional[str] = None):
        self.reader = JsonReader(json_file)
        self.projections = sorted(self.reader.get_projection_names())
        self.features = sorted(self.reader.get_all_features())
        self.protein_ids = sorted(self.reader.get_protein_ids())
        self.pdb_dir = pdb_dir

    def create_app(self):
        app = Dash(__name__, suppress_callback_exceptions=True)
        app.title = "ProtSpace"
        app.layout = create_layout(self)
        setup_callbacks(app, self)
        return app

    def run_server(
        self, port: int = 8050, debug: bool = False, quiet: bool = True
    ) -> None:
        import __main__

        def is_interactive():
            return not hasattr(__main__, "__file__")

        def supress_output():
            sys.stdout = open(os.devnull, "w")
            sys.stderr = open(os.devnull, "w")

        if is_interactive():
            supress_output()
        elif quiet:
            print(f"Dash app is running on http://localhost:{port}/")
            print("Press Ctrl+C to quit")
            supress_output()

        app = self.create_app()
        app.run_server(debug=debug, port=port)

    def generate_images(
        self,
        projection: str,
        feature: str,
        output_dir: str,
        width: int = 1600,
        height: int = 1000,
    ) -> None:
        output_dir = Path(output_dir)
        output_file = output_dir / f"{projection}_{feature}"
        output_dir.mkdir(parents=True, exist_ok=True)

        df = prepare_dataframe(self.reader, projection, feature)
        projection_info = self.reader.get_projection_info(projection)

        if projection_info["dimensions"] == 2:
            fig = create_2d_plot(df, feature, [])
            save_plot(
                fig,
                is_3d=False,
                width=width,
                height=height,
                filename=str(output_file.with_suffix(".svg")),
            )
        else:
            fig = create_3d_plot(df, feature, [])
            save_plot(
                fig, is_3d=True, filename=str(output_file.with_suffix(".html"))
            )

    def get_feature_colors(self, feature: str) -> Dict[str, str]:
        return self.reader.get_feature_colors(feature)
