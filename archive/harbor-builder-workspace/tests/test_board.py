"""Harbor Board tests."""


def test_board_crud(tmp_path, monkeypatch):
    monkeypatch.setattr("harbor.board.ROOT", tmp_path)
    monkeypatch.setattr("harbor.board.BOARD_FILE", tmp_path / ".harbor" / "board.json")

    from harbor.board import create_card, delete_card, get_card, update_card

    card = create_card(project_id="p1", title="Ship auth", description="Magic link flow")
    assert card["title"] == "Ship auth"
    updated = update_card(card["id"], title="Ship auth v2", column="building")
    assert updated["column"] == "building"
    assert get_card(card["id"])["title"] == "Ship auth v2"
    assert delete_card(card["id"])
    assert get_card(card["id"]) is None


def test_board_plan_sync(tmp_path, monkeypatch):
    monkeypatch.setattr("harbor.board.ROOT", tmp_path)
    monkeypatch.setattr("harbor.board.BOARD_FILE", tmp_path / ".harbor" / "board.json")

    from harbor.board import list_board, move_card, sync_plan_to_board

    plan = {"id": "p1", "title": "Launch", "goal": "Ship", "tasks": [{"text": "Auth", "done": False}]}
    sync_plan_to_board(plan, "proj1")
    board = list_board("proj1")
    assert board["total"] == 2
    cards = board["cards"]["backlog"]
    assert any(c["title"] == "Auth" for c in cards)

    card_id = cards[0]["id"]
    moved = move_card(card_id, "building")
    assert moved["column"] == "building"
