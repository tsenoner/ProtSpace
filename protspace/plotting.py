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
        category_orders={
            selected_feature: sorted(df[selected_feature].unique())
        },
    )

    fig.update_traces(
        marker=dict(
            size=DEFAULT_MARKER_SIZE,
            line=dict(width=DEFAULT_LINE_WIDTH, color="black"),
        )
    )

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
                    size=HIGHLIGHT_MARKER_SIZE,
                    color=HIGHLIGHT_COLOR,
                    line=dict(
                        width=HIGHLIGHT_LINE_WIDTH, color=HIGHLIGHT_BORDER_COLOR
                    ),
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
        uirevision="constant",
    )
    return fig


def create_3d_plot(
    df: pd.DataFrame,
    selected_feature: str,
    selected_proteins: List[str],
) -> go.Figure:
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
        category_orders={
            selected_feature: sorted(df[selected_feature].unique())
        },
    )

    fig.update_traces(
        marker=dict(
            size=DEFAULT_MARKER_SIZE // 1.5,
            line=dict(width=DEFAULT_LINE_WIDTH, color="rgba(0, 0, 0, 0.1)"),
        )
    )

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
                    size=HIGHLIGHT_MARKER_SIZE,
                    color=HIGHLIGHT_COLOR,
                    line=dict(
                        width=HIGHLIGHT_LINE_WIDTH, color=HIGHLIGHT_BORDER_COLOR
                    ),
                ),
                hoverinfo="text",
                hovertext=f"{selected_feature}={feature_value}<br>identifier={identifier}",
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
    bounds = {
        dim: [df[dim].min() * 1.05, df[dim].max() * 1.05]
        for dim in ["x", "y", "z"]
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
    if is_3d:
        if filename:
            fig.write_html(filename, include_plotlyjs="cdn")
        else:
            buffer = io.StringIO()
            fig.write_html(buffer, include_plotlyjs="cdn")
            buffer.seek(0)
            return dcc.send_bytes(
                buffer.getvalue().encode(), "protspace_3d_plot.html"
            )
    else:
        if width is None or height is None:
            raise ValueError(
                "Width and height must be provided for 2D plots"
            )

        # Base sizes for font and marker at a reference height
        base_font_size = 14
        base_marker_size = 10  # Adjust based on your default marker size
        base_height = 600  # Reference height

        # Calculate scaling factors
        scaling_factor = height / base_height

        # Adjust font size proportionally
        font_size = base_font_size * scaling_factor

        # Adjust marker size proportionally
        legend_marker_size = base_marker_size * scaling_factor

        # Optional: Set minimum and maximum values to avoid extremes
        font_size = max(10, min(font_size, 30))
        legend_marker_size = max(5, min(legend_marker_size, 20))

        # Create a copy of the figure to modify for saving
        fig_to_save = fig

        # Update the legend for the saved version
        fig_to_save.update_layout(
            legend=dict(
                font=dict(size=font_size),
                itemsizing='constant',
            )
        )

        # Loop over each trace in the original figure
        for trace in fig.data:
            # Add the original trace without the legend
            original_trace = trace
            original_trace.showlegend = False  # Hide original trace from legend
            fig_to_save.add_trace(original_trace)

            # Create a dummy trace for the legend
            legend_trace = go.Scatter(
                x=[None],  # No data point
                y=[None],
                mode=trace.mode,
                name=trace.name,
                marker=dict(
                    color=trace.marker.color,
                    size=legend_marker_size,
                    symbol=trace.marker.symbol,
                    line=eval(trace.marker.line.to_json()),
                ),
                showlegend=True,
                legendgroup=trace.legendgroup,
            )
            fig_to_save.add_trace(legend_trace)

        if filename:
            fig_to_save.write_image(filename, format="svg", width=width, height=height)
        else:
            buffer = io.BytesIO()
            fig_to_save.write_image(buffer, format="svg", width=width, height=height)
            buffer.seek(0)
            return dcc.send_bytes(buffer.getvalue(), "protspace_2d_plot.svg")

