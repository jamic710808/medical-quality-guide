#!/usr/bin/env python3
"""Synthetic behavioral checks. No real history, credentials, or model calls."""

import copy
import json
from pathlib import Path
import tempfile
import unittest

import session_history as history


def user(identifier, text):
    return {"id": identifier, "type": "userMessage", "content": [{"type": "text", "text": text}]}


THREAD = "test-session"
TURNS = [
    {"id": "turn-1", "status": "completed", "itemsView": "full", "items": [
        user("user-1", "目標是查看訂單。先討論方案 A，不要發郵件。"),
        {"id": "agent-1", "type": "agentMessage", "text": "建議採用方案 A。", "phase": "final"},
    ]},
    {"id": "turn-2", "status": "completed", "itemsView": "full", "items": [
        user("user-2", "同意方案 A，請執行檢查。"),
        {"id": "cmd-2", "type": "commandExecution", "command": "run-checks",
         "status": "failed", "exitCode": 1, "aggregatedOutput": "檢查失敗\n" + "e" * 6000},
        {"id": "agent-2", "type": "agentMessage", "text": "已經完成。"},
    ]},
    {"id": "turn-3", "status": "inProgress", "itemsView": "full", "items": [
        user("user-3", "撤回之前的方案 A，改用方案 B。發佈尚未批准。\n保留這個限定。"),
        {"id": "private-3", "type": "reasoning", "content": ["INTERNAL_NOT_FOR_TRANSCRIPT"]},
        {"id": "hook-3", "type": "hookPrompt", "fragments": ["INJECTED_NOT_USER_COMMUNICATION"]},
        {"id": "agent-3", "type": "agentMessage", "text": "現在轉向方案 B。"},
    ]},
]


class FakeServer:
    def __init__(self, turns=None):
        self.turns = copy.deepcopy(TURNS if turns is None else turns)
        self.calls = []

    def call(self, method, params):
        self.calls.append((method, params))
        if method not in history.READ_METHODS:
            raise AssertionError("Unexpected mutation: " + method)
        if method == "thread/read":
            return {"thread": {"id": THREAD, "name": "方案討論", "cwd": "/example",
                               "createdAt": 1, "updatedAt": 2, "status": {"type": "active"}}}
        if method == "thread/turns/list":
            rows = list(reversed(self.turns))
            start = int(params.get("cursor", "0"))
            end = min(len(rows), start + min(2, params.get("limit", 50)))
            return {"data": rows[start:end], "nextCursor": str(end) if end < len(rows) else None}
        if method == "thread/items/list":
            turn = next((t for t in self.turns if t["id"] == params["turnId"]), None)
            rows = [{"turnId": turn["id"], "item": i} for i in turn["items"]] if turn else []
            start = int(params.get("cursor", "0"))
            end = min(len(rows), start + 2)
            return {"data": rows[start:end], "nextCursor": str(end) if end < len(rows) else None}
        if method == "thread/list":
            return {"data": [{"id": THREAD, "name": "方案討論", "cwd": "/example", "updatedAt": 2}],
                    "nextCursor": None}
        raise AssertionError(method)


def invoke(operation, arguments, server=None):
    args = history.parser().parse_args([operation, *arguments])
    rows = []
    function = {"read": history.read_history, "search": history.search_history,
                "show": history.show_source, "list": history.list_threads}[operation]
    server = server or FakeServer()
    coverage = function(server, args, rows.append)
    return rows, coverage, server


