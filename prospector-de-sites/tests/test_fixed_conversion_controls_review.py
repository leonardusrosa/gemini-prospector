from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


def load_fixed_controls_review():
    module_path = Path(__file__).resolve().parents[1] / "fixed_conversion_controls_review.py"
    spec = spec_from_file_location("fixed_conversion_controls_review", module_path)
    assert spec and spec.loader
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_assistant_and_floating_whatsapp_is_blocked():
    mod = load_fixed_controls_review()
    result = mod.inspect_html(
        '<div data-role="assistant-launcher"></div>'
        '<a data-role="floating-whatsapp" href="https://wa.me/5511999999999">WhatsApp</a>'
    )
    assert result["pass"] is False
    assert result["failures"][0]["key"] == "assistant_floating_whatsapp_conflict"


def test_assistant_with_normal_whatsapp_cta_and_no_floating_passes():
    mod = load_fixed_controls_review()
    result = mod.inspect_html(
        '<a href="https://wa.me/5511999999999">Agendar</a>'
        '<div data-role="assistant-launcher"></div>'
    )
    assert result["pass"] is True


def test_floating_whatsapp_without_assistant_is_not_blocked_by_exclusivity_rule():
    mod = load_fixed_controls_review()
    result = mod.inspect_html(
        '<a data-role="floating-whatsapp" href="https://wa.me/5511999999999">WhatsApp</a>'
    )
    assert result["pass"] is True
