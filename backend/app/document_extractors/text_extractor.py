class TextDocumentExtractor:
    def extract(self, content: bytes) -> str:
        return content.decode("utf-8")
