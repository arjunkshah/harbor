"""Harbor Board tests."""

import pytest


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
