import io
import itertools
from typing import Any, Dict, List, Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
from dash import dcc

from .config import (
    DEFAULT_LINE_WIDTH,
    DEFAULT_MARKER_SIZE,
    HIGHLIGHT_BORDER_COLOR,
    HIGHLIGHT_COLOR,
    HIGHLIGHT_LINE_WIDTH,
    HIGHLIGHT_MARKER_SIZE,
)


def create_2d_plot(
    df: pd.DataFrame,
    selected_feature: str,
    selected_proteins: List[str],
) -> go.Figure:
    """Create a 2D scatter plot."""
    fig = px.scatter(
        df,
        x="x",
        y="y",
        color=selected_feature,
        hover_data={
            "identifier": True,
            selected_feature: True,
            "x": False,
            "y": False,
        },
        category_orders={selected_feature: sorted(df[selected_feature].unique())},
    )

    fig.update_traces(
        marker=dict(
            size=DEFAULT_MARKER_SIZE,
            line=dict(width=DEFAULT_LINE_WIDTH, color="black"),
        )
    )

    if selected_proteins:
        selected_df = df[df["identifier"].isin(selected_proteins)]
        fig.add_trace(
            go.Scatter(
                x=selected_df["x"],
                y=selected_df["y"],
                mode="markers",
                marker=dict(
                    size=HIGHLIGHT_MARKER_SIZE,
                    color=HIGHLIGHT_COLOR,
                    line=dict(width=HIGHLIGHT_LINE_WIDTH, color=HIGHLIGHT_BORDER_COLOR),
                ),
                hoverinfo="skip",
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
        uirevision="constant",
    )
    return fig


def create_3d_plot(
    df: pd.DataFrame,
    selected_feature: str,
    selected_proteins: List[str],
) -> go.Figure:
    """Create a 3D scatter plot."""
    fig = px.scatter_3d(
        df,
        x="x",
        y="y",
        z="z",
        color=selected_feature,
        hover_data={
            "identifier": True,
            selected_feature: True,
            "x": False,
            "y": False,
            "z": False,
        },
        category_orders={selected_feature: sorted(df[selected_feature].unique())},
    )

    fig.update_traces(
        marker=dict(
            size=DEFAULT_MARKER_SIZE,
            line=dict(
                width=DEFAULT_LINE_WIDTH, color="black"
            ),  # "rgba(0, 0, 0, 0.1)"),
        )
    )

    if selected_proteins:
        selected_df = df[df["identifier"].isin(selected_proteins)]
        fig.add_trace(
            go.Scatter3d(
                x=selected_df["x"],
                y=selected_df["y"],
                z=selected_df["z"],
                mode="markers",
                marker=dict(
                    size=HIGHLIGHT_MARKER_SIZE,
                    color=HIGHLIGHT_COLOR,
                    line=dict(width=HIGHLIGHT_LINE_WIDTH, color=HIGHLIGHT_BORDER_COLOR),
                ),
                hoverinfo="skip",
                showlegend=False,
            )
        )

    fig.add_trace(create_bounding_box(df))
    fig.update_layout(
        scene=get_3d_scene_layout(df),
        margin=dict(l=0, r=0, t=0, b=0),
        uirevision="constant",
    )
    return fig


def create_bounding_box(df: pd.DataFrame) -> go.Scatter3d:
    """Create a bounding box for the 3D scatter plot."""
    bounds = {
        dim: [df[dim].min() * 1.05, df[dim].max() * 1.05] for dim in ["x", "y", "z"]
    }
    vertices = list(itertools.product(*bounds.values()))
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

    x = []
    y = []
    z = []
    for edge in edges:
        for vertex in edge:
            x.append(vertices[vertex][0])
            y.append(vertices[vertex][1])
            z.append(vertices[vertex][2])
        x.append(None)
        y.append(None)
        z.append(None)

    return go.Scatter3d(
        x=x,
        y=y,
        z=z,
        mode="lines",
        line=dict(color="black", width=1),
        hoverinfo="none",
        showlegend=False,
    )


def get_3d_scene_layout(df: pd.DataFrame) -> Dict[str, Any]:
    """Define the layout for the 3D scene."""
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


def save_plot(
    fig: go.Figure,
    is_3d: bool,
    width: Optional[int] = None,
    height: Optional[int] = None,
    filename: Optional[str] = None,
) -> Optional[Dict]:
    """Save the plot to a file or return it for download."""
    if is_3d:
        if filename:
            fig.write_html(filename, include_plotlyjs="cdn")
        else:
            buffer = io.StringIO()
            fig.write_html(buffer, include_plotlyjs="cdn")
            buffer.seek(0)
            return dcc.send_bytes(buffer.getvalue().encode(), "protspace_3d_plot.html")
    else:
        if width is None or height is None:
            raise ValueError("Width and height must be provided for 2D plots")

        # Adjust font size proportionally
        scaling_factor = height / 600
        font_size = max(10, min(14 * scaling_factor, 30))

        # Adjust marker size proportionally
        marker_size = max(5, min(10 * scaling_factor, 20))

        fig.update_layout(
            legend=dict(font=dict(size=font_size)),
        )
        fig.update_traces(marker=dict(size=marker_size))

        if filename:
            fig.write_image(filename, format="svg", width=width, height=height)
        else:
            buffer = io.BytesIO()
            fig.write_image(buffer, format="svg", width=width, height=height)
            buffer.seek(0)
            return dcc.send_bytes(buffer.getvalue(), "protspace_2d_plot.svg")
