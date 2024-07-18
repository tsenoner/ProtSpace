from dash import dcc, html
from dash_bio import NglMoleculeViewer


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
                style={"width": "48vw", "display": "inline-block"},
            ),
        ], style={"display": "flex", "justifyContent": "space-between"}),
    ]

    if app.pdb_dir:
        plot_layout = html.Div([
            html.Div([
                dcc.Graph(id="scatter-plot", style={"height": "100%"}, responsive=True)
            ], style={
                "border": "2px solid #dddddd",
                "height": "calc(100vh - 200px)",
                "width": "48vw",
                "display": "inline-block",
                "marginBottom": "20px",
            }),
            html.Div([
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
            }),
        ], style={"display": "flex", "justifyContent": "space-between"})
    else:
        plot_layout = html.Div([
            dcc.Graph(id="scatter-plot", style={"height": "calc(100vh - 200px)"}, responsive=True)
        ], style={
            "border": "2px solid #dddddd",
            "height": "calc(100vh - 200px)",
            "marginBottom": "20px",
        })

    common_layout.append(plot_layout)

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