#!/usr/bin/env python3
"""Run repository quality checks from trusted Codex hooks; stdin is event metadata only."""

import argparse
import fcntl
import fnmatch
import hashlib
import json
import os
import re
from pathlib import Path
import subprocess
import sys
import time
import uuid

RESULTS = '.quality-results'


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args])


def snapshot(root):
    names = git(root, 'ls-files', '-z', '--cached', '--others', '--exclude-standard').split(b'\0')
    result = {}
    for raw in names:
        if not raw:
            continue
        name = os.fsdecode(raw)
        if name.startswith(RESULTS + '/'):
            continue
        path = root / name
        if path.is_symlink():
            value = ('symlink:' + os.readlink(path)).encode()
        elif path.is_file():
            value = path.read_bytes()
        else:
            continue
        result[name] = hashlib.sha256(value).hexdigest()
    return result


def fingerprint(files):
    return hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()


def matches(path, patterns):
    return any(fnmatch.fnmatchcase(path, p) or (p.startswith('**/') and fnmatch.fnmatchcase(path, p[3:])) for p in patterns)


def changed(before, after):
    return sorted(p for p in set(before) | set(after) if before.get(p) != after.get(p))


def read_json(path, default):
    return json.loads(path.read_text()) if path.exists() else default


def atomic_json(path, value):
    tmp = path.with_name(path.name + '.' + uuid.uuid4().hex)
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    tmp.replace(path)


def execute(root, argv, log_path, timeout):
    started = time.monotonic()
    try:
        with log_path.open('w') as log:
            proc = subprocess.run(argv, cwd=root, stdout=log, stderr=subprocess.STDOUT, timeout=timeout)
        status = 'passed' if proc.returncode == 0 else 'failed'
        return {'status': status, 'exit_code': proc.returncode, 'seconds': round(time.monotonic() - started, 3)}
    except (OSError, subprocess.TimeoutExpired) as exc:
        log_path.write_text(str(exc) + '\n')
        return {'status': 'error', 'error': str(exc)}


