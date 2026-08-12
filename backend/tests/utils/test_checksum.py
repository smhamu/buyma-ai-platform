from app.utils.checksum import calculate_sha256


def test_calculate_sha256_returns_64_character_hash():
    result = calculate_sha256(b"BUYMA document")

    assert len(result) == 64
    assert result == (
        "2f682795d62d9e524554047073b42369"
        "9ea0f63beeb33aca88596dcc806e38ee"
    )
