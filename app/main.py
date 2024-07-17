import argparse
import itertools
import io
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import dash
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
from dash import dcc, html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from dash_bio import NglMoleculeViewer
from dash_bio.utils import ngl_parser

from .data.json_loader import JsonReader


class ProtSpaceApp:
    def __init__(self, json_file: str, pdb_dir: Optional[str] = None):
        self.reader = JsonReader(json_file)
        self.projections = sorted(self.reader.get_projection_names())
        self.features = sorted(self.reader.get_all_features())
        self.protein_ids = sorted(self.reader.get_protein_ids())
        self.pdb_dir = pdb_dir

    def _create_app(self) -> dash.Dash:
        app = dash.Dash(__name__, suppress_callback_exceptions=True)
        app.title = "ProtSpace"
        app.layout = self._create_layout()
        self._setup_callbacks(app)
        return app

    def _create_layout(self) -> html.Div:
        common_layout = [
            html.H1(
                "ProtSpace",
                style={
                    "textAlign": "center",
                    "margin": "0",
                    "padding": "10px 0",
                },
            ),
            html.Div(
                [
                    dcc.Dropdown(
                        id="feature-dropdown",
                        options=[
                            {"label": feature, "value": feature}
                            for feature in self.features
                        ],
                        value=self.features[0],
                        placeholder="Select a feature",
                        style={"width": "24vw", "display": "inline-block"},
                    ),
                    dcc.Dropdown(
                        id="projection-dropdown",
                        options=[
                            {"label": proj, "value": proj}
                            for proj in self.projections
                        ],
                        value=self.projections[0],
                        placeholder="Select a projection",
                        style={"width": "24vw", "display": "inline-block"},
                    ),
                    dcc.Dropdown(
                        id="protein-search-dropdown",
                        options=[
                            {"label": pid, "value": pid}
                            for pid in self.protein_ids
                        ],
                        value=[],
                        placeholder="Search for protein identifiers",
                        multi=True,
                        style={"width": "48vw", "display": "inline-block"},
                    ),
                ],
                style={"display": "flex", "justifyContent": "space-between"},
            ),
        ]

        if self.pdb_dir:
            plot_layout = html.Div(
                [
                    html.Div(
                        [  # Wrapper for the scatter plot
                            dcc.Graph(
                                id="scatter-plot",
                                style={"height": "100%"},
                                responsive=True,
                            )
                        ],
                        style={
                            "border": "2px solid #dddddd",
                            "height": "calc(100vh - 200px)",
                            "width": "48vw",
                            "display": "inline-block",
                            "marginBottom": "20px",
                        },
                    ),
                    html.Div(
                        [  # Wrapper for the protein structure viewer and info
                            NglMoleculeViewer(
                                id="ngl-molecule-viewer",
                                width="100%",
                                height="calc(100vh - 200px)",
                                molStyles={
                                    "representations": ["cartoon"],
                                    "chosenAtomsColor": "white",
                                    "chosenAtomsRadius": 0.5,
                                    "molSpacingXaxis": 50,
                                    "sideByside": True,
                                },
                            ),
                        ],
                        style={
                            "border": "2px solid #dddddd",
                            "height": "calc(100vh - 200px)",
                            "width": "48vw",
                            "display": "inline-block",
                            "marginBottom": "20px",
                        },
                    ),
                ],
                style={
                    "display": "flex",
                    "justifyContent": "space-between",
                },
            )
        else:
            plot_layout = html.Div(
                [
                    dcc.Graph(
                        id="scatter-plot",
                        style={"height": "calc(100vh - 200px)"},
                        responsive=True,
                    )
                ],
                style={
                    "border": "2px solid #dddddd",
                    "height": "calc(100vh - 200px)",
                    "marginBottom": "20px",
                },
            )

        common_layout.append(plot_layout)

        common_layout.append(
            html.Div(
                [  # Wrapper for the button and inputs
                    html.Button("Download", id="download-button", n_clicks=0),
                    dcc.Input(
                        id="image-width",
                        type="number",
                        placeholder="Width",
                        value=1600,
                        style={"marginLeft": "10px"},
                    ),
                    dcc.Input(
                        id="image-height",
                        type="number",
                        placeholder="Height",
                        value=1000,
                        style={"marginLeft": "10px"},
                    ),
                    dcc.Download(id="download-plot"),
                ],
                style={
                    "display": "flex",
                    "justifyContent": "center",
                    "alignItems": "center",
                    "height": "50px",
                },
            )
        )

        return html.Div(
            common_layout,
            style={
                "display": "flex",
                "flexDirection": "column",
                "height": "100vh",
                "padding": "20px",
                "boxSizing": "border-box",
            },
        )

    def _setup_callbacks(self, app: dash.Dash) -> None:
        @app.callback(
            Output("scatter-plot", "figure"),
            [
                Input("projection-dropdown", "value"),
                Input("feature-dropdown", "value"),
                Input("protein-search-dropdown", "value"),
            ],
        )
        def update_graph(
            selected_projection: str,
            selected_feature: str,
            selected_proteins: List[str],
        ) -> go.Figure:
            df = self._prepare_dataframe(selected_projection, selected_feature)
            projection_info = self.reader.get_projection_info(
                selected_projection
            )

            if projection_info["dimensions"] == 2:
                return self._create_2d_plot(
                    df, selected_feature, selected_proteins
                )
            else:
                return self._create_3d_plot(
                    df, selected_feature, selected_proteins
                )

        if self.pdb_dir:
            @app.callback(
                Output("ngl-molecule-viewer", "data"),
                Input("protein-search-dropdown", "value"),
            )
            def update_protein_structure_info(
                selected_proteins: List[str],
            ) -> tuple:
                if not selected_proteins:
                    raise PreventUpdate

                data_list = []
                for protein_id in selected_proteins:
                    protein_id_underscore = protein_id.replace(".", "_")
                    data_structure = ngl_parser.get_data(
                        data_path=self.pdb_dir + "/",
                        pdb_id=protein_id_underscore,
                        color="black",
                        reset_view=True,
                        local=True,
                    )
                    data_list.append(data_structure)

                return data_list

        @app.callback(
            Output("download-plot", "data"),
            Input("download-button", "n_clicks"),
            State("scatter-plot", "figure"),
            State("projection-dropdown", "value"),
            State("image-width", "value"),
            State("image-height", "value"),
            prevent_initial_call=True,
        )
        def download_plot(n_clicks, figure, selected_projection, width, height):
            if n_clicks == 0:
                raise PreventUpdate

            projection_info = self.reader.get_projection_info(
                selected_projection
            )

            if projection_info["dimensions"] == 2:
                return self._save_2d_plot(figure, width, height)
            else:
                return self._save_3d_plot(figure)

    def generate_images(self, projection: str, feature: str, output_dir: str, width: int, height: int) -> None:
        output_dir = Path(output_dir)
        output_file = output_dir / f"{projection}_{feature}"
        output_dir.mkdir(parents=True, exist_ok=True)

        df = self._prepare_dataframe(projection, feature)
        projection_info = self.reader.get_projection_info(projection)
        if projection_info["dimensions"] == 2:
            fig = self._create_2d_plot(df, feature, [])
            self._save_2d_plot(fig, width, height, output_file.with_suffix(".svg"))
        else:
            fig = self._create_3d_plot(df, feature, [])
            self._save_3d_plot(fig, output_file.with_suffix(".html"))

    def _save_2d_plot(self, figure: dict, width: int, height: int, filename: Optional[str] = None) -> Union[None, dict]:
        fig = go.Figure(figure)
        if filename:
            fig.write_image(filename, format="svg", width=width, height=height)
        else:
            buffer = io.BytesIO()
            fig.write_image(buffer, format="svg", width=width, height=height)
            buffer.seek(0)
            return dcc.send_bytes(buffer.getvalue(), "protspace_2d_plot.svg")

    def _save_3d_plot(self, figure: dict, filename: Optional[str] = None) -> Union[None, dict]:
        fig = go.Figure(figure)
        if filename:
            fig.write_html(filename, include_plotlyjs="cdn")
        else:
            buffer = io.StringIO()
            fig.write_html(buffer, include_plotlyjs="cdn")
            buffer.seek(0)
            return dcc.send_bytes(buffer.getvalue(), "protspace_3d_plot.html")

    def _prepare_dataframe(
        self, selected_projection: str, selected_feature: str
    ) -> pd.DataFrame:
        projection_data = self.reader.get_projection_data(selected_projection)
        df = pd.DataFrame(projection_data)
        df["x"] = df["coordinates"].apply(lambda x: x["x"])
        df["y"] = df["coordinates"].apply(lambda x: x["y"])
        if (
            self.reader.get_projection_info(selected_projection)["dimensions"]
            == 3
        ):
            df["z"] = df["coordinates"].apply(lambda x: x["z"])

        df[selected_feature] = df["identifier"].apply(
            lambda x: self.reader.get_protein_features(x).get(selected_feature)
        )
        df[selected_feature] = df[selected_feature].replace(
            {np.nan: "<NaN>", None: "<NaN>"}
        )

        if df[selected_feature].dtype in ["float64", "int64"]:
            df[selected_feature] = df[selected_feature].astype(str)

        return df

    def _create_color_map(
        self, df: pd.DataFrame, selected_feature: str
    ) -> Dict[str, str]:
        unique_values = df[selected_feature].unique()
        sorted_values = sorted([val for val in unique_values if val != "<NaN>"])
        sorted_values.append("<NaN>")

        color_discrete_map = {
            val: px.colors.qualitative.Plotly[
                i % len(px.colors.qualitative.Plotly)
            ]
            for i, val in enumerate(sorted_values)
            if val != "<NaN>"
        }
        color_discrete_map["<NaN>"] = "lightgrey"
        return color_discrete_map

    def _create_2d_plot(
        self,
        df: pd.DataFrame,
        selected_feature: str,
        selected_proteins: List[str],
    ) -> go.Figure:
        color_discrete_map = self._create_color_map(df, selected_feature)
        fig = px.scatter(
            df,
            x="x",
            y="y",
            color=selected_feature,
            color_discrete_map=color_discrete_map,
            hover_data={
                "identifier": True,
                selected_feature: True,
                "x": False,
                "y": False,
            },
            category_orders={
                selected_feature: sorted(df[selected_feature].unique())
            },
        )

        # Increase dot size and set border width to 0.5
        fig.update_traces(
            marker=dict(size=10, line=dict(width=0.5, color="black"))
        )

        # Highlight selected proteins
        if selected_proteins:
            selected_df = df[df["identifier"].isin(selected_proteins)]
            feature_value = selected_df[selected_feature].values[0]
            identifier = selected_df["identifier"].values[0]
            fig.add_trace(
                go.Scatter(
                    x=selected_df["x"],
                    y=selected_df["y"],
                    mode="markers",
                    marker=dict(
                        size=20,
                        color="rgba(255, 255, 0, 0.7)",  # Semi-transparent yellow
                        line=dict(width=3, color="red"),
                    ),
                    hoverinfo="text",
                    hovertext=f"{selected_feature}={feature_value}<br>identifier={identifier}",
                    showlegend=False,
                )
            )

        fig.update_layout(
            xaxis=dict(
                showticklabels=False,
                showline=False,
                zeroline=False,
                showgrid=False,
                title=None,
            ),
            yaxis=dict(
                showticklabels=False,
                showline=False,
                zeroline=False,
                showgrid=False,
                title=None,
            ),
            plot_bgcolor="white",
            margin=dict(l=0, r=0, t=0, b=0),
            uirevision="constant",  # Prevents scene update when searching protein IDs
        )
        return fig

    def _create_3d_plot(
        self,
        df: pd.DataFrame,
        selected_feature: str,
        selected_proteins: List[str],
    ) -> go.Figure:
        color_discrete_map = self._create_color_map(df, selected_feature)
        fig = px.scatter_3d(
            df,
            x="x",
            y="y",
            z="z",
            color=selected_feature,
            color_discrete_map=color_discrete_map,
            hover_data={
                "identifier": True,
                selected_feature: True,
                "x": False,
                "y": False,
                "z": False,
            },
            category_orders={
                selected_feature: sorted(df[selected_feature].unique())
            },
        )

        # Add black border to markers
        fig.update_traces(marker=dict(line=dict(width=1, color="black")))

        # Highlight selected proteins
        if selected_proteins:
            selected_df = df[df["identifier"].isin(selected_proteins)]
            feature_value = selected_df[selected_feature].values[0]
            identifier = selected_df["identifier"].values[0]
            fig.add_trace(
                go.Scatter3d(
                    x=selected_df["x"],
                    y=selected_df["y"],
                    z=selected_df["z"],
                    mode="markers",
                    marker=dict(
                        size=15,
                        color="rgba(255, 255, 0, 0.7)",  # Semi-transparent yellow
                        line=dict(width=3, color="red"),
                    ),
                    hoverinfo="text",
                    hovertext=f"{selected_feature}={feature_value}<br>identifier={identifier}",
                    showlegend=False,
                )
            )

        fig.add_trace(self._create_bounding_box(df))
        fig.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),
            scene=self._get_3d_scene_layout(df),
            uirevision="constant",  # Prevents scene update when searching protein IDs
        )
        return fig

    def _create_bounding_box(self, df: pd.DataFrame) -> go.Scatter3d:
        bounds = {
            dim: [df[dim].min() * 1.05, df[dim].max() * 1.05]
            for dim in ["x", "y", "z"]
        }
        vertices = np.array(list(itertools.product(*bounds.values())))
        edges = [
            (0, 1),
            (1, 3),
            (3, 2),
            (2, 0),
            (4, 5),
            (5, 7),
            (7, 6),
            (6, 4),
            (0, 4),
            (1, 5),
            (2, 6),
            (3, 7),
        ]

        return go.Scatter3d(
            x=[
                v
                for edge in edges
                for v in (vertices[edge[0]][0], vertices[edge[1]][0], None)
            ],
            y=[
                v
                for edge in edges
                for v in (vertices[edge[0]][1], vertices[edge[1]][1], None)
            ],
            z=[
                v
                for edge in edges
                for v in (vertices[edge[0]][2], vertices[edge[1]][2], None)
            ],
            mode="lines",
            line=dict(color="black", width=2),
            hoverinfo="none",
            showlegend=False,
        )

    def _get_3d_scene_layout(self, df: pd.DataFrame) -> Dict[str, Any]:
        axis_layout = dict(
            showbackground=False,
            showticklabels=False,
            showline=False,
            zeroline=False,
            showgrid=False,
            showspikes=False,
            title="",
        )
        return {
            "xaxis": {
                **axis_layout,
                "range": [df["x"].min() * 1.05, df["x"].max() * 1.05],
            },
            "yaxis": {
                **axis_layout,
                "range": [df["y"].min() * 1.05, df["y"].max() * 1.05],
            },
            "zaxis": {
                **axis_layout,
                "range": [df["z"].min() * 1.05, df["z"].max() * 1.05],
            },
            "aspectmode": "cube",
        }

    def run_server(self, debug: bool = True, port: int = 8050) -> None:
        self.app = self._create_app()
        self.app.run_server(debug=debug, port=port)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ProtSpace")
    parser.add_argument("json", help="Path to the input JSON file")
    parser.add_argument(
        "--pdb_dir",
        required=False,
        help="Path to the directory containing PDB files",
    )
    parser.add_argument(
        "--port", type=int, default=8050, help="Port to run the server on"
    )
    return parser.parse_args()

def create_file(json_file: str, projection: str, feature: str, output_dir: str = ".", width: int = 1600, height: int = 1000) -> None:
    protspace = ProtSpaceApp(json_file)
    available_projections = protspace.reader.get_projection_names()
    available_features = protspace.reader.get_all_features()

    if projection not in available_projections:
        raise ValueError(f"Projection '{projection}' not found. Available projections are: {', '.join(available_projections)}")

    if feature not in available_features:
        raise ValueError(f"Feature '{feature}' not found. Available features are: {', '.join(available_features)}")

    protspace.generate_images(output_dir=output_dir, projection=projection, feature=feature, width=width, height=height)
    print(f"Image generated and saved in {output_dir}")


def main(json: str, port: int=8050, pdb_dir: Optional[str] = None) -> None:
    protspace = ProtSpaceApp(json, pdb_dir)
    protspace.run_server(debug=True, port=port)


if __name__ == "__main__":
    args = parse_arguments()
    for p in ["PCA2", "PCA3", "UMAP2", "UMAP3"]:
        for f in ["group", "major_group"]:
            create_file(json_file=args.json, output_dir="examples/out", projection=p, feature=f)
    main(**vars(args))
