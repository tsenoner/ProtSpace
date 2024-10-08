from dash import dcc, html
from dash_bio import NglMoleculeViewer
import dash_daq as daq
from dash_iconify import DashIconify

from .config import MARKER_SHAPES
from .data_loader import JsonReader


def create_layout(app):
    """Create the layout for the Dash application."""
    dropdown_style = {"width": "24vw", "marginRight": "10px"}

    # Get default data if available
    default_json_data = app.get_default_json_data()
    if default_json_data:
        reader = JsonReader(default_json_data)
        features = sorted(reader.get_all_features())
        projections = sorted(reader.get_projection_names())
        protein_ids = sorted(reader.get_protein_ids())

        feature_options = [{"label": feature, "value": feature} for feature in features]
        projection_options = [{"label": proj, "value": proj} for proj in projections]
        protein_options = [{"label": pid, "value": pid} for pid in protein_ids]

        # Select the first feature and projection
        first_feature = features[0] if features else None
        first_projection = projections[0] if projections else None
    else:
        feature_options = []
        projection_options = []
        protein_options = []
        first_feature = None
        first_projection = None

    # Get PDB files data if available
    pdb_files_data = app.get_pdb_files_data()

    common_layout = [
        html.H1(
            "ProtSpace",
            style={"textAlign": "center", "margin": "0", "padding": "10px 0"},
        ),
        html.Div(
            [
                html.Div(
                    [
                        dcc.Dropdown(
                            id="feature-dropdown",
                            options=feature_options,
                            value=first_feature,
                            placeholder="Select a feature",
                            style={
                                "width": "200px",
                                "marginRight": "10px",
                                "minWidth": "150px",
                            },
                        ),
                        dcc.Dropdown(
                            id="projection-dropdown",
                            options=projection_options,
                            value=first_projection,
                            placeholder="Select a projection",
                            style={
                                "width": "200px",
                                "marginRight": "10px",
                                "minWidth": "150px",
                            },
                        ),
                        dcc.Dropdown(
                            id="protein-search-dropdown",
                            options=protein_options,
                            placeholder="Search for protein identifiers",
                            multi=True,
                            style={
                                "flexGrow": "1",
                                "marginRight": "10px",
                                "minWidth": "150px",
                            },
                        ),
                    ],
                    style={
                        "display": "flex",
                        "flexGrow": "1",
                        "flexWrap": "nowrap",
                        "alignItems": "center",
                    },
                ),
                html.Div(
                    [
                        html.Button(
                            DashIconify(
                                icon="material-symbols:download", width=24, height=24
                            ),
                            id="download-json-button",
                            title="Download JSON",
                            style={"marginLeft": "5px"},
                        ),
                        dcc.Download(id="download-json"),
                        dcc.Upload(
                            id="upload-json",
                            children=html.Button(
                                DashIconify(
                                    icon="material-symbols:upload", width=24, height=24
                                ),
                                title="Upload JSON",
                                style={"marginLeft": "5px"},
                            ),
                            multiple=False,
                        ),
                        dcc.Upload(
                            id="upload-pdb-zip",
                            children=html.Button(
                                DashIconify(
                                    icon="fa6-solid:file-zipper", width=24, height=24
                                ),
                                title="Upload PDB ZIP",
                                style={"marginLeft": "5px"},
                            ),
                            multiple=False,
                        ),
                        html.Button(
                            DashIconify(icon="carbon:settings", width=24, height=24),
                            id="settings-button",
                            title="Settings",
                            style={"marginLeft": "5px"},
                        ),
                    ],
                    style={
                        "display": "flex",
                        "flexWrap": "nowrap",
                        "alignItems": "center",
                    },
                ),
            ],
            style={
                "display": "flex",
                "flexWrap": "nowrap",
                "alignItems": "center",
                "marginBottom": "10px",
            },
        ),
        html.Div(
            [
                html.Div(
                    [
                        dcc.Graph(
                            id="scatter-plot", style={"height": "100%"}, responsive=True
                        )
                    ],
                    id="scatter-plot-div",
                    style={
                        "border": "2px solid #dddddd",
                        "height": "calc(100vh - 200px)",
                        "width": "100%",
                        "display": "inline-block",
                        "verticalAlign": "top",
                    },
                ),
                html.Div(
                    [
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
                    id="ngl-viewer-div",
                    style={
                        "border": "2px solid #dddddd",
                        "height": "calc(100vh - 200px)",
                        "width": "49%",
                        "display": "none",  # Hidden by default
                        "verticalAlign": "top",
                    },
                ),
                html.Div(
                    [
                        html.H4(
                            "Marker Style Settings", style={"marginBottom": "10px"}
                        ),
                        html.Div(
                            [
                                html.Label("Select Feature Value:"),
                                dcc.Dropdown(
                                    id="feature-value-dropdown",
                                    style={"marginBottom": "10px"},
                                ),
                            ]
                        ),
                        html.Div(
                            [
                                html.Label("Marker Color:"),
                                daq.ColorPicker(
                                    id="marker-color-picker",
                                    style={"marginBottom": "10px"},
                                ),
                            ]
                        ),
                        html.Div(
                            [
                                html.Label("Marker Shape:"),
                                dcc.Dropdown(
                                    id="marker-shape-dropdown",
                                    options=[
                                        {
                                            "label": shape.replace("-", " ").title(),
                                            "value": shape,
                                        }
                                        for shape in MARKER_SHAPES
                                    ],
                                    style={"marginBottom": "10px"},
                                ),
                            ]
                        ),
                        html.Button("Apply", id="apply-style-button"),
                    ],
                    id="marker-style-controller",
                    style={
                        "display": "none",
                        "width": "300px",
                        "padding": "20px",
                        "backgroundColor": "#f0f0f0",
                        "borderRadius": "5px",
                    },
                ),
            ],
            style={"display": "flex", "justifyContent": "space-between"},
        ),
        dcc.Store(id="json-data-store", data=default_json_data),
        dcc.Store(id="pdb-files-store", data=pdb_files_data),
    ]

    common_layout.append(
        html.Div(
            [
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
