from workflow import can_visit, invalidate


def test_navigation_requires_confirmed_prerequisites():
    state = {}
    assert can_visit(state, 0)
    assert not can_visit(state, 1)
    state["analysis"] = object()
    assert can_visit(state, 1)
    assert not can_visit(state, 2)
    state["understanding_confirmed"] = True
    assert can_visit(state, 2)
    assert not can_visit(state, 3)
    state["draft"] = object()
    assert can_visit(state, 3)


def test_source_changes_clear_all_dependent_results_and_preserve_connection():
    state = {"analysis": object(), "understanding_confirmed": True, "draft": object(),
        "draft_inputs": (1,), "quantity_TEAM": "20", "products": ["TEAM"], "months": 12,
        "api_key": "test-key", "nav": 0}
    invalidate(state, "source")
    assert "analysis" not in state and "draft" not in state and "quantity_TEAM" not in state
    assert "products" not in state and "months" not in state
    assert state["api_key"] == "test-key"


def test_commercial_changes_clear_draft_but_keep_confirmed_analysis():
    state = {"analysis": object(), "understanding_confirmed": True, "draft": object(), "draft_inputs": (1,)}
    invalidate(state, "commercial")
    assert "draft" not in state
    assert state["understanding_confirmed"] is True
    assert "analysis" in state
