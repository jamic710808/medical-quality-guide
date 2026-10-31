#!/usr/bin/env python3
"""Scoped file/evidence checks for maintain-project; never judges product semantics."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone


RUNTIME = '.codex/maintenance'


def stamp():
    return datetime.now(timezone.utc).isoformat()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def safe_path(root, value):
    if not isinstance(value, str) or not value or Path(value).is_absolute():
        raise ValueError('路徑必須是項目內的非空相對路徑')
    path = root / value
    if not path.resolve().is_relative_to(root) or path.resolve() == root:
        raise ValueError(f'路徑不能指向項目外或項目根: {value}')
    return path


def fingerprint(root, value, ancestors=()):
    path = safe_path(root, value)
    if not path.exists():
        return None
    if path.is_file():
        return digest(path.read_bytes())
    if not path.is_dir():
        raise ValueError(f'不支持的文件類型: {value}')
    resolved = path.resolve()
    if resolved in ancestors:
        raise ValueError(f'檢查輸入包含循環目錄鏈接: {value}')
    files = {}
    for child in sorted(path.rglob('*')):
        name = child.relative_to(root).as_posix()
        safe_path(root, name)
        if child.is_file():
            files[name] = digest(child.read_bytes())
        elif child.is_dir():
            files[name + '/'] = fingerprint(root, name, ancestors + (resolved,)) if child.is_symlink() else 'directory'
    return digest(json.dumps(files, sort_keys=True).encode())


def valid_id(value):
    if not isinstance(value, str) or not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]{0,79}', value):
        raise ValueError('變更 ID 和檢查名僅允許字母、數字、下劃線及連字符，最長80字符')
    return value


def state_path(root, change_id):
    return safe_path(root, f'{RUNTIME}/runs/{valid_id(change_id)}.json')


def write_json(path, value, exclusive=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    if exclusive:
        with path.open('x', encoding='utf-8') as stream:
            stream.write(content)
        return
    fd, temporary = tempfile.mkstemp(prefix='.write-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            stream.write(content)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def read_state(root, change_id):
    result = json.loads(state_path(root, change_id).read_text())
    if result.get('schema_version') != 1 or result.get('project') != str(root):
        raise ValueError('運行記錄版本或項目不匹配')
    return result


def ensure_ignore(root):
    path = safe_path(root, '.gitignore')
    content = path.read_text() if path.exists() else ''
    rule = f'/{RUNTIME}/'
    if rule not in content.splitlines():
        path.write_text(content + ('\n' if content and not content.endswith('\n') else '') + rule + '\n')


def begin(root, scope, session_id):
    if not isinstance(scope, dict):
        raise ValueError('變更範圍必須是 JSON 對象')
    change_id = valid_id(scope.get('id'))
    if state_path(root, change_id).exists():
        raise ValueError('該變更 ID 已存在；不得覆蓋基線或歷史結果')
    if not isinstance(scope.get('request'), str) or not scope['request'].strip():
        raise ValueError('需要本輪需求說明')
    sources = scope.get('sources', [])
    documents = scope.get('documents', [])
    protected = scope.get('protected', [])
    checks = scope.get('checks', [])
    if not isinstance(sources, list) or not sources:
        raise ValueError('需要至少一個本輪實現文件')
    if not isinstance(documents, list) or not isinstance(protected, list):
        raise ValueError('documents 和 protected 必須是數組')
    if not isinstance(checks, list) or not checks or len(checks) != len(set(checks)):
        raise ValueError('需要不重複的實際檢查名')
    for name in checks:
        valid_id(name)
    doc_paths = []
    for doc in documents:
        if not isinstance(doc, dict) or doc.get('action') not in ('update', 'keep') or not str(doc.get('reason', '')).strip():
            raise ValueError('文檔需明確 path、update/keep 決定及理由')
        doc_paths.append(doc['path'])
    paths = sources + doc_paths
    if len(paths) != len(set(paths)):
        raise ValueError('實現和文檔路徑不能重複')
    for value in paths:
        path = safe_path(root, value)
        if path.exists() and not path.is_file():
            raise ValueError(f'實現與文檔範圍應列具體文件: {value}')
        for boundary in protected:
            if path.resolve().is_relative_to(safe_path(root, boundary).resolve()):
                raise ValueError(f'修改範圍與保護路徑重疊: {value}')
    if session_id:
        for path in safe_path(root, f'{RUNTIME}/runs').glob('*.json'):
            prior = json.loads(path.read_text())
            if prior.get('session_id') == session_id and prior.get('state') == 'open':
                raise ValueError('同一會話已有活動變更；先完成或暫停，再開始新的範圍')
    before = {value: fingerprint(root, value) for value in paths + protected}
    result = {'schema_version': 1, 'project': str(root), 'id': change_id,
              'request': scope['request'], 'session_id': session_id, 'state': 'open',
              'sources': sources, 'documents': documents, 'protected': protected,
              'required_checks': checks, 'before': before, 'checks': {}, 'started_at': stamp()}
    ensure_ignore(root)
    write_json(state_path(root, change_id), result, exclusive=True)
    return {'status': 'begun', 'id': change_id, 'session_bound': bool(session_id),
            'record': f'{RUNTIME}/runs/{change_id}.json'}


def require_open(state):
    if state['state'] != 'open':
        raise ValueError('該變更不是活動狀態')


def run_check(root, state, name, argv, inputs, timeout):
    require_open(state)
    if name not in state['required_checks']:
        raise ValueError('檢查名不在本輪範圍內')
    if not argv:
        raise ValueError('缺少實際檢查命令')
    selected = list(dict.fromkeys(state['sources'] + inputs))
    before = {value: fingerprint(root, value) for value in selected}
    if any(before[value] is None for value in inputs):
        raise ValueError('額外聲明的檢查輸入尚不存在')
    output = safe_path(root, f'{RUNTIME}/logs/{state["id"]}-{valid_id(name)}.txt')
    output.parent.mkdir(parents=True, exist_ok=True)
    receipt = {'argv': argv, 'cwd': str(root), 'inputs': before, 'started_at': stamp(),
               'output_path': output.relative_to(root).as_posix()}
    try:
        result = subprocess.run(argv, cwd=root, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, timeout=timeout, check=False)
        receipt.update(exit_code=result.returncode, execution='ran')
        data = result.stdout
    except subprocess.TimeoutExpired as exc:
        receipt.update(exit_code=None, execution='error', error='檢查超時')
        data = exc.stdout or b''
    except OSError as exc:
        receipt.update(exit_code=None, execution='error', error=str(exc))
        data = b''
    after = {value: fingerprint(root, value) for value in selected}
    receipt['inputs_unchanged_during_check'] = before == after
    receipt['finished_at'] = stamp()
    receipt['output_truncated'] = len(data) > 200_000
    output.write_bytes(data[:200_000])
    receipt['output_sha256'] = digest(output.read_bytes())
    state['checks'][name] = receipt
    write_json(state_path(root, state['id']), state)
    if receipt['execution'] == 'error':
        status = 'error'
    else:
        status = 'pass' if receipt['exit_code'] == 0 and before == after else 'fail'
    return {'status': status, 'id': state['id'], 'check': name, 'receipt': receipt}


def evaluate(root, state):
    issues, missing, errors = [], [], []
    changed_sources = [value for value in state['sources'] if fingerprint(root, value) != state['before'][value]]
    if not changed_sources:
        issues.append('本輪實現文件沒有變化')
    for doc in state['documents']:
        value = doc['path']
        current = fingerprint(root, value)
        if doc['action'] == 'update' and (current is None or current == state['before'][value]):
            issues.append(f'應同步的文檔尚未更新: {value}')
        if doc['action'] == 'keep' and current != state['before'][value]:
            issues.append(f'應保留的文檔發生變化: {value}')
    for value in state['protected']:
        if fingerprint(root, value) != state['before'][value]:
            issues.append(f'保護路徑發生變化: {value}')
    for name in state['required_checks']:
        receipt = state['checks'].get(name)
        if receipt is None:
            missing.append(f'未執行檢查: {name}')
            continue
        if receipt.get('execution') != 'ran':
            errors.append(f'檢查未正常執行: {name}: {receipt.get("error", "未知錯誤")}')
            continue
        if receipt['exit_code'] != 0:
            issues.append(f'檢查失敗: {name}，退出狀態 {receipt["exit_code"]}')
        if not receipt['inputs_unchanged_during_check']:
            issues.append(f'檢查過程中輸入發生變化: {name}')
        if {p: fingerprint(root, p) for p in receipt['inputs']} != receipt['inputs']:
            issues.append(f'檢查證據已過期: {name}')
        if fingerprint(root, receipt['output_path']) != receipt['output_sha256']:
            issues.append(f'檢查輸出缺失或已改變: {name}')
    status = 'error' if errors else 'fail' if issues else 'not_run' if missing else 'pass'
    return {'status': status, 'id': state['id'], 'issues': issues + missing + errors,
            'changed_sources': changed_sources, 'document_decisions': state['documents'],
            'semantic_alignment': 'requires_agent_review'}


def hook(root, event):
    if not isinstance(event, dict):
        raise ValueError('Hook 輸入必須是 JSON 對象')
    if event.get('hook_event_name') != 'Stop' or not event.get('session_id'):
        return None
    if event.get('cwd') and not Path(event['cwd']).resolve().is_relative_to(root):
        return None
    active = []
    for path in safe_path(root, f'{RUNTIME}/runs').glob('*.json'):
        state = json.loads(path.read_text())
        if state.get('session_id') == event['session_id'] and state.get('state') == 'open':
            active.append(read_state(root, state['id']))
    if not active:
        return None
    if len(active) != 1:
        return {'systemMessage': '項目維護檢查 error：當前會話有多個活動變更，未自動選擇。'}
    state = active[0]
    result = evaluate(root, state)
    if result['status'] == 'pass':
        return None
    message = f'項目維護檢查 {result["status"]}（{state["id"]}）：' + '；'.join(result['issues'])
    if result['status'] != 'fail' or event.get('stop_hook_active'):
        return {'systemMessage': message}
    # Exact failure state blocks at most once. Cache creation is atomic across concurrent handlers.
    current = {value: fingerprint(root, value) for value in state['before']}
    key = digest(json.dumps([state['id'], result['issues'], current], sort_keys=True).encode())
    marker = safe_path(root, f'{RUNTIME}/blocks/{state["id"]}-{key}')
    marker.parent.mkdir(parents=True, exist_ok=True)
    try:
        with marker.open('x') as stream:
            stream.write(stamp())
    except FileExistsError:
        return {'systemMessage': message + '；同一問題已報告，未重複阻斷。'}
    return {'decision': 'block', 'reason': message}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for command in ['begin', 'run-check', 'check', 'finish', 'pause', 'resume', 'hook']:
        item = sub.add_parser(command)
        item.add_argument('--project', required=True)
        if command not in ('begin', 'hook'):
            item.add_argument('--id', required=True)
        if command == 'begin':
            item.add_argument('--session-id', default=os.environ.get('CODEX_THREAD_ID'))
        if command == 'run-check':
            item.add_argument('--name', required=True)
            item.add_argument('--input', action='append', default=[])
            item.add_argument('--timeout', type=float, default=120)
            item.add_argument('argv', nargs=argparse.REMAINDER)
        if command == 'finish':
            item.add_argument('--review', required=True)
        if command == 'pause':
            item.add_argument('--reason', required=True)
    args = parser.parse_args()
    root = Path(args.project).resolve()
    try:
        if not root.is_dir():
            raise ValueError('項目根不存在')
        if args.command == 'begin':
            result = begin(root, json.load(sys.stdin), args.session_id)
        elif args.command == 'hook':
            result = hook(root, json.load(sys.stdin))
        else:
            state = read_state(root, args.id)
            if args.command == 'run-check':
                argv = args.argv[1:] if args.argv[:1] == ['--'] else args.argv
                result = run_check(root, state, args.name, argv, args.input, args.timeout)
            elif args.command in ('check', 'finish'):
                result = evaluate(root, state)
                if args.command == 'finish':
                    require_open(state)
                    if not args.review.strip():
                        raise ValueError('收尾需要實際語義核對說明')
                    if result['status'] == 'pass':
                        state.update(state='completed', semantic_review=args.review, finished_at=stamp())
                        write_json(state_path(root, state['id']), state)
            elif args.command == 'pause':
                require_open(state)
                if not args.reason.strip():
                    raise ValueError('暫停需要原因')
                state.update(state='paused', pause_reason=args.reason)
                write_json(state_path(root, state['id']), state)
                result = {'status': 'paused', 'id': state['id']}
            else:
                if state['state'] != 'paused':
                    raise ValueError('只能恢復暫停的變更')
                # Preserve one active scope per session even after a pause.
                for path in safe_path(root, f'{RUNTIME}/runs').glob('*.json'):
                    other = json.loads(path.read_text())
                    if state.get('session_id') and other['id'] != state['id'] and other.get('session_id') == state['session_id'] and other.get('state') == 'open':
                        raise ValueError('同一會話已有其他活動變更')
                state.update(state='open')
                write_json(state_path(root, state['id']), state)
                result = {'status': 'resumed', 'id': state['id']}
    except (ValueError, OSError, KeyError, TypeError) as exc:
        result = {'systemMessage': f'項目維護檢查 error：{exc}'} if args.command == 'hook' else {'status': 'error', 'error': str(exc)}
    if result is not None:
        print(json.dumps(result, ensure_ascii=False))
    if args.command != 'hook' and result and result.get('status') in ('fail', 'not_run', 'error'):
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
