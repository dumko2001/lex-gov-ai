import os
import json
import logging
import zipfile
import io
from typing import Dict, Any, List, Optional
import httpx
from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class SarvamVisionClient:
    """Client for Sarvam Vision Document Intelligence API.

    Handles the full flow: create job → upload → start → poll → download.
    Max 10 pages per job.
    """

    def __init__(self):
        self.api_key = settings.SARVAM_API_KEY
        self.base_url = settings.SARVAM_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def extract_document(self, file_path: str, language: str = "en-IN") -> str:
        """
        Extract text from a PDF using Sarvam Vision Document Intelligence.
        Returns the extracted text in markdown format.

        For PDFs > 10 pages, splits into chunks and processes each.
        """
        if not self.api_key:
            raise ValueError("SARVAM_API_KEY not configured")

        # Check file size and page count
        from pypdf import PdfReader

        reader = PdfReader(file_path)
        total_pages = len(reader.pages)

        logger.info(f"Processing PDF with {total_pages} pages")

        if total_pages <= 10:
            # Single job
            return await self._process_single_chunk(file_path, language)
        else:
            # Multiple chunks
            return await self._process_multiple_chunks(file_path, total_pages, language)

    async def _process_single_chunk(self, file_path: str, language: str) -> str:
        """Process a single PDF (≤10 pages)."""
        job_id = await self._create_job(language)
        logger.info(f"Created job {job_id}")

        await self._upload_file(job_id, file_path)
        logger.info(f"Uploaded file to job {job_id}")

        await self._start_job(job_id)
        logger.info(f"Started job {job_id}")

        await self._poll_until_complete(job_id)
        logger.info(f"Job {job_id} complete")

        text = await self._download_and_extract(job_id)
        return text

    async def _process_multiple_chunks(
        self, file_path: str, total_pages: int, language: str
    ) -> str:
        """Process a large PDF in chunks of 10 pages."""
        from pypdf import PdfReader, PdfWriter

        reader = PdfReader(file_path)
        all_texts = []

        chunk_size = 10
        for start in range(0, total_pages, chunk_size):
            end = min(start + chunk_size, total_pages)
            logger.info(f"Processing pages {start+1}-{end}")

            # Create chunk PDF
            writer = PdfWriter()
            for i in range(start, end):
                writer.add_page(reader.pages[i])

            chunk_path = f"{file_path}_chunk_{start}.pdf"
            with open(chunk_path, "wb") as f:
                writer.write(f)

            try:
                text = await self._process_single_chunk(chunk_path, language)
                all_texts.append(f"\n\n<!-- PAGES {start+1}-{end} -->\n\n{text}")
            finally:
                if os.path.exists(chunk_path):
                    os.remove(chunk_path)

        return "\n".join(all_texts)

    async def _create_job(self, language: str) -> str:
        """Create a document intelligence job."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/v1/document-intelligence/jobs",
                headers=self.headers,
                json={"language": language, "output_format": "md"},
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
            return data["job_id"]

    async def _upload_file(self, job_id: str, file_path: str):
        """Upload file to the job."""
        # Get upload URLs
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/v1/document-intelligence/jobs/{job_id}/upload-urls",
                headers=self.headers,
                timeout=30.0,
            )
            response.raise_for_status()
            upload_data = response.json()

            # Upload file to presigned URL
            upload_url = upload_data["upload_urls"][0]

            with open(file_path, "rb") as f:
                file_content = f.read()

            upload_headers = {"Content-Type": "application/pdf"}

            response = await client.put(
                upload_url, content=file_content, headers=upload_headers, timeout=60.0
            )
            response.raise_for_status()

    async def _start_job(self, job_id: str):
        """Start processing the job."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/v1/document-intelligence/jobs/{job_id}/start",
                headers=self.headers,
                timeout=30.0,
            )
            response.raise_for_status()

    async def _poll_until_complete(self, job_id: str, max_retries: int = 60):
        """Poll job status until complete or failed."""
        import asyncio

        for _ in range(max_retries):
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/v1/document-intelligence/jobs/{job_id}",
                    headers=self.headers,
                    timeout=30.0,
                )
                response.raise_for_status()
                data = response.json()

                status = data.get("job_state", "PENDING")
                logger.info(f"Job {job_id} status: {status}")

                if status in ["COMPLETED", "SUCCESS"]:
                    return
                elif status in ["FAILED", "ERROR"]:
                    raise ValueError(
                        f"Job {job_id} failed: {data.get('error_message', 'Unknown error')}"
                    )

                await asyncio.sleep(2)

        raise TimeoutError(
            f"Job {job_id} did not complete within {max_retries * 2} seconds"
        )

    async def _download_and_extract(self, job_id: str) -> str:
        """Download output and extract text from markdown."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/v1/document-intelligence/jobs/{job_id}/download-urls",
                headers=self.headers,
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()

            download_url = data["download_urls"][0]

            # Download ZIP
            response = await client.get(download_url, timeout=60.0)
            response.raise_for_status()

            # Extract markdown from ZIP
            with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                # Find markdown file
                md_files = [name for name in z.namelist() if name.endswith(".md")]
                if md_files:
                    with z.open(md_files[0]) as f:
                        return f.read().decode("utf-8")

                # Fallback: find HTML file
                html_files = [name for name in z.namelist() if name.endswith(".html")]
                if html_files:
                    with z.open(html_files[0]) as f:
                        return f.read().decode("utf-8")

                # Fallback: read any text file
                for name in z.namelist():
                    if not name.endswith("/"):
                        with z.open(name) as f:
                            return f.read().decode("utf-8")

            return ""


sarvam_vision_client = SarvamVisionClient()
