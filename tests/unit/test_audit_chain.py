from modelguard_governance.audit import GENESIS_HASH, compute_event_hash, verify_chain


def _chain(n=4):
    events, prev = [], GENESIS_HASH
    for i in range(n):
        ev = {
            "actor_id": "u1",
            "action": f"a{i}",
            "entity_type": "model_version",
            "entity_id": "mv",
            "before_json": {"state": i},
            "after_json": {"state": i + 1},
            "occurred_at": f"2026-01-0{i + 1}T00:00:00",
        }
        ev["previous_hash"] = prev
        ev["event_hash"] = compute_event_hash(prev, ev)
        prev = ev["event_hash"]
        events.append(ev)
    return events


def test_valid_chain_verifies():
    r = verify_chain(_chain())
    assert r.valid and r.checked == 4


def test_altered_prior_payload_is_detected():
    events = _chain()
    events[1]["after_json"] = {"state": 99}
    r = verify_chain(events)
    assert not r.valid and r.first_bad_index == 1


def test_broken_link_is_detected():
    events = _chain()
    events[2]["previous_hash"] = "deadbeef"
    r = verify_chain(events)
    assert not r.valid and r.first_bad_index == 2


def test_empty_chain_is_valid():
    assert verify_chain([]).valid
