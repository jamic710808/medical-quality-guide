#!/usr/bin/env python3
"""Read persisted Codex conversations through the local App Server (stdlib only)."""

import argparse
import datetime as dt
import json
import os
from pathlib import Path
import queue
import subprocess
import sys
import threading
import time


READ_METHODS = {
    "initialize", "thread/list", "thread/read", "thread/turns/list", "thread/items/list"
}
MESSAGE_TYPES = {"userMessage", "agentMessage"}
ACTION_TYPES = {
    "commandExecution", "fileChange", "mcpToolCall", "dynamicToolCall",
    "functionCallOutput", "webSearch", "imageView", "imageGeneration",
    "plan", "enteredReviewMode", "exitedReviewMode", "contextCompaction",
    "collabAgentToolCall", "collabToolCall", "subAgentActivity",
}


class HistoryError(Exception):
    pass


class AppServer:
    """Short-lived stdio connection; no generation or thread mutation methods."""

    def __init__(self, timeout=30):
        self.timeout = timeout
        self.messages = queue.Queue()
        self.serial = 0
        try:
            self.process = subprocess.Popen(
                ["codex", "app-server", "--stdio"], stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                text=True, encoding="utf-8", bufsize=1,
            )
        except FileNotFoundError as exc:
            raise HistoryError("找不到 codex；請在當前運行環境安裝或提供 Codex CLI。") from exc
        self.reader = threading.Thread(target=self._receive, daemon=True)
        self.reader.start()
        try:
            self.call("initialize", {
                "clientInfo": {"name": "read_session_context", "version": "1.0"},
                "capabilities": {"experimentalApi": True},
            })
            self._send({"method": "initialized", "params": {}})
        except Exception:
            self.close()
            raise

    def _receive(self):
        try:
            for line in self.process.stdout:
                try:
                    self.messages.put(json.loads(line))
                except ValueError:
                    continue
        finally:
            self.messages.put(None)

    def _send(self, message):
        try:
            self.process.stdin.write(json.dumps(message) + "\n")
            self.process.stdin.flush()
        except (BrokenPipeError, OSError) as exc:
            raise HistoryError("App Server 連接中斷。") from exc

    def call(self, method, params):
        if method not in READ_METHODS:
            raise HistoryError(f"只讀助手拒絕調用：{method}")
        self.serial += 1
        request_id = self.serial
        self._send({"id": request_id, "method": method, "params": params})
        deadline = time.monotonic() + self.timeout
        while True:
            try:
                message = self.messages.get(timeout=max(0, deadline - time.monotonic()))
            except queue.Empty as exc:
                raise HistoryError(f"{method} 超時；沒有取得完整結果。") from exc
            if message is None:
                raise HistoryError(f"App Server 在 {method} 返回結果前退出。")
            if "method" in message and "id" in message:
                # Do not authorize server-initiated execution or approval requests.
                self._send({"id": message["id"], "error": {
                    "code": -32601, "message": "Read-only history client"
                }})
                continue
            if message.get("id") != request_id:
                continue
            if "error" in message:
                error = message["error"]
                raise HistoryError(
                    f"{method}: {error.get('code')} {error.get('message')}. "
                    "不要為讀取歷史自動遷移存儲、恢復會話或啟動模型；檢查接口支持情況。"
                )
            return message.get("result", {})

    def close(self):
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
        self.reader.join(timeout=3)
        for stream in (self.process.stdin, self.process.stdout):
            if stream:
                stream.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def source(thread_id, turn_id, item_id=None):
    result = {"thread_id": thread_id, "turn_id": turn_id}
    if item_id is not None:
        result["item_id"] = item_id
    return result


def thread_summary(thread):
    return {key: thread[key] for key in (
        "id", "name", "preview", "cwd", "createdAt", "updatedAt", "status",
        "forkedFromId", "source"
    ) if key in thread}


def attachment(content):
    """Keep attachment references, not embedded media or large binary payloads."""
    result = {"type": content.get("type", "unknown"), "attachment_not_read": True}
    for key in ("path", "url", "imageUrl", "name", "id"):
        value = content.get(key)
        if isinstance(value, str):
            result[key] = "<embedded media omitted>" if value.startswith("data:") else value
    return result


