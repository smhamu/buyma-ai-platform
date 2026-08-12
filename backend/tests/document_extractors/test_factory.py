import pytest

from app.document_extractors.factory import DocumentTextExtractorFactory
from app.document_extractors.pdf_extractor import PdfDocumentExtractor
from app.document_extractors.text_extractor import TextDocumentExtractor


def test_txt_extractor():
    result = DocumentTextExtractorFactory.create(".txt")

    assert isinstance(result, TextDocumentExtractor)


def test_markdown_extractor():
    result = DocumentTextExtractorFactory.create(".md")

    assert isinstance(result, TextDocumentExtractor)


def test_pdf_extractor():
    result = DocumentTextExtractorFactory.create(".pdf")

    assert isinstance(result, PdfDocumentExtractor)


def test_unsupported_extension():
    with pytest.raises(ValueError):
        DocumentTextExtractorFactory.create(".xlsx")
