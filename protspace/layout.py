from dash import dcc, html
from dash_bio import NglMoleculeViewer
import dash_daq as daq
from dash_iconify import DashIconify

from .utils import MARKER_SHAPES

def create_layout(app):
    common_layout = [
        html.H1("ProtSpace", style={"textAlign": "center", "margin": "0", "padding": "10px 0"}),
        html.Div([
            dcc.Dropdown(
                id="feature-dropdown",
                options=[{"label": feature, "value": feature} for feature in app.features],
                value=app.features[0],
                placeholder="Select a feature",
                style={"width": "24vw", "display": "inline-block"},
            ),
            dcc.Dropdown(
                id="projection-dropdown",
                options=[{"label": proj, "value": proj} for proj in app.projections],
                value=app.projections[0],
                placeholder="Select a projection",
                style={"width": "24vw", "display": "inline-block"},
            ),
            dcc.Dropdown(
                id="protein-search-dropdown",
                options=[{"label": pid, "value": pid} for pid in app.protein_ids],
                value=[],
                placeholder="Search for protein identifiers",
                multi=True,
                style={"width": "40vw", "display": "inline-block"},
            ),
            html.Button(
                DashIconify(icon="material-symbols:download", width=24, height=24),
                id="download-json-button",
                style={"marginLeft": "10px"},
                title="Download JSON",
            ),
            dcc.Download(id="download-json"),
            dcc.Upload(
                id='upload-json',
                children=html.Button(
                    DashIconify(icon="material-symbols:upload", width=24, height=24),
                    style={"marginLeft": "10px"},
                    title="Upload JSON",
                ),
                multiple=False
            ),
            html.Button(
                DashIconify(icon="carbon:settings", width=24, height=24),
                id="settings-button",
                style={"marginLeft": "10px"},
            ),
        ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "center"}),
        html.Div([
            html.Div([
                dcc.Graph(id="scatter-plot", style={"height": "100%"}, responsive=True)
            ], style={
                "border": "2px solid #dddddd",
                "height": "calc(100vh - 200px)",
                "width": "100%",
                "display": "inline-block",
                "marginBottom": "20px",
            }),
            html.Div([
                html.H4("Marker Style Settings", style={"marginBottom": "10px"}),
                html.Div([
                    html.Label("Select Feature Value:"),
                    dcc.Dropdown(id="feature-value-dropdown", style={"marginBottom": "10px"}),
                ]),
                html.Div([
                    html.Label("Marker Color:"),
                    daq.ColorPicker(id="marker-color-picker", style={"marginBottom": "10px"}),
                ]),
                html.Div([
                    html.Label("Marker Shape:"),
                    dcc.Dropdown(
                        id="marker-shape-dropdown",
                        options=[{"label": shape.replace('-', ' ').title(), "value": shape} for shape in MARKER_SHAPES],
                        style={"marginBottom": "10px"},
                    ),
                ]),
                html.Button("Apply", id="apply-style-button"),
            ], id="marker-style-controller", style={"display": "none", "width": "300px", "padding": "20px", "backgroundColor": "#f0f0f0", "borderRadius": "5px"}),
        ], style={"display": "flex", "justifyContent": "space-between"}),
    ]

    if app.pdb_dir:
        common_layout.append(html.Div([
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
        ], style={
            "border": "2px solid #dddddd",
            "height": "calc(100vh - 200px)",
            "width": "48vw",
            "display": "inline-block",
            "marginBottom": "20px",
        }))

    common_layout.append(html.Div([
        html.Button("Download", id="download-button", n_clicks=0),
        dcc.Input(id="image-width", type="number", placeholder="Width", value=1600, style={"marginLeft": "10px"}),
        dcc.Input(id="image-height", type="number", placeholder="Height", value=1000, style={"marginLeft": "10px"}),
        dcc.Download(id="download-plot"),
    ], style={
        "display": "flex",
        "justifyContent": "center",
        "alignItems": "center",
        "height": "50px",
    }))

    return html.Div(common_layout, style={
        "display": "flex",
        "flexDirection": "column",
        "height": "100vh",
        "padding": "20px",
        "boxSizing": "border-box",
    })