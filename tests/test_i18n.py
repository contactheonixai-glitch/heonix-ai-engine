"""v15g4 FIX A1 lives here: Indic combining marks must survive normalisation."""
from heonix.i18n import _norm_text, _t, detect_language


def test_norm_text_preserves_indic_matras():
    # Hindi: खाना (food) vs खून (blood) collapsed to the same skeleton pre-fix
    assert _norm_text("खाना") != _norm_text("खून")
    assert _norm_text("मुझे खाना चाहिए") == "मुझे खाना चाहिए"
    # Tamil matras survive; punctuation stripped, whitespace collapsed
    assert _norm_text("  சரி!!  ") == "சரி"
    assert "வலி" in _norm_text("எனக்கு ரொம்ப வலி!!!")
    assert _norm_text("Hello,   WORLD!") == "hello world"


def test_detect_language_by_script():
    assert detect_language("வணக்கம் டாக்டர்") == "ta"
    assert detect_language("नमस्ते डॉक्टर") == "hi"
    assert detect_language("hello doctor") == "en"


def test_t_localized_with_safe_fallbacks():
    en, ta, hi = (_t("phone_request", l) for l in ("en", "ta", "hi"))
    assert en and ta and hi and len({en, ta, hi}) == 3
    assert _t("phone_request", "fr") == en          # unsupported lang → English
    assert _t("no_such_key", "ta") == ""            # unknown key → ''
