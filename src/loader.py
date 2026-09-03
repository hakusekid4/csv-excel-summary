"""CSV / Excel ファイルを pandas の DataFrame として読み込む。

ポイント:
- CSV は文字コードが UTF-8 か Shift_JIS(cp932)か分からないので、順番に試す。
- Excel は複数シートがあり得るので、シート名一覧を返す関数も用意する。
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import BinaryIO

import pandas as pd

# CSV で試す文字コードの順番。Excel で保存した CSV は cp932(Shift_JIS)が多い。
CSV_ENCODINGS = ("utf-8-sig", "cp932", "utf-8")
CSV_SUFFIXES = {".csv", ".txt", ".tsv"}
EXCEL_SUFFIXES = {".xlsx", ".xlsm", ".xls"}


class LoadError(Exception):
    """読み込みに失敗したときに、画面に出せる日本語メッセージを持つ例外。"""


def _read_bytes(source: str | Path | BinaryIO | bytes) -> bytes:
    """パス・ファイルオブジェクト・bytes のどれが来ても bytes にそろえる。"""
    if isinstance(source, bytes):
        return source
    if isinstance(source, (str, Path)):
        return Path(source).read_bytes()
    data = source.read()
    if hasattr(source, "seek"):
        source.seek(0)  # Streamlit のアップロードファイルは読み直せるよう先頭に戻す
    return data


def detect_kind(filename: str) -> str:
    """拡張子からファイル種別("csv" / "excel")を返す。対応外なら LoadError。"""
    suffix = Path(filename).suffix.lower()
    if suffix in CSV_SUFFIXES:
        return "csv"
    if suffix in EXCEL_SUFFIXES:
        return "excel"
    raise LoadError(f"対応していないファイル形式です: {suffix or '(拡張子なし)'}。CSV か Excel を選んでください。")


def list_sheets(source: str | Path | BinaryIO | bytes) -> list[str]:
    """Excel ファイルのシート名一覧を返す。"""
    data = _read_bytes(source)
    try:
        with pd.ExcelFile(BytesIO(data)) as xls:
            return [str(name) for name in xls.sheet_names]
    except Exception as e:
        raise LoadError(f"Excel ファイルを開けませんでした: {e}") from e


def read_csv(source: str | Path | BinaryIO | bytes) -> pd.DataFrame:
    """CSV を読み込む。UTF-8 → Shift_JIS の順に試す。区切り文字はカンマ・タブを自動判定。"""
    data = _read_bytes(source)
    last_error: Exception | None = None
    for enc in CSV_ENCODINGS:
        try:
            text = data.decode(enc)
        except UnicodeDecodeError as e:
            last_error = e
            continue
        sep = "\t" if text.count("\t") > text.count(",") else ","
        try:
            return pd.read_csv(BytesIO(text.encode("utf-8")), sep=sep)
        except Exception as e:  # noqa: BLE001
            last_error = e
            continue
    raise LoadError(f"CSV を読み込めませんでした(文字コードや形式を確認してください): {last_error}")


def read_excel(source: str | Path | BinaryIO | bytes, sheet: str | int = 0) -> pd.DataFrame:
    """Excel の 1 シートを読み込む。sheet はシート名か 0 始まりの番号。"""
    data = _read_bytes(source)
    try:
        return pd.read_excel(BytesIO(data), sheet_name=sheet)
    except ValueError as e:
        raise LoadError(f"シート「{sheet}」を読み込めませんでした: {e}") from e
    except Exception as e:
        raise LoadError(f"Excel を読み込めませんでした: {e}") from e


def load_table(
    source: str | Path | BinaryIO | bytes,
    filename: str | None = None,
    sheet: str | int = 0,
) -> pd.DataFrame:
    """ファイル種別を自動判定して DataFrame を返す。

    引数:
        source: ファイルパス、または Streamlit のアップロードファイルなど
        filename: source がパスでない場合に拡張子判定に使う名前
        sheet: Excel のときに読むシート
    戻り値:
        空行・空列を除いた DataFrame
    """
    name = filename or (str(source) if isinstance(source, (str, Path)) else "")
    kind = detect_kind(name)
    df = read_csv(source) if kind == "csv" else read_excel(source, sheet)
    df = df.dropna(how="all").dropna(axis=1, how="all")
    if df.empty:
        raise LoadError("データが空でした。中身のあるファイルを選んでください。")
    df.columns = [str(c).strip() for c in df.columns]
    return df.reset_index(drop=True)
