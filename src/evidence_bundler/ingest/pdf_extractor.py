"""Unified PDF text extraction for ingest."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

ExtractorBackend = Literal["auto", "pdfminer", "pypdf"]
PDFBackend = Literal["pdfminer", "pypdf"]
PDFAttemptStatus = Literal["ok", "empty", "error"]
PDFFailureReason = Literal["empty_text", "extractor_error"]


@dataclass(frozen=True)
class PDFBackendAttempt:
    """Outcome for one PDF extraction backend."""

    backend: PDFBackend
    status: PDFAttemptStatus
    message: str | None = None


class PDFExtractionError(Exception):
    """Raised when a PDF cannot yield extractable text."""

    def __init__(
        self,
        pdf_path: Path,
        *,
        reason: PDFFailureReason,
        attempts: tuple[PDFBackendAttempt, ...],
    ) -> None:
        self.pdf_path = pdf_path
        self.reason = reason
        self.attempts = attempts
        attempt_summary = "; ".join(
            f"{attempt.backend}:{attempt.status}"
            + (f" ({attempt.message})" if attempt.message else "")
            for attempt in attempts
        )
        super().__init__(
            f"PDF extraction failed for {pdf_path.name}: {reason}"
            + (f" [{attempt_summary}]" if attempt_summary else "")
        )


class PDFExtractor:
    """Extract text from PDFs with pdfminer.six primary and pypdf fallback."""

    def __init__(self, backend: ExtractorBackend = "auto") -> None:
        self.backend = backend

    def extract(self, pdf_path: Path) -> str:
        """Return extracted text or raise a classified extraction error."""
        pdf_path = pdf_path.resolve()
        if self.backend == "pdfminer":
            return self._extract_single_backend(pdf_path, "pdfminer")
        if self.backend == "pypdf":
            return self._extract_single_backend(pdf_path, "pypdf")
        return self._extract_auto(pdf_path)

    def _extract_auto(self, pdf_path: Path) -> str:
        attempts: list[PDFBackendAttempt] = []
        pdfminer_text, pdfminer_attempt = self._attempt(pdf_path, "pdfminer")
        attempts.append(pdfminer_attempt)
        if pdfminer_text.strip():
            return pdfminer_text

        pypdf_text, pypdf_attempt = self._attempt(pdf_path, "pypdf")
        attempts.append(pypdf_attempt)
        if pypdf_text.strip():
            return pypdf_text

        raise PDFExtractionError(
            pdf_path,
            reason=_failure_reason(tuple(attempts)),
            attempts=tuple(attempts),
        )

    def _extract_single_backend(self, pdf_path: Path, backend: PDFBackend) -> str:
        text, attempt = self._attempt(pdf_path, backend)
        if text.strip():
            return text
        raise PDFExtractionError(
            pdf_path,
            reason=_failure_reason((attempt,)),
            attempts=(attempt,),
        )

    def _attempt(self, pdf_path: Path, backend: PDFBackend) -> tuple[str, PDFBackendAttempt]:
        try:
            text = (
                self._extract_pdfminer(pdf_path)
                if backend == "pdfminer"
                else self._extract_pypdf(pdf_path)
            )
        except Exception as exc:
            return "", PDFBackendAttempt(
                backend=backend,
                status="error",
                message=f"{type(exc).__name__}: {exc}",
            )

        if not text.strip():
            return "", PDFBackendAttempt(backend=backend, status="empty")
        return text, PDFBackendAttempt(backend=backend, status="ok")

    def _extract_pdfminer(self, pdf_path: Path) -> str:
        from pdfminer.high_level import extract_pages
        from pdfminer.layout import LTTextContainer

        pages: list[str] = []
        for page_layout in extract_pages(str(pdf_path)):
            elements = sorted(
                (element for element in page_layout if isinstance(element, LTTextContainer)),
                key=lambda element: -element.y1,
            )
            page_text = "\n".join(
                element.get_text().strip()
                for element in elements
                if element.get_text().strip()
            )
            if page_text:
                pages.append(page_text)
        return "\n\n".join(pages)

    def _extract_pypdf(self, pdf_path: Path) -> str:
        from pypdf import PdfReader

        reader = PdfReader(str(pdf_path))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n\n".join(page.strip() for page in pages if page.strip())


def _failure_reason(attempts: tuple[PDFBackendAttempt, ...]) -> PDFFailureReason:
    if attempts and all(attempt.status == "empty" for attempt in attempts):
        return "empty_text"
    return "extractor_error"