class HistoryBehaviorTests(unittest.TestCase):
    def test_complete_read_keeps_reversal_and_failed_execution_evidence(self):
        rows, coverage, server = invoke("read", [THREAD, "--all"])
        turns = [r for r in rows if r["record"] == "turn"]
        self.assertEqual([t["source"]["turn_id"] for t in turns], ["turn-3", "turn-2", "turn-1"])
        self.assertTrue(coverage["complete_history"])
        self.assertEqual(coverage["checkpoint"]["last_turn_id"], "turn-3")
        self.assertIn("撤回", turns[0]["items"][0]["content"][0]["text"])
        self.assertIn("同意方案 A", turns[1]["items"][0]["content"][0]["text"])
        failed = turns[1]["items"][1]
        self.assertEqual((failed["status"], failed["exitCode"]), ("failed", 1))
        self.assertTrue(failed["details_truncated"])
        self.assertEqual(failed["source"], history.source(THREAD, "turn-2", "cmd-2"))
        self.assertEqual(turns[1]["items"][2]["text"], "已經完成。")
        serialized = json.dumps(rows)
        self.assertNotIn("INTERNAL_NOT_FOR_TRANSCRIPT", serialized)
        self.assertNotIn("INJECTED_NOT_USER_COMMUNICATION", serialized)
        self.assertEqual(sum(m == "thread/turns/list" for m, _ in server.calls), 2)

    def test_partial_page_and_continuation_never_claim_full_history(self):
        _, first, _ = invoke("read", [THREAD, "--limit", "1"])
        self.assertFalse(first["scope_complete"])
        self.assertFalse(first["complete_history"])
        self.assertEqual(first["next_cursor"], "1")
        _, remainder, _ = invoke("read", [THREAD, "--cursor", "1", "--limit", "10"])
        self.assertTrue(remainder["scope_complete"])
        self.assertFalse(remainder["complete_history"])
        self.assertIsNone(remainder["checkpoint"])

    def test_increment_replays_anchor_with_new_items_and_later_turns(self):
        turns = copy.deepcopy(TURNS)
        turns[-1]["status"] = "completed"
        turns[-1]["items"].append({"id": "cmd-3", "type": "commandExecution", "status": "completed",
                                  "exitCode": 0, "command": "check-B", "aggregatedOutput": "B passed"})
        turns.append({"id": "turn-4", "status": "completed", "itemsView": "full",
                      "items": [user("user-4", "繼續驗證，但不要發佈。") ]})
        rows, coverage, _ = invoke("read", [THREAD, "--after-turn", "turn-3"], FakeServer(turns))
        exported = [r for r in rows if r["record"] == "turn"]
        self.assertEqual([t["source"]["turn_id"] for t in exported], ["turn-4", "turn-3"])
        self.assertEqual(exported[1]["status"], "completed")
        self.assertEqual(exported[1]["items"][-1]["exitCode"], 0)
        self.assertTrue(coverage["overlap_anchor_included"])
        self.assertTrue(coverage["scope_complete"])
        self.assertFalse(coverage["complete_history"])

    def test_missing_increment_anchor_fails_instead_of_silently_resetting(self):
        with self.assertRaisesRegex(history.HistoryError, "錨點不存在"):
            invoke("read", [THREAD, "--after-turn", "removed-turn"])

    def test_search_covers_full_messages_and_returns_original_source(self):
        rows, coverage, _ = invoke("search", [THREAD, "--query", "發佈尚未批准"])
        matches = [r for r in rows if r["record"] == "match"]
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["source"], history.source(THREAD, "turn-3", "user-3"))
        self.assertTrue(coverage["complete_scan"])
        _, limited, _ = invoke("search", [THREAD, "--query", "方案", "--max-hits", "1"])
        self.assertFalse(limited["complete_scan"])

    def test_show_recovers_full_original_and_chunk_offsets(self):
        rows, _, _ = invoke("show", [THREAD, "--turn", "turn-3", "--item", "user-3"])
        original = json.loads(rows[0]["text"])
        self.assertEqual(original["content"][0]["text"], TURNS[2]["items"][0]["content"][0]["text"])
        first, _, _ = invoke("show", [THREAD, "--turn", "turn-2", "--item", "cmd-2", "--chars", "80"])
        self.assertEqual(first[0]["next_offset"], 80)
        second, _, _ = invoke("show", [THREAD, "--turn", "turn-2", "--item", "cmd-2", "--offset", "80"])
        full = json.loads(first[0]["text"] + second[0]["text"])
        self.assertEqual(full["details"]["aggregatedOutput"], TURNS[1]["items"][1]["aggregatedOutput"])

    def test_read_does_not_shorten_long_user_messages(self):
        text = "必須保留的用戶限定。" * 1200
        server = FakeServer([{"id": "long-turn", "status": "completed", "itemsView": "full",
                              "items": [user("long-message", text)]}])
        rows, _, _ = invoke("read", [THREAD], server)
        self.assertEqual(rows[1]["items"][0]["content"][0]["text"], text)

    def test_list_preserves_project_scope_and_uses_title_filter_only(self):
        _, coverage, server = invoke("list", ["--cwd", "/example", "--title", "方案"])
        params = server.calls[0][1]
        self.assertEqual(params["cwd"], "/example")
        self.assertEqual(params["searchTerm"], "方案")
        self.assertTrue(params["useStateDbOnly"])
        self.assertTrue(coverage["title_filter_is_not_full_text_search"])

    def test_mutating_request_is_rejected_before_transport(self):
        client = history.AppServer.__new__(history.AppServer)
        for method in ("thread/resume", "thread/fork", "thread/compact/start", "turn/start", "thread/delete"):
            with self.assertRaisesRegex(history.HistoryError, "只讀助手拒絕"):
                client.call(method, {"threadId": THREAD})

    def test_repeated_cursor_fails_and_existing_export_is_not_overwritten(self):
        seen = set()
        history.check_cursor("same", seen)
        with self.assertRaises(history.HistoryError):
            history.check_cursor("same", seen)
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "history.jsonl"
            target.write_text("existing", encoding="utf-8")
            # Opening fails before a server is started.
            self.assertEqual(history.main(["read", THREAD, "--all", "--out", str(target)]), 1)
            self.assertEqual(target.read_text(encoding="utf-8"), "existing")


if __name__ == "__main__":
    unittest.main()
