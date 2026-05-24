from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

import fitz  # PyMuPDF


def find_index_csv(kb_dir: Path) -> Path:
    for path in kb_dir.glob("*.csv"):
        with path.open(encoding="utf-8-sig") as f:
            header = f.readline()
        if "doc_id" in header and "rel_path" in header and "abs_path" in header:
            return path
    raise FileNotFoundError("未找到资料总索引 CSV。")


def parse_pages(value: str, page_count: int) -> list[int]:
    pages: set[int] = set()
    for part in value.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start, end = [int(x) for x in part.split("-", 1)]
            pages.update(range(start, end + 1))
        else:
            pages.add(int(part))
    bad = [p for p in pages if p < 1 or p > page_count]
    if bad:
        raise ValueError(f"页码超出范围：{bad}；该文件页数为 {page_count}")
    return sorted(pages)


def safe_name(value: str) -> str:
    value = re.sub(r"[^\w\u4e00-\u9fff.-]+", "_", value, flags=re.UNICODE)
    return value[:80].strip("._") or "page"


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Render selected PDF pages from a knowledge-base index.")
    parser.add_argument("--kb", required=True, help="Knowledge-base directory containing 资料总索引.csv.")
    parser.add_argument("--doc-id", required=True, help="Document ID, for example D057.")
    parser.add_argument("--pages", required=True, help="Page list such as 1,2,5-7. Pages are 1-based.")
    parser.add_argument("--zoom", type=float, default=2.0, help="Render zoom. Default: 2.0.")
    args = parser.parse_args()

    kb_dir = Path(args.kb).resolve()
    with find_index_csv(kb_dir).open(encoding="utf-8-sig") as f:
        records = {row["doc_id"]: row for row in csv.DictReader(f)}

    record = records.get(args.doc_id)
    if record is None:
        raise KeyError(f"未找到文档编号：{args.doc_id}")
    if record["ext"].lower() != ".pdf":
        raise ValueError(f"{args.doc_id} 不是 PDF 文件。")

    pdf_path = Path(record["abs_path"])
    if not pdf_path.exists():
        raise FileNotFoundError(f"原始 PDF 不存在：{record['rel_path']}")

    out_dir = kb_dir / "rendered_pages"
    out_dir.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(str(pdf_path))
    matrix = fitz.Matrix(args.zoom, args.zoom)
    stem = safe_name(record["title"])
    for page_no in parse_pages(args.pages, doc.page_count):
        pix = doc.load_page(page_no - 1).get_pixmap(matrix=matrix, alpha=False)
        out = out_dir / f"{args.doc_id}_{stem}_p{page_no:03d}.png"
        pix.save(str(out))
        print(out)
    doc.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
