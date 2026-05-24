# Local Knowledge Base Workflow

Use this workflow when the user asks to learn, index, organize, or build a searchable knowledge base from supplied standards, procedures, manuals, datasheets, or images.

## Build Principles

1. Do not move, delete, or overwrite original source documents.
2. Create a dated output folder, for example `04_知识库/YYYY-MM-DD_资料知识库_v1/`.
3. Generate indexes and extracted text that point back to original file paths.
4. Treat extracted text as a locating aid, not as a replacement for original standards or datasheets.
5. For scanned PDFs or images, create an extraction warning and use rendered pages or OCR/manual reading before citing details.

## Recommended Outputs

| Output | Purpose |
|---|---|
| `资料总索引.csv` | document ID, title, path, source group, size, pages, extraction status, topics |
| `资料总索引.md` | human-readable document list |
| `主题索引.md` | grouping by instrument type, standard family, or workflow |
| `text/` | extracted text files with page separators |
| `页级索引.csv` | page-level status, character count, extraction method, snippet |
| `chunks.jsonl` | machine-readable page chunks for later retrieval |
| `抽取告警与需确认项.md` | no-text, low-text, image-only, or error documents |
| `rendered_pages/` | PNG pages rendered from scanned PDFs for visual review |

## Extraction Status

- `ok`: text extraction is usable, but final conclusions still require source-document verification.
- `no_text`: no embedded text; treat as scanned PDF.
- `low_text`: only trivial text extracted; treat as scanned PDF.
- `image`: image file; no OCR unless separately performed.
- `error`: file could not be opened or parsed; list the error and use another method.

## Search Pattern

Use `rg` first:

```powershell
rg -n "accuracy|允差|允许误差|压力等级|直管段" "04_知识库/*/text"
rg -n "PMP71B|EJA110E|IEC 60751|ISO 5167" "04_知识库"
```

When a match is found, open the extracted text to locate page markers, then check the original PDF page. If no text is available, render pages to PNG and visually inspect them.

## Safety Boundary

Do not claim that the model, standard, certification, material, pressure class, Ex rating, or accuracy requirement is satisfied unless the source document or customer data supports it. Use `资料中未找到明确依据，需厂家确认` for unsupported claims.
