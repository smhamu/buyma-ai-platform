from io import BytesIO

from app.common.exceptions import AppException


class PdfDocumentExtractor:
    def extract(self, content: bytes) -> str:
        try:
            from pypdf import PdfReader

            reader = PdfReader(BytesIO(content))
            return "\n\n".join(
                page_text
                for page in reader.pages
                if (page_text := page.extract_text())
            )
        except AppException:
            raise
        except Exception as exc:
            raise ValueError("Failed to extract text from PDF.") from exc
