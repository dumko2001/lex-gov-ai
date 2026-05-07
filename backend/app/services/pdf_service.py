import os
import io
import logging
from typing import List, Tuple, Optional
from pathlib import Path
from pdf2image import convert_from_path
from pypdf import PdfReader, PdfWriter
import pdfplumber
from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

class PDFService:
    def __init__(self):
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    def save_upload(self, file_bytes: bytes, filename: str) -> Tuple[str, int]:
        """Save uploaded PDF and return (file_path, page_count)."""
        file_path = self.upload_dir / filename
        with open(file_path, "wb") as f:
            f.write(file_bytes)
        
        reader = PdfReader(str(file_path))
        page_count = len(reader.pages)
        
        return str(file_path), page_count
    
    def get_page_images(
        self, 
        file_path: str, 
        page_numbers: List[int], 
        dpi: int = 150
    ) -> List[bytes]:
        """Convert specified PDF pages to PNG images."""
        images = convert_from_path(
            file_path, 
            dpi=dpi,
            first_page=min(page_numbers),
            last_page=max(page_numbers)
        )
        
        result = []
        for i, page_num in enumerate(range(min(page_numbers), max(page_numbers) + 1)):
            if page_num in page_numbers:
                img_byte_arr = io.BytesIO()
                images[i].save(img_byte_arr, format="PNG")
                result.append(img_byte_arr.getvalue())
        
        return result
    
    def slice_pdf(self, file_path: str, page_numbers: List[int]) -> str:
        """Extract specified pages into a new PDF. Returns path to sliced PDF."""
        reader = PdfReader(file_path)
        writer = PdfWriter()
        
        for page_num in page_numbers:
            if 1 <= page_num <= len(reader.pages):
                writer.add_page(reader.pages[page_num - 1])
        
        base_name = Path(file_path).stem
        sliced_path = self.upload_dir / f"{base_name}_sliced.pdf"
        
        with open(sliced_path, "wb") as f:
            writer.write(f)
        
        return str(sliced_path)
    
    def extract_text(self, file_path: str) -> str:
        """Extract all text from a PDF file."""
        text_parts = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        
        return "\n\n".join(text_parts)
    
    def extract_text_by_page(self, file_path: str) -> List[Tuple[int, str]]:
        """Extract text by page. Returns list of (page_number, text)."""
        result = []
        with pdfplumber.open(file_path) as pdf:
            for i, page in enumerate(pdf.pages, 1):
                text = page.extract_text() or ""
                result.append((i, text))
        return result

pdf_service = PDFService()
