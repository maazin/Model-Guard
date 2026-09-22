import pytest

from modelguard_governance.lifecycle import (
    TRANSITIONS,
    Action,
    Role,
    State,
    TransitionError,
    assert_role,
    can_perform,
    is_modifiable,
    next_state,
)


@pytest.mark.parametrize(("frm", "action", "to"), [(k[0], k[1], v) for k, v in TRANSITIONS.items()])
def test_valid_transitions(frm, action, to):
    assert next_state(frm, action) == to


@pytest.mark.parametrize(
    ("frm", "action"),
    [
        (State.DRAFT, Action.APPROVE),
        (State.DRAFT, Action.SUBMIT_REVIEW),
        (State.VALIDATED, Action.APPROVE),
        (State.PENDING_REVIEW, Action.VALIDATE),
        (State.APPROVED, Action.APPROVE),
        (State.MONITORING, Action.APPROVE),
        (State.RETIRED, Action.REOPEN),
        (State.REJECTED, Action.APPROVE),
        (State.DRAFT, Action.START_MONITORING),
    ],
)
def test_invalid_transitions(frm, action):
    with pytest.raises(TransitionError):
        next_state(frm, action)


def test_only_reviewer_can_decide():
    assert can_perform(Role.REVIEWER, Action.APPROVE)
    assert not can_perform(Role.DATA_SCIENTIST, Action.APPROVE)
    assert not can_perform(Role.RISK_LEADER, Action.REJECT)
    with pytest.raises(TransitionError) as e:
        assert_role("data_scientist", Action.APPROVE)
    assert e.value.code == "forbidden"


def test_modifiable_states():
    assert is_modifiable(State.DRAFT) and is_modifiable(State.VALIDATED)
    for s in (State.PENDING_REVIEW, State.APPROVED, State.MONITORING, State.RETIRED, State.REJECTED):
        assert not is_modifiable(s)
