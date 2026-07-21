"""v16g4 FIX M7: 4,096-char Meta cap — long Tamil replies must chunk, not truncate."""
from heonix.channels.whatsapp import _split_wa_chunks


def test_short_message_single_chunk():
    assert _split_wa_chunks("hello") == ["hello"]
    assert _split_wa_chunks("") == [""]


def test_long_message_chunks_on_whitespace_and_loses_nothing():
    msg = " ".join(f"word{i}" for i in range(1500))     # ≫ 4096 chars
    chunks = _split_wa_chunks(msg)
    assert len(chunks) > 1
    assert all(len(c) <= 4096 for c in chunks)
    assert " ".join(" ".join(chunks).split()) == msg    # no words lost


def test_unbroken_run_hard_cuts():
    msg = "த" * 9000
    chunks = _split_wa_chunks(msg)
    assert all(len(c) <= 4096 for c in chunks)
    assert "".join(chunks) == msg
