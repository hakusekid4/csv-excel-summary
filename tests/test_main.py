"""CLI(src/main.py)のテスト: サンプルと同じ形のデータで Excel ができること。"""

from io import BytesIO

import pandas as pd
import pytest

from src.loader import LoadError
from src.main import run


def test_cli_creates_excel(tmp_path, sales_df) -> None:
    src = tmp_path / "in.csv"
    sales_df.to_csv(src, index=False)
    out = run([str(src), "--group", "店舗", "--value", "金額", "--date", "日付", "--out", str(tmp_path / "o.xlsx")])
    with pd.ExcelFile(BytesIO(out.read_bytes())) as xls:
        assert xls.sheet_names == ["項目別集計", "期間別推移", "元データ"]


def test_cli_unknown_column(tmp_path, sales_df) -> None:
    src = tmp_path / "in.csv"
    sales_df.to_csv(src, index=False)
    with pytest.raises(LoadError):
        run([str(src), "--group", "ない列", "--value", "金額"])
