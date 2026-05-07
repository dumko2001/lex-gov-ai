import json
import logging
import re
from typing import Dict, Any
import httpx
import asyncio
from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class SarvamClient:
    def __init__(self):
        self.api_key = settings.SARVAM_API_KEY
        self.base_url = settings.SARVAM_BASE_URL
        self.model = settings.SARVAM_MODEL_PASS2
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def extract_action_plan(self, text: str, page_range: str) -> Dict[str, Any]:
        """
        Send sliced judgment text to Sarvam-105B for structured extraction.
        Uses response_format={"type": "json_object"} to get clean JSON output.
        """
        if not self.api_key:
            raise ValueError("SARVAM_API_KEY not configured")

        prompt = f"""You are an expert legal assistant specializing in Karnataka High Court judgments.

TASK: Extract a structured action plan from the operative portion of a court judgment.

INPUT TEXT (Operative Portion, pages {page_range}):
{text}

EXTRACTION SCHEMA — Output ONLY valid JSON:
{{
  "case_id": "string or null",
  "date_of_order": "YYYY-MM-DD or null",
  "parties": {{
    "petitioner": "string or null",
    "respondent": "string or null"
  }},
  "directives": [
    {{
      "action_type": "COMPLY" or "CONSIDER_APPEAL",
      "responsible_dept": "Revenue" | "Home" | "Law" | "Transport" | "Education" | "Health" | "Urban Development" | "Rural Development" | "Forest" | "Other",
      "deadline_explicit": "YYYY-MM-DD or null",
      "deadline_inferred": "YYYY-MM-DD or null",
      "source_page": integer,
      "source_paragraph": "text snippet or paragraph reference",
      "source_text": "exact verbatim text from judgment",
      "confidence_score": 0.0 to 1.0
    }}
  ],
  "is_complete_info_present": true or false,
  "overall_confidence": 0.0 to 1.0,
  "completeness_assessment": "brief explanation of what might be missing"
}}

RULES:
1. CONDITIONAL DIRECTIVES: If "If X within N days, then Y within M days", extract BOTH conditions.
2. MULTIPLE DEPARTMENTS: Create separate directive objects for each department.
3. LIMITATION PERIODS (for deadline_inferred):
   - 30 days: Specific statutory appeals
   - 60 days: Most High Court orders (DEFAULT)
   - 90 days: Constitutional matters, SLPs
   Calculate from date_of_order.
4. SOURCE TEXT: Include EXACT verbatim text from judgment for each directive.
5. CONFIDENCE: Score based on clarity. Ambiguous conditional language → lower score.
6. COMPLETENESS: If you suspect any directive was missed, set is_complete_info_present=false.

Output ONLY the JSON. No markdown code blocks, no explanations."""

        last_error = None
        for attempt in range(1, 2):
            # Relax response format on retries in case the provider returns blank
            # content for strict json_object mode.
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a senior legal assistant for Karnataka government.",
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.1 if attempt > 1 else 0.2,
                "max_tokens": 4000,
            }
            if attempt == 1:
                payload["response_format"] = {"type": "json_object"}

            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{self.base_url}/v1/chat/completions",
                        headers=self.headers,
                        json=payload,
                        timeout=45.0,
                    )
                    response.raise_for_status()
                    data = response.json()
                    raw_content = data["choices"][0]["message"]["content"]

                if not raw_content or not str(raw_content).strip():
                    raise ValueError("Sarvam returned empty content")

                logger.info(
                    f"Pass 2 raw response (attempt {attempt}): {raw_content[:500]}"
                )
                return self._parse_json_content(raw_content)
            except Exception as exc:
                last_error = exc
                logger.warning("Pass 2 attempt %s failed: %s", attempt, exc)
                if attempt < 3:
                    await asyncio.sleep(1.5 * attempt)

        raise ValueError(f"Pass 2 extraction failed after retries: {last_error}")

    def _parse_json_content(self, raw_content: str) -> Dict[str, Any]:
        """Parse model output JSON with light recovery for fenced/mixed output."""
        text = raw_content.strip()
        if not text:
            raise ValueError("Sarvam returned empty content")

        # Direct parse first.
        try:
            return json.loads(text)
        except Exception:
            pass

        # Strip fenced code blocks if present.
        fenced = re.search(
            r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL | re.IGNORECASE
        )
        if fenced:
            return json.loads(fenced.group(1))

        # Fallback: take the first JSON object found.
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(text[start : end + 1])

        raise ValueError("Unable to parse JSON from Sarvam response")


sarvam_client = SarvamClient()