def project_item(item, detail_chars=4000):
    kind = item.get("type")
    result = {"item_id": item.get("id"), "type": kind}
    if kind == "userMessage":
        result["role"] = "user"
        result["content"] = [
            {"type": "text", "text": c["text"]} if isinstance(c.get("text"), str)
            else attachment(c) for c in item.get("content", [])
        ]
    elif kind == "agentMessage":
        result.update(role="assistant", text=item.get("text", ""))
        for key in ("phase", "questions"):
            if item.get(key) is not None:
                result[key] = item[key]
    elif kind in ACTION_TYPES:
        # Status is always outside truncated details: a failed action stays failed.
        for key in ("status", "success", "exitCode"):
            if key in item:
                result[key] = item[key]
        details = {k: v for k, v in item.items()
                   if k not in {"id", "type", "status", "success", "exitCode"}}
        encoded = json.dumps(details, ensure_ascii=False)
        if detail_chars is not None and len(encoded) > detail_chars:
            result["details_excerpt"] = encoded[:detail_chars]
            result["details_truncated"] = True
            result["details_total_chars"] = len(encoded)
        else:
            result["details"] = details
    else:
        # Reasoning, injected hook prompts, and unknown internal records are not
        # user/assistant communication. Never turn them into a transcript.
        return None
    return result


def turn_record(thread_id, turn):
    items, omitted = [], {}
    for item in turn.get("items", []):
        projected = project_item(item)
        if projected is None:
            kind = item.get("type", "unknown")
            omitted[kind] = omitted.get(kind, 0) + 1
        else:
            projected["source"] = source(thread_id, turn["id"], item.get("id"))
            items.append(projected)
    return {
        "record": "turn", "source": source(thread_id, turn["id"]),
        "status": turn.get("status"), "started_at": turn.get("startedAt"),
        "completed_at": turn.get("completedAt"), "items": items,
        "omitted_item_types": omitted,
    }


def check_cursor(cursor, seen):
    if cursor is not None:
        if cursor in seen:
            raise HistoryError("分頁遊標重複；已停止，不能聲稱讀完歷史。")
        seen.add(cursor)


def metadata(client, thread_id):
    return client.call("thread/read", {"threadId": thread_id, "includeTurns": False})["thread"]


def list_threads(client, args, emit):
    cursor, seen, total = args.cursor, set(), 0
    while total < args.limit:
        check_cursor(cursor, seen)
        params = {
            "limit": min(50, args.limit - total), "sortKey": "updated_at",
            "sortDirection": "desc", "archived": args.archived,
            "useStateDbOnly": True,
            "sourceKinds": ["cli", "vscode", "appServer", "exec"],
        }
        if cursor is not None:
            params["cursor"] = cursor
        if not args.all_projects:
            params["cwd"] = str(Path(args.cwd).expanduser().resolve())
        if args.title:
            params["searchTerm"] = args.title
        page = client.call("thread/list", params)
        for thread in page.get("data", []):
            if args.since is None or thread.get("updatedAt", 0) >= args.since:
                emit({"record": "session", "thread": thread_summary(thread)})
                total += 1
        cursor = page.get("nextCursor")
        if cursor is None:
            break
    return {
        "record": "coverage", "operation": "list", "sessions_returned": total,
        "next_cursor": cursor, "complete_scan": cursor is None,
        "title_filter_is_not_full_text_search": True,
    }


def read_history(client, args, emit):
    thread = metadata(client, args.thread)
    emit({"record": "session", "thread": thread_summary(thread),
          "observed_at": now(), "order": "newest_first"})
    cursor, seen, total, newest = args.cursor, set(), 0, None
    anchor_found = False
    exhaustive = args.all or args.after_turn is not None
    while True:
        check_cursor(cursor, seen)
        params = {
            "threadId": args.thread, "itemsView": "full", "sortDirection": "desc",
            "limit": 50 if exhaustive else min(50, args.limit - total),
        }
        if cursor is not None:
            params["cursor"] = cursor
        page = client.call("thread/turns/list", params)
        for turn in page.get("data", []):
            if newest is None:
                newest = turn["id"]
            if turn.get("itemsView") not in (None, "full"):
                raise HistoryError("服務端未返回 full 輪次，不能將顯示摘要當作完整記錄。")
            emit(turn_record(args.thread, turn))
            total += 1
            if turn["id"] == args.after_turn:
                anchor_found = True
                break
        cursor = page.get("nextCursor")
        if anchor_found or cursor is None or (not exhaustive and total >= args.limit):
            break
    if args.after_turn and not anchor_found:
        raise HistoryError("增量錨點不存在；可能已回滾或選錯會話。請重新讀取指定範圍。")
    return {
        "record": "coverage", "operation": "read", "thread_id": args.thread,
        "scope": "since_anchor_inclusive" if args.after_turn else "history",
        "turns_returned": total, "scope_complete": anchor_found or cursor is None,
        "start_cursor": args.cursor,
        "complete_history": not args.cursor and not args.after_turn and cursor is None,
        "next_cursor": None if anchor_found else cursor,
        "overlap_anchor_included": anchor_found,
        "checkpoint": None if args.cursor else {
            "thread_id": args.thread, "last_turn_id": newest, "observed_at": now(),
        },
        "live_history_is_not_atomic_snapshot": True,
    }


