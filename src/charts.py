"""グラフを作る。Altair(Streamlit 同梱)を使うので、ブラウザ上で日本語もホバー表示も問題なく動く。

配色の方針(読みやすさのため):
- 系列が 1 つなので単色(青)。虹色は使わない。
- 目盛線は薄いグレーにして、データより目立たせない。
"""

from __future__ import annotations

import altair as alt
import pandas as pd

SERIES_COLOR = "#2a78d6"  # データの色(青)
GRID_COLOR = "#e1e0d9"  # 目盛線
AXIS_COLOR = "#898781"  # 軸のラベル


def _base(chart: alt.Chart, title: str) -> alt.Chart:
    """全グラフ共通の見た目(タイトル、軸、目盛線)をそろえる。"""
    return (
        chart.properties(title=title, height=360)
        .configure_axis(gridColor=GRID_COLOR, labelColor=AXIS_COLOR, titleColor=AXIS_COLOR, domainColor=GRID_COLOR)
        .configure_view(strokeWidth=0)
        .configure_title(anchor="start", fontSize=14)
    )


def bar_chart(summary: pd.DataFrame, label_col: str, value_col: str, title: str = "") -> alt.Chart:
    """項目別の横棒グラフ。大きい順に上から並べ、ホバーで値を表示する。"""
    chart = (
        alt.Chart(summary)
        .mark_bar(color=SERIES_COLOR, cornerRadiusEnd=4, size=18)
        .encode(
            y=alt.Y(f"{label_col}:N", sort="-x", title=None),
            x=alt.X(f"{value_col}:Q", title=value_col, axis=alt.Axis(format=",.0f")),
            tooltip=[
                alt.Tooltip(f"{label_col}:N"),
                alt.Tooltip(f"{value_col}:Q", format=",.1f"),
            ],
        )
    )
    return _base(chart, title)


def line_chart(trend: pd.DataFrame, period_col: str, value_col: str, title: str = "") -> alt.Chart:
    """期間別の折れ線グラフ。点にホバーすると値が出る。"""
    base = alt.Chart(trend).encode(
        x=alt.X(f"{period_col}:O", title=None, axis=alt.Axis(labelAngle=-45)),
        y=alt.Y(f"{value_col}:Q", title=value_col, axis=alt.Axis(format=",.0f")),
        tooltip=[
            alt.Tooltip(f"{period_col}:O"),
            alt.Tooltip(f"{value_col}:Q", format=",.1f"),
        ],
    )
    line = base.mark_line(color=SERIES_COLOR, strokeWidth=2)
    points = base.mark_point(color=SERIES_COLOR, filled=True, size=64)
    return _base(line + points, title)
