import base64
import json

from dash import no_update
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from dash_bio.utils import ngl_parser
import plotly.graph_objs as go

from .data_processing import prepare_dataframe
from .plotting import create_2d_plot, create_3d_plot, save_plot
from .utils import NAN_COLOR
from .data_loader import JsonReader


def setup_callbacks(app, protspace):
    def get_reader(json_data):
        """Helper function to get JsonReader instance."""
        if json_data:
            return JsonReader(json_data)
        else:
            return None

    @app.callback(
        Output("json-data-store", "data"),
        [
            Input("upload-json", "contents"),
            State("upload-json", "filename"),
            State("json-data-store", "data"),
        ],
        prevent_initial_call=True,
    )
    def update_json_data(contents, filename, current_data):
        if contents is None:
            raise PreventUpdate

        content_type, content_string = contents.split(",")
        decoded = base64.b64decode(content_string)
        try:
            if "json" in filename:
                data = json.loads(decoded.decode("utf-8"))
                return data
            else:
                return no_update
        except Exception as e:
            print(f"Error loading JSON: {e}")
            return no_update

    @app.callback(
        [
            Output("feature-dropdown", "options"),
            Output("feature-dropdown", "value"),
            Output("projection-dropdown", "options"),
            Output("projection-dropdown", "value"),
            Output("protein-search-dropdown", "options"),
        ],
        [
            Input("json-data-store", "data"),
        ],
    )
    def update_dropdowns(json_data):
        if json_data is None:
            return [], None, [], None, []

        reader = get_reader(json_data)
        feature_options = [{"label": feature, "value": feature} for feature in sorted(reader.get_all_features())]
        projection_options = [{"label": proj, "value": proj} for proj in sorted(reader.get_projection_names())]
        protein_options = [{"label": pid, "value": pid} for pid in sorted(reader.get_protein_ids())]

        # Select the first feature and projection
        first_feature = reader.get_all_features()[0] if reader.get_all_features() else None
        first_projection = reader.get_projection_names()[0] if reader.get_projection_names() else None

        return (
            feature_options,
            first_feature,
            projection_options,
            first_projection,
            protein_options,
        )

    @app.callback(
        Output("scatter-plot", "figure"),
        [
            Input("projection-dropdown", "value"),
            Input("feature-dropdown", "value"),
            Input("protein-search-dropdown", "value"),
            Input("apply-style-button", "n_clicks"),
            State("json-data-store", "data"),
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
        json_data,
        selected_value,
        selected_color,
        selected_shape,
    ):
        if json_data is None or not selected_projection or not selected_feature:
            # Return a blank figure
            fig = go.Figure()
            fig.update_layout(
                xaxis=dict(visible=False),
                yaxis=dict(visible=False),
                plot_bgcolor="white",
                margin=dict(l=0, r=0, t=0, b=0),
            )
            return fig

        reader = JsonReader(json_data)

        # Update the changed values
        if n_clicks and selected_value:
            if selected_color:
                color_hex = selected_color.get('hex', '#000000')
                reader.update_feature_color(selected_feature, selected_value, color_hex)
            if selected_shape:
                reader.update_marker_shape(selected_feature, selected_value, selected_shape)
            # Update the JSON data in the store
            json_data = reader.get_data()

        df = prepare_dataframe(reader, selected_projection, selected_feature)
        feature_colors = reader.get_feature_colors(selected_feature)
        marker_shapes = reader.get_marker_shape(selected_feature)
        projection_info = reader.get_projection_info(selected_projection)

        # Choose the appropriate plotting function
        if projection_info.get("dimensions") == 2:
            fig = create_2d_plot(df, selected_feature, selected_proteins)
        else:
            fig = create_3d_plot(df, selected_feature, selected_proteins)

        # Apply styles
        for value in df[selected_feature].unique():
            marker_style = {}
            if value == "<NaN>":
                marker_style['color'] = NAN_COLOR
            else:
                color = feature_colors.get(value)
                shape = marker_shapes.get(value)
                if color:
                    marker_style['color'] = color
                if shape:
                    marker_style['symbol'] = shape

            if marker_style:
                fig.update_traces(marker=marker_style, selector=dict(name=str(value)))

        return fig

    @app.callback(
        Output("download-json", "data"),
        Input("download-json-button", "n_clicks"),
        State("json-data-store", "data"),
        prevent_initial_call=True,
    )
    def download_json(n_clicks, json_data):
        if n_clicks == 0 or json_data is None:
            raise PreventUpdate

        return dict(
            content=json.dumps(json_data, indent=2),
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
        [
            Input("feature-dropdown", "value"),
            State("json-data-store", "data"),
        ],
    )
    def update_feature_value_options(selected_feature, json_data):
        if selected_feature is None or json_data is None:
            return []
        reader = get_reader(json_data)
        unique_values = reader.get_unique_feature_values(selected_feature)
        return [{"label": str(val), "value": str(val)} for val in sorted(unique_values)]

    @app.callback(
        Output("marker-color-picker", "value"),
        [
            Input("feature-dropdown", "value"),
            Input("feature-value-dropdown", "value"),
            State("json-data-store", "data"),
        ],
    )
    def update_marker_color_picker(selected_feature, selected_value, json_data):
        if selected_feature is None or selected_value is None or json_data is None:
            raise PreventUpdate

        reader = get_reader(json_data)
        feature_colors = reader.get_feature_colors(selected_feature)
        if selected_value in feature_colors:
            return {"hex": feature_colors[selected_value]}
        else:
            # Default to black
            return {"hex": "#000000"}

    @app.callback(
        Output("marker-shape-dropdown", "value"),
        [
            Input("feature-dropdown", "value"),
            Input("feature-value-dropdown", "value"),
            State("json-data-store", "data"),
        ],
    )
    def update_marker_shape_dropdown(selected_feature, selected_value, json_data):
        if selected_feature is None or selected_value is None or json_data is None:
            raise PreventUpdate

        reader = get_reader(json_data)
        marker_shapes = reader.get_marker_shape(selected_feature)
        if selected_value in marker_shapes:
            return marker_shapes[selected_value]
        else:
            return None  # No shape selected

    if protspace.pdb_dir:

        @app.callback(
            Output("ngl-molecule-viewer", "data"),
            [
                Input("protein-search-dropdown", "value"),
                State("json-data-store", "data"),
            ],
        )
        def update_protein_structure_info(selected_proteins, json_data):
            if not selected_proteins or json_data is None:
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
        [
            State("scatter-plot", "figure"),
            State("projection-dropdown", "value"),
            State("image-width", "value"),
            State("image-height", "value"),
            State("json-data-store", "data"),
        ],
        prevent_initial_call=True,
    )
    def download_plot(n_clicks, figure, selected_projection, width, height, json_data):
        if n_clicks == 0 or json_data is None:
            raise PreventUpdate

        reader = JsonReader(json_data)
        projection_info = reader.get_projection_info(selected_projection)
        is_3d = projection_info["dimensions"] == 3

        fig = go.Figure(figure)
        return save_plot(fig, is_3d, width, height)