def searchable_text(item, actions=False):
    if item.get("type") not in MESSAGE_TYPES and not actions:
        return ""
    projected = project_item(item, detail_chars=None)
    if projected is None:
        return ""
    if projected.get("role") == "user":
        return "\n".join(c.get("text", "") for c in projected["content"])
    if projected.get("role") == "assistant":
        return projected["text"] + (
            "\n" + json.dumps(projected["questions"], ensure_ascii=False)
            if "questions" in projected else ""
        )
    return json.dumps(projected, ensure_ascii=False)


def search_history(client, args, emit):
    emit({"record": "session", "thread": thread_summary(metadata(client, args.thread)),
          "observed_at": now()})
    cursor, seen, turns, hits = None, set(), 0, 0
    for_query = [q.casefold() for q in args.query]
    while True:
        check_cursor(cursor, seen)
        params = {"threadId": args.thread, "limit": 50,
                  "itemsView": "full", "sortDirection": "desc"}
        if cursor is not None:
            params["cursor"] = cursor
        page = client.call("thread/turns/list", params)
        for turn in page.get("data", []):
            if turn.get("itemsView") not in (None, "full"):
                raise HistoryError("全文檢索需要 full 輪次；不能檢索顯示摘要並聲稱檢索了正文。")
            turns += 1
            for item in turn.get("items", []):
                text = searchable_text(item, args.actions)
                folded = text.casefold()
                matched = [q for q in for_query if q in folded]
                if not matched:
                    continue
                position = folded.find(matched[0])
                # This is a discovery excerpt, never an exact quotation API.
                start = max(0, position - 180)
                end = min(len(text), position + len(matched[0]) + 350)
                emit({"record": "match", "source": source(args.thread, turn["id"], item.get("id")),
                      "item_type": item.get("type"), "turn_status": turn.get("status"),
                      "matched_queries": matched, "excerpt": text[start:end],
                      "excerpt_only": True})
                hits += 1
                if hits >= args.max_hits:
                    return {"record": "coverage", "operation": "search", "hits": hits,
                            "turns_scanned": turns, "complete_scan": False,
                            "stop_reason": "hit_limit", "queries": args.query}
        cursor = page.get("nextCursor")
        if cursor is None:
            return {"record": "coverage", "operation": "search", "hits": hits,
                    "turns_scanned": turns, "complete_scan": True,
                    "stop_reason": "end_of_history", "queries": args.query}


def show_source(client, args, emit):
    cursor, seen, selected = None, set(), []
    while True:
        check_cursor(cursor, seen)
        params = {"threadId": args.thread, "turnId": args.turn,
                  "limit": 100, "sortDirection": "asc"}
        if cursor is not None:
            params["cursor"] = cursor
        page = client.call("thread/items/list", params)
        for entry in page.get("data", []):
            if entry.get("turnId") != args.turn:
                raise HistoryError("服務端返回了其他輪次，已停止原文定位。")
            item = entry["item"]
            if args.item and item.get("id") != args.item:
                continue
            projected = project_item(item, detail_chars=None)
            if projected is None:
                if args.item:
                    raise HistoryError("該條目不是可導出的用戶溝通或工作記錄。")
                continue
            selected.append(projected)
        cursor = page.get("nextCursor")
        if (args.item and selected) or cursor is None:
            break
    if not selected:
        raise HistoryError("找不到指定的可讀記錄；不會從摘要補造原文。")
    text = json.dumps(selected[0] if args.item else selected, ensure_ascii=False, indent=2)
    if args.offset > len(text):
        raise HistoryError("offset 超過原文長度。")
    end = min(len(text), args.offset + args.chars)
    emit({"record": "source_excerpt", "source": source(args.thread, args.turn, args.item),
          "encoding": "json", "offset": args.offset, "end_offset": end,
          "total_chars": len(text), "text": text[args.offset:end],
          "complete": args.offset == 0 and end == len(text),
          "next_offset": end if end < len(text) else None})
    return {"record": "coverage", "operation": "show", "items_found": len(selected),
            "scope_complete": args.offset == 0 and end == len(text)}


