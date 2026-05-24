from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from pypdf import PdfReader

try:
    import fitz  # PyMuPDF
except Exception:  # pragma: no cover
    fitz = None

try:
    from PIL import Image
except Exception:  # pragma: no cover
    Image = None


TOPIC_RULES = [
    ("温度-热电偶", ["热电偶", "thermocouple", "60584", "16839", "e230", "e220", "e2846", "jjg 141", "jjf 1637"]),
    ("温度-热电阻/铂电阻", ["热电阻", "铂电阻", "platinum resistance", "rtd", "60751", "30121", "e1137", "e2593", "e644"]),
    ("温度-高温测量", ["ams2750", "ams 2750", "高温测量", "tus", "sat"]),
    ("压力/差压变送器", ["压力变送器", "差压变送器", "pmp", "pmd", "eja", "jjg 882"]),
    ("流量-差压式", ["差压式流量", "iso 5167", "2624", "孔板", "喷嘴", "文丘里", "楔形", "锥形", "jjg640"]),
    ("流量-涡街", ["涡街", "vortex"]),
    ("流量-科里奥利", ["科里奥利", "coriolis", "mass flow", "jjg 1038"]),
    ("流量-电磁", ["电磁流量", "magnetic", "axg"]),
    ("法兰/管件/管螺纹", ["法兰", "flange", "b16.5", "b16.9", "hgt", "hg/t", "管螺纹", "pipe thread", "iso 228"]),
    ("仪表安装/护套/热套管", ["thermowell", "tw20", "ptc 19.3", "护套", "套管"]),
    ("温度变送器", ["温度变送器", "temperature transmitter", "tmt", "yta", "5333", "5334"]),
]


@dataclass
class Record:
    doc_id: str
    title: str
    rel_path: str
    abs_path: str
    ext: str
    source_group: str
    size_bytes: int
    modified_time: str
    page_count: int | str
    text_chars: int
    extraction_status: str
    topics: str
    standard_or_model: str
    text_file: str
    notes: str


def safe_text(value: str) -> str:
    value = value.replace("\x00", "")
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r"\n{4,}", "\n\n\n", value)
    return value.strip()


def snippet(value: str, length: int = 180) -> str:
    return re.sub(r"\s+", " ", value).strip()[:length]


def rel(root: Path, path: Path) -> str:
    return str(path.relative_to(root)).replace("\\", "/")


def infer_source_group(root: Path, path: Path) -> str:
    parts = path.relative_to(root).parts
    return parts[0] if parts else ""


def infer_standard_or_model(title: str) -> str:
    patterns = [
        r"(GB[/／]?\s*T?\s*\d+(?:[.\-]\d+)*)",
        r"(GBT\s*\d+(?:[.\-]\d+)*)",
        r"(JJF\s*\d+(?:-\d+)?)",
        r"(JJG\s*\d+(?:-\d+)?)",
        r"(IEC\s*\d+(?:-\d+)*)",
        r"(ISO\s*\d+(?:-\d+)*)",
        r"(ASTM\s*[A-Z]\s*\d+(?:[/\-][A-Z]?\d+)*)",
        r"(ASME\s*B\d+(?:\.\d+)*)",
        r"(AMS\s*2750[A-Z]?)",
        r"(HG[/／]?\s*T\s*\d+(?:-\d+)?)",
        r"\b(PMP\d+[A-Z]?|PMD\d+[A-Z]?|EJA\d+[A-Z]?|TMT\d+|YTA\d+|TR\d+(?:-\d+)?|TW\d+|AXG|EE\d+)\b",
    ]
    matches: list[str] = []
    normalized = title.replace("\u00a0", " ")
    for pattern in patterns:
        matches.extend(re.findall(pattern, normalized, flags=re.IGNORECASE))
    return "; ".join(dict.fromkeys(str(m).upper().strip() for m in matches))


def infer_topics(title: str, sample: str) -> list[str]:
    haystack = f"{title}\n{sample}".lower()
    topics = [topic for topic, keys in TOPIC_RULES if any(key.lower() in haystack for key in keys)]
    return topics or ["未分类-待人工确认"]