def run(root, payload, full=False):
    event = payload.get('hook_event_name')
    if event not in ('PostToolUse', 'Stop'):
        raise ValueError('Only PostToolUse and Stop events are supported')
    out = root / RESULTS
    out.mkdir(parents=True, exist_ok=True)
    with (out / 'lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return {'status': 'busy', 'reason': 'Another quality check is running; results are not yet available'}
        state_path = out / 'state.json'
        state = read_json(state_path, {})
        current = snapshot(root)
        head = git(root, 'rev-parse', 'HEAD').decode().strip()
        registry_path = root / '.codex/hooks/checks.json'
        registry_bytes = registry_path.read_bytes()
        registry_hash = hashlib.sha256(registry_bytes).hexdigest()
        registry = json.loads(registry_bytes)
        if 'files' in state:
            delta = changed(state['files'], current)
        else:
            # On installation, include all existing tracked and untracked work, not clean files.
            dirty = git(root, 'diff', '--name-only', 'HEAD', '-z').split(b'\0')
            untracked = git(root, 'ls-files', '--others', '--exclude-standard', '-z').split(b'\0')
            delta = sorted({os.fsdecode(p) for p in dirty + untracked if p and not os.fsdecode(p).startswith(RESULTS + '/')})
        pending = sorted(set(state.get('pending', [])) | set(delta))
        full_scope = event == 'Stop' or full
        paths = pending if full_scope else delta
        if full_scope and not paths and state.get('head') != head:
            paths = state.get('last_scope', [])
        same_full = state.get('full_key') == [head, fingerprint(current), registry_hash, full]
        if full_scope and same_full and not full:
            previous = read_json(root / state['report'], {})
            return {'status': previous.get('status', 'incomplete'), 'report': state['report'], 'cached': True}
        if not paths and not full:
            return {'status': 'unchanged', 'reason': 'No new changes requiring checks', 'previous_report': state.get('report')}
        force_all = full or bool(set(paths) & {'.codex/hooks/checks.json', 'scripts/codex_hooks.py'})
        selected = [c for c in registry['checks'] if force_all or any(matches(p, c['paths']) for p in paths)]
        run_id = str(time.time_ns()) + '-' + uuid.uuid4().hex[:8]
        run_dir = out / run_id
        run_dir.mkdir()
        report = {'schema_version': 1, 'event': event, 'session_id': payload.get('session_id'),
                  'turn_id': payload.get('turn_id'), 'head': head, 'started_at': time.time(),
                  'registry_hash': registry_hash, 'input_fingerprint': fingerprint(current),
                  'scope': 'full' if full_scope else 'changed', 'explicit_full': full, 'paths': paths, 'checks': []}
        expected = current
        concurrent = set()
        for check in selected:
            record = {'id': check['id'], 'commands': []}
            commands = check.get('commands')
            if not commands or check.get('status') != 'connected':
                record.update(status='unavailable', reason=check.get('reason', 'Check is not connected'))
            else:
                files = sorted(p for p in paths if matches(p, check.get('file_paths', check['paths'])) and (root / p).is_file())
                # A deletion still requires full validation, even if no formatter input remains.
                for index, command in enumerate(commands):
                    if command.get('formatter') and not files:
                        continue
                    if full and 'full' in command:
                        argv = command['full']
                    else:
                        argv = command.get('all') if (full_scope and not command.get('formatter')) or not files else command.get('changed', command.get('all'))
                    if not isinstance(argv, list) or not argv or not all(isinstance(arg, str) for arg in argv):
                        raise ValueError('Invalid command in check ' + check['id'])
                    expanded = []
                    for arg in argv:
                        if arg == '{files}':
                            expanded.extend(files)
                        elif arg == '{spotless_files}':
                            expanded.append('-PspotlessFiles=' + ','.join(re.escape(str(root / p)) for p in files))
                        else:
                            expanded.append(arg)
                    log = run_dir / (check['id'] + '-' + str(index) + '.log')
                    before_command = snapshot(root)
                    concurrent.update(changed(expected, before_command))
                    result = execute(root, expanded, log, check.get('timeout', 300))
                    after_command = snapshot(root)
                    mutations = changed(before_command, after_command)
                    permitted = set(files) if command.get('formatter') else set()
                    concurrent.update(p for p in mutations if p not in permitted)
                    result['changed_files'] = mutations
                    expected = after_command
                    result.update(argv=expanded, log=str(log.relative_to(root)))
                    record['commands'].append(result)
                    if result['status'] != 'passed':
                        break
                record['status'] = 'passed' if all(r['status'] == 'passed' for r in record['commands']) else 'failed'
            report['checks'].append(record)
        after = snapshot(root)
        concurrent.update(changed(expected, after))
        final_head = git(root, 'rev-parse', 'HEAD').decode().strip()
        head_changed = head != final_head
        unrelated = sorted(concurrent)
        report['output_fingerprint'] = fingerprint(after)
        report['concurrent_changes'] = unrelated
        report['final_head'] = final_head
        report['status'] = 'passed' if all(c['status'] == 'passed' for c in report['checks']) and not unrelated and not head_changed else 'incomplete'
        report['finished_at'] = time.time()
        report_path = run_dir / 'report.json'
        atomic_json(report_path, report)
        invalidated = bool(unrelated) or head_changed
        remaining = sorted(set(pending) | set(paths) | concurrent) if invalidated else ([] if full_scope else pending)
        state = {'files': after, 'pending': remaining, 'report': str(report_path.relative_to(root)),
                 'head': head, 'last_scope': paths if full_scope else state.get('last_scope', [])}
        if full_scope and not invalidated:
            state['full_key'] = [head, fingerprint(after), registry_hash, full]
        atomic_json(state_path, state)
        return {'status': report['status'], 'report': str(report_path.relative_to(root)),
                'checks': {c['id']: c['status'] for c in report['checks']}, 'concurrent_changes': unrelated}


def feedback(result, payload):
    if result['status'] == 'busy' and payload.get('hook_event_name') == 'PostToolUse':
        # A concurrent check has no final result yet; keep this tool result.
        return {'systemMessage': 'Quality checks are still running; no completed result is available: ' + json.dumps(result, ensure_ascii=False)}
    if result['status'] in ('passed', 'unchanged'):
        return {'systemMessage': 'Quality checks: ' + json.dumps(result, ensure_ascii=False)} if result['status'] == 'passed' else {}
    reason = 'Quality checks are not complete: ' + json.dumps(result, ensure_ascii=False)
    if payload.get('hook_event_name') == 'Stop' and payload.get('stop_hook_active'):
        # Surface unresolved failures once without an endless Stop continuation loop.
        return {'systemMessage': reason}
    return {'decision': 'block', 'reason': reason}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--full', action='store_true', help='Validate all registered checks, including unavailable ones')
    args = parser.parse_args()
    payload = json.load(sys.stdin)
    try:
        # Resolve repository from this reviewed script, never from event-supplied commands or paths.
        root = Path(__file__).resolve().parent.parent
        result = run(root, payload, args.full)
        print(json.dumps(feedback(result, payload), ensure_ascii=False))
    except Exception as exc:
        print(json.dumps(feedback({'status': 'error', 'reason': str(exc)}, payload), ensure_ascii=False))


if __name__ == '__main__':
    main()
