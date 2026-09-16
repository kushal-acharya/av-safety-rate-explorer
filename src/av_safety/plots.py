"""Pure DataFrame-to-Plotly figure builders."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go


def rates_figure(table: pd.DataFrame, unit: int, confidence: float) -> go.Figure:
    """Plot rates with horizontal intervals; mark zero-count upper bounds explicitly."""
    shown = table.rate.where(table.events > 0, table.upper) * unit
    figure = go.Figure(
        go.Scatter(
            x=shown,
            y=table.group,
            mode="markers",
            marker={"color": ["#0a7d68" if k else "#c77a50" for k in table.events], "size": 10},
            error_x={
                "type": "data",
                "symmetric": False,
                "array": table.upper * unit - shown,
                "arrayminus": shown - table.lower * unit,
            },
            text=table.method,
            hovertemplate="%{y}: %{x:.4g}<br>%{text}<extra></extra>",
        )
    )
    figure.update_layout(
        title=f"Disengagement rates · {confidence:.0%} confidence intervals",
        xaxis_title=f"Disengagements per {unit:,} miles",
        yaxis_title="Group",
        template="plotly_white",
        height=max(340, len(table) * 42),
        margin={"l": 20, "r": 25, "t": 60, "b": 40},
    )
    return figure


def power_figure(table: pd.DataFrame, target: float) -> go.Figure:
    """Plot normal-approximate power against total exposure across both arms."""
    figure = go.Figure(
        go.Scatter(
            x=table.miles, y=table.power, mode="lines", line={"color": "#0a7d68"}, fill="tozeroy"
        )
    )
    figure.add_hline(y=target, line_dash="dot", line_color="#c77a50")
    figure.update_layout(
        title="Power vs total exposure",
        xaxis_title="Total miles · both arms",
        yaxis_title="Power",
        yaxis_tickformat=".0%",
        template="plotly_white",
    )
    return figure
