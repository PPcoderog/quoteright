"""Dependencies between intake, confirmed understanding, and draft pricing."""


def invalidate(state, stage: str) -> None:
    keys = {"draft", "draft_inputs"}
    if stage in {"source", "analysis"}:
        keys |= {"understanding_confirmed", "proposal_initialized", "products", "months", "discount", "coverage_ack", "questions_ack", "acknowledged_gap_ids"}
        keys |= {key for key in state if key.startswith("quantity_")}
    if stage == "source":
        keys |= {"analysis", "analysis_inputs", "analysis_connection"}
    for key in keys:
        state.pop(key, None)


def can_visit(state, step: int) -> bool:
    if step == 0:
        return True
    if step == 1:
        return "analysis" in state
    if step == 2:
        return "analysis" in state and state.get("understanding_confirmed", False)
    if step == 3:
        return "draft" in state and state.get("understanding_confirmed", False)
    return False
