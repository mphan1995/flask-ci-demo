from functions.action_registry import ACTIONS, get_action, list_actions


def test_registry_contains_actions():
    expected = {
        "recycle_bin",
        "user_temp",
        "windows_temp",
        "browser_cache",
        "windows_update",
        "defender_quick_scan",
    }
    assert expected.issubset(set(ACTIONS.keys()))


def test_registry_entries_have_callables():
    for action_id, action in ACTIONS.items():
        assert get_action(action_id) is action
        assert callable(action["scan"])
        assert callable(action["run"])


def test_list_actions_minimal_fields():
    items = list_actions()
    assert isinstance(items, list)
    assert items
    sample = items[0]
    assert "id" in sample
    assert "name" in sample
    assert "description" in sample
    assert "requires_admin" in sample
