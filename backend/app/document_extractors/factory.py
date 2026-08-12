from app.document_extractors.pdf_extractor import PdfDocumentExtractor
from app.document_extractors.text_extractor import TextDocumentExtractor


class DocumentTextExtractorFactory:
    @staticmethod
    def create(extension: str):
        normalized_extension = extension.lower()

        if normalized_extension in {".txt", ".md", ".markdown"}:
            return TextDocumentExtractor()

        if normalized_extension == ".pdf":
            return PdfDocumentExtractor()

        raise ValueError("Unsupported document file extension.")