def collect_sources(root: Path, source_dirs: list[str]) -> list[Path]:
    files: list[Path] = []
    for item in source_dirs:
        source = root / item
        if source.exists():
            files.extend(p for p in source.rglob("*") if p.is_file())
    return sorted(
        [p for p in files if p.suffix.lower() in {".pdf", ".png", ".jpg", ".jpeg"}],
        key=lambda p: rel(root, p).lower(),
    )


def extract_pdf(path: Path, doc_id: str) -> tuple[int, int, list[dict], str, str]:
    pages: list[dict] = []
    notes: list[str] = []
    fitz_doc = None
    reader = None

    try:
        reader = PdfReader(str(path))
        page_count = len(reader.pages)
    except Exception as exc:
        if fitz is None:
            return 0, 0, pages, "error", f"PDF 打开失败：{exc!r}"
        try:
            fitz_doc = fitz.open(str(path))
            page_count = fitz_doc.page_count
            notes.append(f"pypdf 打开失败，已使用 PyMuPDF：{exc!r}")
        except Exception as fitz_exc:
            return 0, 0, pages, "error", f"PDF 打开失败：{exc!r}；PyMuPDF 失败：{fitz_exc!r}"
    else:
        if fitz is not None:
            try:
                fitz_doc = fitz.open(str(path))
            except Exception as exc:
                notes.append(f"PyMuPDF 兜底打开失败：{exc!r}")

    total_chars = 0
    for idx in range(1, page_count + 1):
        method = "pypdf"
        text = ""
        try:
            if reader is not None:
                text = reader.pages[idx - 1].extract_text() or ""
        except Exception as exc:
            notes.append(f"第 {idx} 页 pypdf 抽取失败：{exc!r}")

        if fitz_doc is not None and len(safe_text(text)) < 20:
            try:
                fitz_text = fitz_doc.load_page(idx - 1).get_text("text") or ""
                if len(safe_text(fitz_text)) > len(safe_text(text)):
                    text = fitz_text
                    method = "pymupdf"
            except Exception as exc:
                notes.append(f"第 {idx} 页 PyMuPDF 抽取失败：{exc!r}")

        text = safe_text(text)
        total_chars += len(text)
        pages.append(
            {
                "doc_id": doc_id,
                "page": idx,
                "text_chars": len(text),
                "status": "ok" if text else "empty",
                "method": method if text else "",
                "snippet": snippet(text),
                "text": text,
            }
        )

    if fitz_doc is not None:
        fitz_doc.close()

    avg_chars = total_chars / page_count if page_count else 0
    status = "no_text" if total_chars == 0 else "low_text" if avg_chars < 80 else "ok"
    return page_count, total_chars, pages, status, "；".join(notes)


def inspect_image(path: Path) -> tuple[str, str]:
    if Image is None:
        return "image", "图片资料；Pillow 不可用，未读取尺寸，未进行 OCR。"
    try:
        with Image.open(path) as img:
            return "image", f"图片尺寸：{img.width}x{img.height}；未进行 OCR。"
    except Exception as exc:
        return "error", f"图片读取失败：{exc!r}"


