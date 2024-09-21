import base64
import json

import plotly.graph_objs as go
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from dash_bio.utils import ngl_parser

from .data_processing import prepare_dataframe
from .plotting import create_2d_plot, create_3d_plot, save_plot
from .utils import NAN_COLOR


def setup_callbacks(app, protspace):
    @app.callback(
        Output("scatter-plot", "figure"),
        [
            Input("projection-dropdown", "value"),
            Input("feature-dropdown", "value"),
            Input("protein-search-dropdown", "value"),
            Input("apply-style-button", "n_clicks"),
        ],
        [
            State("feature-value-dropdown", "value"),
            State("marker-color-picker", "value"),
            State("marker-shape-dropdown", "value"),
        ],
    )
    def update_graph(
        selected_projection,
        selected_feature,
        selected_proteins,
        n_clicks,
        selected_value,
        selected_color,
        selected_shape,
    ):
        # Update the changed values
        if n_clicks is not None and selected_value is not None:
            if selected_color:
                # print(selected_color)
                if selected_color['hex'].startswith('rgba'):
                    selected_color_str = selected_color['hex']
                else:
                    selected_color_str = "rgba({r}, {g}, {b}, {a})".format(**selected_color['rgb'])
                protspace.reader.update_feature_color(selected_feature, selected_value, selected_color_str)
            if selected_shape:
                protspace.reader.update_marker_shape(selected_feature, selected_value, selected_shape)

        df = prepare_dataframe(
            protspace.reader, selected_projection, selected_feature
        )
        feature_colors = protspace.reader.get_feature_colors(selected_feature)
        marker_shapes = protspace.reader.get_marker_shape(selected_feature)
        projection_info = protspace.reader.get_projection_info(selected_projection)

        if projection_info["dimensions"] == 2:
            fig = create_2d_plot(df, selected_feature, selected_proteins)
        else:
            fig = create_3d_plot(df, selected_feature, selected_proteins)

        # Apply all stored styles
        for value in df[selected_feature].unique():
            color = feature_colors.get(value)
            shape = marker_shapes.get(value)
            if color or shape:
                fig.update_traces(
                    marker=dict(
                        color=color if color else None,
                        symbol=shape if shape else None,
                    ),
                    selector=dict(name=value)
                )
            if value == "<NaN>":
                fig.update_traces(
                    marker=dict(
                        color=NAN_COLOR,
                    ),
                    selector=dict(name=value)
                )

        return fig

    @app.callback(
        Output("feature-dropdown", "options"),
        Output("feature-dropdown", "value"),
        Output("projection-dropdown", "options"),
        Output("projection-dropdown", "value"),
        Output("protein-search-dropdown", "options"),
        Input("upload-json", "contents"),
        State("upload-json", "filename"),
        prevent_initial_call=True,
    )
    def update_data_from_upload(contents, filename):
        if contents is None:
            raise PreventUpdate

        content_type, content_string = contents.split(",")
        decoded = base64.b64decode(content_string)
        try:
            if "json" in filename:
                data = json.loads(decoded.decode("utf-8"))
                protspace.reader.data = data  # Update the data in the reader
                protspace.update_data()  # Update the ProtSpace object

                # Update dropdowns
                feature_options = [{"label": feature, "value": feature} for feature in protspace.features]
                projection_options = [{"label": proj, "value": proj} for proj in protspace.projections]
                protein_options = [{"label": pid, "value": pid} for pid in protspace.protein_ids]

                # Select the first feature and projection
                first_feature = protspace.features[0] if protspace.features else None
                first_projection = protspace.projections[0] if protspace.projections else None


                return (
                    feature_options,
                    first_feature,
                    projection_options,
                    first_projection,
                    protein_options,
                )
        except Exception as e:
            print(f"Error loading JSON: {e}")
            return [], None, [], None, []

    @app.callback(
        Output("download-json", "data"),
        Input("download-json-button", "n_clicks"),
        prevent_initial_call=True,
    )
    def download_json(n_clicks):
        if n_clicks == 0:
            raise PreventUpdate

        return dict(
            content=json.dumps(protspace.reader.data, indent=2),
            filename="protspace_data.json",
        )

    @app.callback(
        Output("marker-style-controller", "style"),
        Input("settings-button", "n_clicks"),
        State("marker-style-controller", "style"),
    )
    def toggle_marker_style_controller(n_clicks, current_style):
        if n_clicks is None:
            return {"display": "none"}
        if current_style["display"] == "none":
            return {
                "display": "block",
                "width": "300px",
                "padding": "20px",
                "backgroundColor": "#f0f0f0",
                "borderRadius": "5px",
            }
        else:
            return {"display": "none"}

    @app.callback(
        Output("feature-value-dropdown", "options"),
        Input("feature-dropdown", "value"),
    )
    def update_feature_value_options(selected_feature):
        if selected_feature is None:
            return []
        unique_values = protspace.reader.get_unique_feature_values(
            selected_feature
        )
        return [{"label": str(val), "value": str(val)} for val in sorted(unique_values)]

    @app.callback(
        Output("marker-color-picker", "value"),
        Input("feature-dropdown", "value"),
        Input("feature-value-dropdown", "value"),
    )
    def update_marker_color_picker(selected_feature, selected_value):
        if selected_feature is None or selected_value is None:
            raise PreventUpdate

        feature_colors = protspace.reader.get_feature_colors(selected_feature)
        if selected_value in feature_colors:
            return {"hex": feature_colors[selected_value]}
        else:
            # If no color is defined for the selected value, return a default color
            return {"hex": "#000000"}  # Default to black

    @app.callback(
        Output("marker-shape-dropdown", "value"),
        Input("feature-dropdown", "value"),
        Input("feature-value-dropdown", "value"),
    )
    def update_marker_shape_dropdown(selected_feature, selected_value):
        if selected_feature is None or selected_value is None:
            raise PreventUpdate

        marker_shapes = protspace.reader.get_marker_shape(selected_feature)
        if selected_value in marker_shapes:
            return marker_shapes[selected_value]
        else:
            return None  # No shape selected

    if protspace.pdb_dir:

        @app.callback(
            Output("ngl-molecule-viewer", "data"),
            Input("protein-search-dropdown", "value"),
        )
        def update_protein_structure_info(selected_proteins):
            if not selected_proteins:
                raise PreventUpdate

            data_list = []
            for protein_id in selected_proteins:
                protein_id_underscore = protein_id.replace(".", "_")
                data_structure = ngl_parser.get_data(
                    data_path=protspace.pdb_dir + "/",
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

        projection_info = protspace.reader.get_projection_info(
            selected_projection
        )
        is_3d = projection_info["dimensions"] == 3

        fig = go.Figure(figure)
        return save_plot(fig, is_3d, width, height)
