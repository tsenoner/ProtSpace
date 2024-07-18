import plotly.graph_objs as go
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from dash_bio.utils import ngl_parser

from .data_processing import prepare_dataframe
from .plotting import create_2d_plot, create_3d_plot, save_plot


def setup_callbacks(app, protspace):
    @app.callback(
        Output("scatter-plot", "figure"),
        [
            Input("projection-dropdown", "value"),
            Input("feature-dropdown", "value"),
            Input("protein-search-dropdown", "value"),
        ],
    )
    def update_graph(selected_projection, selected_feature, selected_proteins):
        df = prepare_dataframe(protspace.reader, selected_projection, selected_feature)
        projection_info = protspace.reader.get_projection_info(selected_projection)

        if projection_info["dimensions"] == 2:
            return create_2d_plot(df, selected_feature, selected_proteins)
        else:
            return create_3d_plot(df, selected_feature, selected_proteins)

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

        projection_info = protspace.reader.get_projection_info(selected_projection)
        is_3d = projection_info["dimensions"] == 3

        fig = go.Figure(figure)
        return save_plot(fig, is_3d, width, height)