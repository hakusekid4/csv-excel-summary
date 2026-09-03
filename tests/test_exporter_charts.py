"""exporter.py と charts.py のテスト。"""

from io import BytesIO

import pandas as pd
import pytest

from src.charts import bar_chart, line_chart
from src.exporter import to_excel_bytes


def test_to_excel_bytes_roundtrip() -> None:
    sheets = {"項目別集計": pd.DataFrame({"店舗": ["A"], "合計": [1]}), "bad[name]:x": pd.DataFrame({"a": [1]})}
    data = to_excel_bytes(sheets)
    with pd.ExcelFile(BytesIO(data)) as xls:
        assert xls.sheet_names == ["項目別集計", "badnamex"]
        assert pd.read_excel(xls, "項目別集計").iloc[0]["合計"] == 1


def test_to_excel_bytes_empty_raises() -> None:
    with pytest.raises(ValueError):
        to_excel_bytes({})


def test_charts_build_valid_spec() -> None:
    summary = pd.DataFrame({"店舗": ["A", "B"], "合計": [10, 5]})
    spec = bar_chart(summary, "店舗", "合計", "t").to_dict()
    assert spec["mark"]["type"] == "bar"
    trend = pd.DataFrame({"期間": ["2025-01", "2025-02"], "合計": [1, 2]})
    spec = line_chart(trend, "期間", "合計", "t").to_dict()
    assert "layer" in spec  # 線 + 点の 2 層
