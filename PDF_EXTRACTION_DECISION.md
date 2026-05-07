# PDF Extraction: Architecture Decision

**Date:** 2026-05-05  
**Test file:** `WP_2938_2026_Sand_Mining_Home_Mines_3_Weeks.pdf` (4 pages, text-based)  
**Gold standard:** Sarvam Vision Document Intelligence API

---

## Methods Tested

| Method | Result | Verdict |
|--------|--------|---------|
| **Sarvam Vision** | Markdown output, clean structure, embedded seal image | Gold standard |
| **pdfplumber** | Clean text, zero broken words, proper formatting | Best free alternative |
| **PyMuPDF** | Accurate text but excessive whitespace (178 lines) | Acceptable with cleanup |
| **OCR (Tesseract)** | No broken words, but garbled ellipsis (`..~.`) | Fallback for scanned PDFs only |
| **PyPDF** | 15+ broken words (`elec tronic`, `H on'ble`, `ma fias`) | **Rejected** |
| **marker** | Did not test — downloads 1.35GB+ of AI models | Too heavy |
| **LlamaParse** | Not tested — requires separate API key | — |

---

## Why PyPDF Was Rejected

PyPDF inserts spurious spaces inside words when the PDF uses justified alignment or kerning. Examples from the test:
- `elec tronic` → `electronic`
- `H on'ble` → `Hon'ble`
- `politic al` → `political`
- `ma fias` → `mafias`
- `Gov ernment` → `Government`

This breaks keyword search, entity extraction, and downstream LLM prompts.

---

## Why pdfplumber Was Chosen

- Zero broken words on the same file where PyPDF failed
- Preserves paragraph structure, quotes, and signatures correctly
- Fast (~0.1s for 4 pages)
- No external model downloads
- Output is close enough to Sarvam that the same downstream pipeline works

---

## Recommended Strategy

```
Text-based PDFs (most court judgments)
    → pdfplumber (fast, accurate, free)

Scanned/image PDFs or pdfplumber returns low confidence
    → Sarvam Vision (gold standard, paid)
```

PyPDF removed from all extraction paths. `pypdf` is still used in Pass 1 for **page counting** and **PDF slicing** only, never for text extraction.

---

## Pipeline Integration Results

### Pass 1: Rule-based page detection (replaced Sarvam Vision)
- **pdfplumber** extracts text page-by-page
- **Heuristic scoring** detects operative pages without any LLM
- **Test result:** Sand Mining PDF → Preamble `[1]`, Operative `[3-4]` — correct
- **Speed:** ~0.1s for 4 pages vs ~10s for Sarvam Vision API call

### Bugs Fixed During Integration

| Bug | Fix |
|-----|-----|
| SQLite incompatible with `JSONB`/`ARRAY` | Changed models to use generic `JSON` type |
| SQLite incompatible with `UUID(as_uuid=True)` | Changed IDs to `String(36)` |
| Background task used request's DB session | Background task creates its own `SessionLocal()` |
| `datetime.now(timezone.utc)` vs naive SQLite datetimes | Helper `_now()` returns naive UTC datetime |
| Sarvam-105B returns `content: null` | Fallback to `reasoning_content`, regex extract JSON from markdown blocks |

### End-to-end Test

```bash
curl -X POST "http://localhost:8000/judgments/upload" \
  -F "file=@WP_2938_2026_Sand_Mining_Home_Mines_3_Weeks.pdf" \
  -F "ccms_case_id=WP_2938_2026"
```

**Result:** Pipeline completes in ~15s. Judgment status → `NEEDS_REVIEW`. Action plan extracted with 3 directives.

### Remaining Issue
- Sarvam-105B is a reasoning model — outputs chain-of-thought instead of direct JSON
- JSON extraction works via regex but is brittle
- **Recommendation:** Switch Pass 2 to a non-reasoning model (e.g., `sarvam-1`, `sarvam-2`) for more reliable structured output

## Output Files (for verification)

All raw extractions saved at:
```
/tmp/pdf_comparison_outputs/
├── 01_pypdf.txt          (rejected — broken words)
├── 02_ocr.txt            (fallback quality)
├── 03_pymupdf.txt        (heavy whitespace)
├── 04_pdfplumber.txt     (selected — clean)
└── 05_sarvam_vision.md   (gold standard)
```
