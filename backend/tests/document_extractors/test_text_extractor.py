from app.document_extractors.text_extractor import TextDocumentExtractor


def test_extract_txt():
    extractor = TextDocumentExtractor()

    result = extractor.extract("BUYMA商品登録".encode("utf-8"))

    assert result == "BUYMA商品登録"