def write_outputs(kb_dir: Path, records: list[Record], page_rows: list[dict]) -> None:
    (kb_dir / "text").mkdir(parents=True, exist_ok=True)

    with (kb_dir / "资料总索引.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(Record.__annotations__.keys()))
        writer.writeheader()
        for record in records:
            writer.writerow(record.__dict__)

    with (kb_dir / "页级索引.csv").open("w", newline="", encoding="utf-8-sig") as f:
        fieldnames = ["doc_id", "page", "text_chars", "status", "method", "snippet"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in page_rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})

    with (kb_dir / "chunks.jsonl").open("w", encoding="utf-8") as f:
        for row in page_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    lines = ["# 资料总索引", "", "| 编号 | 分类 | 主题 | 标准/型号 | 页数 | 状态 | 原始文件 |", "|---|---|---|---|---:|---|---|"]
    for record in records:
        lines.append(f"| {record.doc_id} | {record.source_group} | {record.topics} | {record.standard_or_model} | {record.page_count} | {record.extraction_status} | {record.rel_path} |")
    (kb_dir / "资料总索引.md").write_text("\n".join(lines), encoding="utf-8")

    by_topic: dict[str, list[Record]] = {}
    for record in records:
        for topic in record.topics.split("; "):
            by_topic.setdefault(topic, []).append(record)
    topic_lines = ["# 主题索引", ""]
    for topic in sorted(by_topic):
        topic_lines.extend([f"## {topic}", ""])
        for record in by_topic[topic]:
            topic_lines.append(f"- {record.doc_id} | {record.standard_or_model or record.title} | {record.rel_path} | {record.extraction_status}")
        topic_lines.append("")
    (kb_dir / "主题索引.md").write_text("\n".join(topic_lines), encoding="utf-8")

    warning_lines = [
        "# 抽取告警与需确认项",
        "",
        "| 编号 | 状态 | 页数 | 文本字符数 | 原始文件 | 备注 |",
        "|---|---|---:|---:|---|---|",
    ]
    for record in records:
        if record.extraction_status not in {"ok", "image"}:
            warning_lines.append(f"| {record.doc_id} | {record.extraction_status} | {record.page_count} | {record.text_chars} | {record.rel_path} | {record.notes} |")
    (kb_dir / "抽取告警与需确认项.md").write_text("\n".join(warning_lines), encoding="utf-8")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Build a searchable instrumentation source-document knowledge base.")
    parser.add_argument("--root", default=".", help="Project root containing source directories.")
    parser.add_argument("--out", required=True, help="Output knowledge-base directory.")
    parser.add_argument("--sources", nargs="*", default=["00_客户需求", "01_产品样本与技术资料", "02_标准与计量规程", "03_法兰和管道标准"], help="Source directories relative to root.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    kb_dir = Path(args.out).resolve()
    text_dir = kb_dir / "text"
    text_dir.mkdir(parents=True, exist_ok=True)

    records: list[Record] = []
    page_rows: list[dict] = []

    for idx, path in enumerate(collect_sources(root, args.sources), start=1):
        doc_id = f"D{idx:03d}"
        rel_path = rel(root, path)
        title = path.stem
        text_file = f"text/{doc_id}_{hashlib.sha1(rel_path.encode('utf-8')).hexdigest()[:8]}.txt"

        if path.suffix.lower() == ".pdf":
            page_count, text_chars, pages, status, notes = extract_pdf(path, doc_id)
            sample = "\n".join(page["snippet"] for page in pages[:5])
            for page in pages:
                row = {"source_path": rel_path, "title": title, **page}
                page_rows.append(row)
            (kb_dir / text_file).write_text(
                "\n".join([f"# {doc_id} {title}", f"原始文件：{rel_path}", ""] + [f"\n--- PAGE {p['page']} ---\n{p['text']}" for p in pages]),
                encoding="utf-8",
            )
        else:
            page_count, text_chars, pages = "", 0, []
            status, notes = inspect_image(path)
            sample = notes
            text_file = ""

        record = Record(
            doc_id=doc_id,
            title=title,
            rel_path=rel_path,
            abs_path=str(path),
            ext=path.suffix.lower(),
            source_group=infer_source_group(root, path),
            size_bytes=path.stat().st_size,
            modified_time=datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
            page_count=page_count,
            text_chars=text_chars,
            extraction_status=status,
            topics="; ".join(infer_topics(title, sample)),
            standard_or_model=infer_standard_or_model(title),
            text_file=text_file,
            notes=notes,
        )
        records.append(record)
        print(f"{doc_id} {status:8} pages={page_count} chars={text_chars} {rel_path}")

    write_outputs(kb_dir, records, page_rows)
    print(f"知识库已生成：{kb_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
