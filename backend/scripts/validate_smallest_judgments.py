from pathlib import Path
from pypdf import PdfReader
import sys

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.services.pdf_service import pdf_service  # noqa: E402
from app.services.pipeline_service import pipeline_service  # noqa: E402


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    base = repo_root / "test-data" / "judgments"
    pdfs = []
    for p in base.rglob("*.pdf"):
        if p.suffix.lower() != ".pdf":
            continue
        pages = len(PdfReader(str(p)).pages)
        pdfs.append((pages, p))

    selected = sorted(pdfs)[:3]
    print("Selected smallest real judgments:")
    for n, p in selected:
        print(f"- {n} pages :: {p}")

    print("\nPass1 + slicing validation:")
    for n, p in selected:
        page_rows = pdf_service.extract_text_by_page(str(p))
        page_texts = {page_num: text for page_num, text in page_rows}

        classifications = []
        for page_num in range(1, n + 1):
            scores = pipeline_service._score_page(page_texts.get(page_num, ""))
            classifications.append(
                {
                    "page": page_num,
                    "operative_score": scores["operative"],
                    "preamble_score": scores["preamble"],
                    "procedural_score": scores["procedural"],
                }
            )

        operative_pages = pipeline_service._find_operative_block(classifications, n)
        operative_range = (
            pipeline_service._build_page_range(operative_pages)
            if operative_pages
            else f"{max(1, n - 4)}-{n}"
        )
        parsed_pages = pipeline_service._parse_page_range(operative_range)
        sliced_path = pdf_service.slice_pdf(str(p), parsed_pages)
        sliced_pages = len(PdfReader(sliced_path).pages)
        sliced_text = pdf_service.extract_text(sliced_path)

        print(f"\n{p.name}")
        print(f"  total_pages={n}")
        print(f"  operative_range={operative_range}")
        print(f"  parsed_pages={parsed_pages}")
        print(f"  sliced_pages={sliced_pages}")
        print(f"  sliced_text_chars={len(sliced_text)}")
        print(f"  pass2_payload_chars={min(30000, len(sliced_text))}")


if __name__ == "__main__":
    main()
