"""Model version lifecycle state machine.

    DRAFT -> VALIDATED -> PENDING_REVIEW -> APPROVED -> MONITORING -> RETIRED
                             |                 |
                             +-> REJECTED <----+
"""

from __future__ import annotations

from enum import StrEnum


class State(StrEnum):
    DRAFT = "DRAFT"
    VALIDATED = "VALIDATED"
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED = "APPROVED"
    MONITORING = "MONITORING"
    REJECTED = "REJECTED"
    RETIRED = "RETIRED"


class Role(StrEnum):
    DATA_SCIENTIST = "data_scientist"
    REVIEWER = "reviewer"
    RISK_LEADER = "risk_leader"


class Action(StrEnum):
    VALIDATE = "validate"
    SUBMIT_REVIEW = "submit_review"
    APPROVE = "approve"
    REJECT = "reject"
    START_MONITORING = "start_monitoring"
    RETIRE = "retire"
    REOPEN = "reopen"  # rejected -> draft so the scientist can fix and resubmit


class TransitionError(Exception):
    def __init__(self, message: str, *, code: str = "invalid_transition") -> None:
        super().__init__(message)
        self.code = code


# (from_state, action) -> to_state
TRANSITIONS: dict[tuple[State, Action], State] = {
    (State.DRAFT, Action.VALIDATE): State.VALIDATED,
    (State.VALIDATED, Action.VALIDATE): State.VALIDATED,  # re-run allowed while not under review
    (State.VALIDATED, Action.SUBMIT_REVIEW): State.PENDING_REVIEW,
    (State.PENDING_REVIEW, Action.APPROVE): State.APPROVED,
    (State.PENDING_REVIEW, Action.REJECT): State.REJECTED,
    (State.APPROVED, Action.REJECT): State.REJECTED,  # approval can be withdrawn with reason
    (State.APPROVED, Action.START_MONITORING): State.MONITORING,
    (State.APPROVED, Action.RETIRE): State.RETIRED,
    (State.MONITORING, Action.RETIRE): State.RETIRED,
    (State.REJECTED, Action.REOPEN): State.DRAFT,
}

ACTION_ROLES: dict[Action, frozenset[Role]] = {
    Action.VALIDATE: frozenset({Role.DATA_SCIENTIST}),
    Action.SUBMIT_REVIEW: frozenset({Role.DATA_SCIENTIST}),
    Action.APPROVE: frozenset({Role.REVIEWER}),
    Action.REJECT: frozenset({Role.REVIEWER}),
    Action.START_MONITORING: frozenset({Role.DATA_SCIENTIST, Role.REVIEWER}),
    Action.RETIRE: frozenset({Role.REVIEWER}),
    Action.REOPEN: frozenset({Role.DATA_SCIENTIST}),
}

MODIFIABLE_STATES: frozenset[State] = frozenset({State.DRAFT, State.VALIDATED})
"""States in which documents/controls may still be edited. VALIDATED is included because
validation only proves the metrics exist; editing documentation resets nothing quantitative.
Training configuration is never modifiable after registration."""


def next_state(current: State, action: Action) -> State:
    try:
        return TRANSITIONS[(State(current), Action(action))]
    except KeyError as exc:
        raise TransitionError(f"cannot {action} from {current}") from exc


def can_perform(role: Role | str, action: Action) -> bool:
    return Role(role) in ACTION_ROLES[Action(action)]


def assert_role(role: Role | str, action: Action) -> None:
    if not can_perform(role, action):
        allowed = ", ".join(sorted(ACTION_ROLES[Action(action)]))
        raise TransitionError(f"role '{role}' may not {action}; allowed: {allowed}", code="forbidden")


def is_modifiable(state: State | str) -> bool:
    return State(state) in MODIFIABLE_STATES
