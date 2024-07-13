import argparse
import itertools
from typing import Dict, Any
import os
import tempfile

import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go

from .data.json_loader import JsonReader

class ProtSpaceApp:
    def __init__(self, json_file: str):
        self.reader = JsonReader(json_file)
        self.projections = sorted(self.reader.get_projection_names())
        self.features = sorted(self.reader.get_all_features())
        self.app = self._create_app()
        self.temp_dir = tempfile.mkdtemp()

    def _create_app(self) -> dash.Dash:
        app = dash.Dash(__name__, suppress_callback_exceptions=True)
        app.title = "ProtSpace"
        app.layout = self._create_layout()
        self._setup_callbacks(app)
        return app

    def _create_layout(self) -> html.Div:
        return html.Div([
            html.H1("ProtSpace", style={"textAlign": "center"}),
            html.Div([
                dcc.Dropdown(
                    id="feature-dropdown",
                    options=[{"label": feature, "value": feature} for feature in self.features],
                    value=self.features[0],
                    style={"width": "48%", "display": "inline-block"},
                ),
                dcc.Dropdown(
                    id="projection-dropdown",
                    options=[{"label": proj, "value": proj} for proj in self.projections],
                    value=self.projections[0],
                    style={"width": "48%", "float": "right", "display": "inline-block"},
                ),
            ]),
            dcc.Graph(id="scatter-plot", style={"height": "80vh"}, responsive=True),
            html.Div([
                html.Button("Download", id="download-button", n_clicks=0),
                dcc.Input(id="image-width", type="number", placeholder="Width", value=1000, style={"marginLeft": "10px"}),
                dcc.Input(id="image-height", type="number", placeholder="Height", value=800, style={"marginLeft": "10px"}),
                dcc.Download(id="download-plot")
            ], style={"textAlign": "center", "marginTop": "20px"}),
        ], style={"padding": "20px"})

    def _setup_callbacks(self, app: dash.Dash) -> None:
        @app.callback(
            Output("scatter-plot", "figure"),
            [Input("projection-dropdown", "value"),
             Input("feature-dropdown", "value")]
        )
        def update_graph(selected_projection: str, selected_feature: str) -> go.Figure:
            df = self._prepare_dataframe(selected_projection, selected_feature)
            projection_info = self.reader.get_projection_info(selected_projection)

            if projection_info["dimensions"] == 2:
                return self._create_2d_plot(df, selected_feature)
            else:
                return self._create_3d_plot(df, selected_feature)

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
                raise dash.exceptions.PreventUpdate

            projection_info = self.reader.get_projection_info(selected_projection)

            if projection_info["dimensions"] == 2:
                return self._save_2d_plot(figure, width, height)
            else:
                return self._save_3d_plot(figure, width, height)

    def _save_2d_plot(self, figure: dict, width: int, height: int) -> dict:
        filename = os.path.join(self.temp_dir, "protspace_2d_plot.svg")
        fig = go.Figure(figure)
        fig.update_layout(width=width, height=height)
        fig.write_image(filename)
        return dcc.send_file(filename)

    def _save_3d_plot(self, figure: dict, width: int, height: int) -> dict:
        filename = os.path.join(self.temp_dir, "protspace_3d_plot.html")
        fig = go.Figure(figure)
        fig.update_layout(width=width, height=height)
        fig.write_html(filename, include_plotlyjs="cdn")
        return dcc.send_file(filename)

    def _prepare_dataframe(self, selected_projection: str, selected_feature: str) -> pd.DataFrame:
        projection_data = self.reader.get_projection_data(selected_projection)
        df = pd.DataFrame(projection_data)
        df["x"] = df["coordinates"].apply(lambda x: x["x"])
        df["y"] = df["coordinates"].apply(lambda x: x["y"])
        if self.reader.get_projection_info(selected_projection)["dimensions"] == 3:
            df["z"] = df["coordinates"].apply(lambda x: x["z"])

        df[selected_feature] = df["identifier"].apply(
            lambda x: self.reader.get_protein_features(x).get(selected_feature)
        )
        df[selected_feature] = df[selected_feature].replace({np.nan: "<NaN>", None: "<NaN>"})

        if df[selected_feature].dtype in ["float64", "int64"]:
            df[selected_feature] = df[selected_feature].astype(str)

        return df

    def _create_color_map(self, df: pd.DataFrame, selected_feature: str) -> Dict[str, str]:
        unique_values = df[selected_feature].unique()
        sorted_values = sorted([val for val in unique_values if val != "<NaN>"])
        sorted_values.append("<NaN>")

        color_discrete_map = {
            val: px.colors.qualitative.Plotly[i % len(px.colors.qualitative.Plotly)]
            for i, val in enumerate(sorted_values) if val != "<NaN>"
        }
        color_discrete_map["<NaN>"] = "lightgrey"
        return color_discrete_map

    def _create_2d_plot(self, df: pd.DataFrame, selected_feature: str) -> go.Figure:
        color_discrete_map = self._create_color_map(df, selected_feature)
        fig = px.scatter(
            df,
            x="x", y="y",
            color=selected_feature,
            color_discrete_map=color_discrete_map,
            hover_data={"identifier": True, selected_feature: True, "x": False, "y": False},
            category_orders={selected_feature: sorted(df[selected_feature].unique())},
        )

        # Increase dot size and set border width to 0.5
        fig.update_traces(marker=dict(size=10, line=dict(width=0.5, color='black')))

        fig.update_layout(
            xaxis=dict(showticklabels=False, showline=False, zeroline=False, showgrid=False, title=None),
            yaxis=dict(showticklabels=False, showline=False, zeroline=False, showgrid=False, title=None),
            plot_bgcolor='white',
            shapes=[
                dict(
                    type="rect",
                    xref="paper", yref="paper",
                    x0=0, y0=0, x1=1, y1=1,
                    line=dict(color="black", width=1),
                    fillcolor="rgba(0,0,0,0)"
                )
            ],
        )
        return fig

    def _create_3d_plot(self, df: pd.DataFrame, selected_feature: str) -> go.Figure:
        color_discrete_map = self._create_color_map(df, selected_feature)
        fig = px.scatter_3d(
            df,
            x="x", y="y", z="z",
            color=selected_feature,
            color_discrete_map=color_discrete_map,
            hover_data={"identifier": True, selected_feature: True, "x": False, "y": False, "z": False},
            category_orders={selected_feature: sorted(df[selected_feature].unique())},
        )

        # Add black border to markers
        fig.update_traces(marker=dict(line=dict(width=1, color='black')))

        fig.add_trace(self._create_bounding_box(df))
        fig.update_layout(
            scene=self._get_3d_scene_layout(df),
        )
        return fig

    def _create_bounding_box(self, df: pd.DataFrame) -> go.Scatter3d:
        bounds = {dim: [df[dim].min() * 1.05, df[dim].max() * 1.05] for dim in ["x", "y", "z"]}
        vertices = np.array(list(itertools.product(*bounds.values())))
        edges = [(0, 1), (1, 3), (3, 2), (2, 0), (4, 5), (5, 7), (7, 6), (6, 4), (0, 4), (1, 5), (2, 6), (3, 7)]

        return go.Scatter3d(
            x=[v for edge in edges for v in (vertices[edge[0]][0], vertices[edge[1]][0], None)],
            y=[v for edge in edges for v in (vertices[edge[0]][1], vertices[edge[1]][1], None)],
            z=[v for edge in edges for v in (vertices[edge[0]][2], vertices[edge[1]][2], None)],
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
            "xaxis": {**axis_layout, "range": [df["x"].min() * 1.05, df["x"].max() * 1.05]},
            "yaxis": {**axis_layout, "range": [df["y"].min() * 1.05, df["y"].max() * 1.05]},
            "zaxis": {**axis_layout, "range": [df["z"].min() * 1.05, df["z"].max() * 1.05]},
            "aspectmode": "cube",
        }

    def _get_common_layout(self, selected_feature: str) -> Dict[str, Any]:
        return {
            "legend_title_text": selected_feature,
            "height": 800,
            "autosize": True,
            "margin": dict(l=0, r=0, t=30, b=0),
            "title": None,
        }

    def run_server(self, debug: bool = True, port: int = 8050) -> None:
        self.app.run_server(debug=debug, port=port)

def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ProtSpace")
    parser.add_argument("json", help="Path to the input JSON file")
    parser.add_argument("--port", type=int, default=8050, help="Port to run the server on")
    return parser.parse_args()

def main() -> None:
    args = parse_arguments()
    app = ProtSpaceApp(args.json)
    app.run_server(debug=True, port=args.port)

if __name__ == "__main__":
    main()