def positive(value):
    n = int(value)
    if n <= 0:
        raise argparse.ArgumentTypeError("必須是正整數")
    return n


def iso_time(value):
    try:
        return dt.datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except ValueError as exc:
        raise argparse.ArgumentTypeError("使用 ISO 日期或時間，例如 2026-09-28T00:00:00+08:00") from exc


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="operation", required=True)
    ls = sub.add_parser("list", help="列出當前項目的候選會話；title 只篩標題")
    scope = ls.add_mutually_exclusive_group()
    scope.add_argument("--cwd", default=os.getcwd())
    scope.add_argument("--all-projects", action="store_true")
    ls.add_argument("--title")
    ls.add_argument("--since", type=iso_time, help="按會話最後更新時間過濾")
    ls.add_argument("--archived", action="store_true")
    ls.add_argument("--limit", type=positive, default=20)
    ls.add_argument("--cursor")
    rd = sub.add_parser("read", help="讀取會話輪次；完整讀取或增量讀取寫入指定臨時文件")
    rd.add_argument("thread", help="精確的會話 UUID")
    mode = rd.add_mutually_exclusive_group()
    mode.add_argument("--all", action="store_true")
    mode.add_argument("--after-turn", help="包含此輪及之後的新記錄，補讀未完成的末輪")
    mode.add_argument("--cursor", help="上一頁 coverage.next_cursor")
    rd.add_argument("--limit", type=positive, default=10)
    se = sub.add_parser("search", help="在一個指定會話的溝通正文中做字面檢索")
    se.add_argument("thread")
    se.add_argument("--query", action="append", required=True, help="可重複，多關鍵詞為 OR")
    se.add_argument("--actions", action="store_true", help="同時檢索工作記錄")
    se.add_argument("--max-hits", type=positive, default=20)
    sh = sub.add_parser("show", help="通過 turn/item ID 回查原文或工作證據")
    sh.add_argument("thread")
    sh.add_argument("--turn", required=True)
    sh.add_argument("--item")
    sh.add_argument("--offset", type=int, default=0)
    sh.add_argument("--chars", type=positive, default=12000)
    for command in (ls, rd, se, sh):
        command.add_argument("--out", type=Path, help="新建 JSONL 文件；不會覆蓋已有文件")
    return p


def main(argv=None):
    p = parser()
    args = p.parse_args(argv)
    if args.operation == "read" and (args.all or args.after_turn) and not args.out:
        p.error("完整或增量讀取請指定 --out 臨時文件，避免終端截斷造成遺漏。")
    if args.operation == "show" and args.offset < 0:
        p.error("offset 不能為負數")
    if args.operation == "search" and any(not q for q in args.query):
        p.error("query 不能為空")
    stream = sys.stdout
    try:
        if args.out:
            fd = os.open(args.out, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            stream = os.fdopen(fd, "w", encoding="utf-8")
        def emit(record):
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")
        with AppServer() as client:
            action = {"list": list_threads, "read": read_history,
                      "search": search_history, "show": show_source}[args.operation]
            coverage = action(client, args, emit)
            emit(coverage)
        if args.out:
            print(json.dumps({"output": str(args.out.resolve()), **coverage}, ensure_ascii=False))
        return 0
    except (HistoryError, OSError, KeyError, ValueError) as exc:
        message = str(exc)
        if stream is not sys.stdout:
            stream.write(json.dumps({"record": "error", "scope_complete": False,
                                     "message": message}, ensure_ascii=False) + "\n")
        print(json.dumps({"error": message, "scope_complete": False}, ensure_ascii=False), file=sys.stderr)
        return 1
    finally:
        if stream is not sys.stdout:
            stream.close()


if __name__ == "__main__":
    sys.exit(main())
