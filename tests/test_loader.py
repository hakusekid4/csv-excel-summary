"""loader.py のテスト: CSV(UTF-8 / Shift_JIS)、Excel、エラー。"""

import pandas as pd
import pytest

from src.loader import LoadError, detect_kind, list_sheets, load_table


def test_detect_kind() -> None:
    assert detect_kind("a.csv") == "csv"
    assert detect_kind("A.XLSX") == "excel"
    with pytest.raises(LoadError):
        detect_kind("a.pdf")


def test_load_csv_utf8_and_cp932(tmp_path) -> None:
    df = pd.DataFrame({"店舗": ["渋谷店"], "金額": [100]})
    utf8 = tmp_path / "u.csv"
    sjis = tmp_path / "s.csv"
    df.to_csv(utf8, index=False, encoding="utf-8-sig")
    df.to_csv(sjis, index=False, encoding="cp932")
    for path in (utf8, sjis):
        loaded = load_table(path)
        assert list(loaded.columns) == ["店舗", "金額"]
        assert loaded.iloc[0]["店舗"] == "渋谷店"


def test_load_tsv(tmp_path) -> None:
    path = tmp_path / "t.tsv"
    path.write_text("a\tb\n1\t2\n", encoding="utf-8")
    assert list(load_table(path).columns) == ["a", "b"]


def test_load_excel_with_sheets(tmp_path) -> None:
    path = tmp_path / "x.xlsx"
    with pd.ExcelWriter(path) as w:
        pd.DataFrame({"x": [1]}).to_excel(w, sheet_name="一枚目", index=False)
        pd.DataFrame({"y": [2]}).to_excel(w, sheet_name="二枚目", index=False)
    assert list_sheets(path) == ["一枚目", "二枚目"]
    assert list(load_table(path).columns) == ["x"]
    assert list(load_table(path, sheet="二枚目").columns) == ["y"]


def test_load_from_bytes_with_filename() -> None:
    data = b"a,b\n1,2\n"
    df = load_table(data, filename="memo.csv")
    assert df.shape == (1, 2)


def test_empty_file_raises(tmp_path) -> None:
    path = tmp_path / "e.csv"
    path.write_text("a,b\n", encoding="utf-8")
    with pytest.raises(LoadError):
        load_table(path)
