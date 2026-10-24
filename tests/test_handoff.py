from app.agents.nodes.handoff import _build_contact_options


def test_sample_expert_gets_no_contact_options():
    options = _build_contact_options({"name": "Alex Chen", "email": "alex@example.com", "whatsapp": "+14155551234"})
    assert options.startswith("None.")
    assert "WhatsApp:" not in options


def test_expert_without_email_is_treated_as_sample():
    assert _build_contact_options({"name": "No Email"}).startswith("None.")


def test_real_expert_gets_contact_options():
    options = _build_contact_options({"name": "Real Expert", "email": "real@securefirm.io", "whatsapp": "+15550100"})
    assert "WhatsApp: Click to chat with Real Expert" in options
    assert "Email: Send a message to Real Expert" in options
