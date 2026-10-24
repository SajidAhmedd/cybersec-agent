from app.agents.nodes.matching import order_matches
from app.schemas.expert import public_expert


def _expert(id, **extra):
    return {"id": id, "name": f"Expert {id}", "skills": ["incident_response"], **extra}


def _match(expert, score):
    return {"expert": expert, "match": {"expert_id": expert["id"], "match_score": score}}


FEATURED = _expert(9, is_featured=True, email="me@real.dev", whatsapp="+447700900000", public_contact=True)
EXTERNAL = _expert(5, is_external=True, profile_url="https://www.toptal.com/x")


def test_featured_first_then_external_then_by_score():
    matched = [_match(_expert(1), 0.95), _match(_expert(2), 0.9), _match(EXTERNAL, 0.7), _match(_expert(3), 0.6)]
    ids = [m["expert"]["id"] for m in order_matches(matched, [FEATURED], [EXTERNAL], ["incident_response"])]
    assert ids == [9, 5, 1, 2, 3]


def test_pinned_experts_added_when_graph_missed_them():
    matched = [_match(_expert(1), 0.95), _match(_expert(2), 0.9)]
    ordered = order_matches(matched, [FEATURED], [EXTERNAL], ["incident_response"])
    assert [m["expert"]["id"] for m in ordered] == [9, 5, 1, 2]
    assert ordered[0]["match"]["matched_skills"] == ["incident_response"]


def test_featured_expert_not_listed_twice():
    matched = [_match(_expert(1), 0.95), _match(FEATURED, 0.8), _match(EXTERNAL, 0.7)]
    ids = [m["expert"]["id"] for m in order_matches(matched, [FEATURED], [EXTERNAL], [])]
    assert ids == [9, 5, 1]


def test_limit_keeps_pinned_slots():
    matched = [_match(_expert(i), 1 - i / 10) for i in range(1, 8)]
    ids = [m["expert"]["id"] for m in order_matches(matched, [FEATURED], [EXTERNAL], [], limit=5)]
    assert ids == [9, 5, 1, 2, 3]


def test_public_contact_kept_only_when_expert_opted_in():
    assert public_expert(FEATURED)["whatsapp"] == "+447700900000"
    hidden = public_expert(_expert(1, email="a@example.com", whatsapp="+1", phone="+1"))
    assert not {"email", "whatsapp", "phone"} & hidden.keys()
