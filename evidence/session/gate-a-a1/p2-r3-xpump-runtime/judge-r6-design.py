#!/usr/bin/env python3
"""Judge one design-complete R6 cell from GATEA_EVENT lines.

Order authority is telemetry `seq`, not logcat file order. A completion cover
is required: renderer role, same generation as Present CALLBACK, serial >= S
(batch watermark). Gaps/duplicates fail unless a complete ring dump fills them.
"""
from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

EV_LEASE = 2
EV_PUBLISH = 6
EV_COMPLETED = 14
EV_FAILED = 15
EV_FATAL = 16
EV_SUCCESS = 17
EV_REQUEST = 29
EV_CALLBACK = 30
EV_REJECT = 31
EV_EARLY_ACK = 32
EV_REQUEUE_FAILED = 33
EV_ACK_AFTER_COMPLETED = 34
XOP_COPY = 1
XOP_SOLID = 2
XOP_COMPOSITE = 3
XOP_PRESENT = 4
XOP_PREPARE = 5
MAJOR_COPY = 62
MAJOR_SOLID = 70
MAJOR_GETIMAGE = 73
ROLE_X = 1
ROLE_RENDERER = 2
CAP = 512
PAT = re.compile(
    r'GATEA_EVENT seq=(\d+) role=(\d+) event=(\d+) generation=(\d+) '
    r'serial=(\d+) src=(\d+) dst=(\d+)'
)


class JudgeFail(Exception):
    def __init__(self, code: str, extra: str = '') -> None:
        super().__init__(code)
        self.code = code
        self.extra = extra


def parse(follow: str) -> list[dict]:
    events = []
    for m in PAT.finditer(follow):
        seq, role, event, gen, serial, src, dst = (int(x) for x in m.groups())
        events.append({
            'seq': seq, 'role': role, 'event': event, 'gen': gen,
            'serial': serial, 'src': src, 'dst': dst,
        })
    return events


def merge_by_seq(follow_events: list[dict], ring_events: list[dict]) -> list[dict]:
    by_seq: dict[int, dict] = {}
    for e in follow_events + ring_events:
        prev = by_seq.get(e['seq'])
        if prev is not None and prev != e:
            raise JudgeFail('telemetry_seq_conflict', f'seq={e["seq"]} {prev} vs {e}')
        by_seq[e['seq']] = e
    return list(by_seq.values())


def order_events(events: list[dict]) -> list[dict]:
    if not events:
        return []
    seqs = [e['seq'] for e in events]
    if len(seqs) != len(set(seqs)):
        raise JudgeFail('telemetry_seq_duplicate')
    ordered = sorted(events, key=lambda e: e['seq'])
    lo, hi = ordered[0]['seq'], ordered[-1]['seq']
    if hi - lo + 1 != len(ordered):
        missing = [i for i in range(lo, hi + 1) if i not in set(seqs)]
        raise JudgeFail('telemetry_seq_gap', f'missing={missing[:16]}')
    if lo != 0:
        raise JudgeFail('telemetry_seq_prefix', f'lo={lo}')
    return ordered


def major_minor(src: int) -> tuple[int, int]:
    return src >> 32, src & 0xFFFFFFFF


def is_present_req(src: int) -> bool:
    maj, mn = major_minor(src)
    return mn == 1 and maj not in (MAJOR_COPY, MAJOR_SOLID, MAJOR_GETIMAGE)


def is_composite_req(src: int) -> bool:
    maj, mn = major_minor(src)
    return mn == 8 and maj not in (MAJOR_COPY, MAJOR_SOLID, MAJOR_GETIMAGE)


def first_after(events: list[dict], after_seq: int, pred) -> dict | None:
    return next((e for e in events if e['seq'] > after_seq and pred(e)), None)


def completion_cover(events: list[dict], after_seq: int, gen: int, serial_s: int):
    return first_after(
        events, after_seq,
        lambda e: (
            e['event'] == EV_COMPLETED
            and e['role'] == ROLE_RENDERER
            and e['gen'] == gen
            and e['serial'] >= serial_s
        ),
    )


def fail(code: str, extra: str = '') -> None:
    raise JudgeFail(code, extra)


def paired_composite(
    events: list[dict], after_seq: int, code_prefix: str,
) -> tuple[dict, dict]:
    request = first_after(
        events, after_seq,
        lambda e: e['event'] == EV_REQUEST and is_composite_req(e['src']),
    )
    if request is None:
        fail(f'd2_{code_prefix}_missing_composite_request')
    callback = first_after(
        events, request['seq'],
        lambda e: e['event'] == EV_CALLBACK and e['src'] == XOP_COMPOSITE,
    )
    if callback is None:
        fail(f'd2_{code_prefix}_missing_composite_callback')
    if callback['dst'] != request['dst']:
        fail(f'd2_{code_prefix}_composite_request_callback_unpaired')
    return request, callback


def direct_lifecycle(
    events: list[dict], after_seq: int, gen: int, min_serial: int,
    code_prefix: str, *, dest_id: int = 0, before_seq: int | None = None,
) -> dict:
    """Bind one direct transaction; LEASE has serial=0, PUBLISH assigns it."""
    lease = first_after(
        events, after_seq,
        lambda e: (
            e['event'] == EV_LEASE
            and e['role'] == ROLE_X
            and e['gen'] == gen
            and e['serial'] == 0
            and e['src'] != 0
            and e['dst'] != 0
            and (dest_id == 0 or e['dst'] == dest_id)
        ),
    )
    if lease is None or (before_seq is not None and lease['seq'] >= before_seq):
        suffix = '_before_next_request' if before_seq is not None else ''
        fail(f'd2_{code_prefix}_missing_target_lease{suffix}')
    source_id = lease['src']
    target_dst = lease['dst']

    def in_window(e: dict) -> bool:
        return before_seq is None or e['seq'] < before_seq

    publish = first_after(
        events, lease['seq'],
        lambda e: (
            in_window(e)
            and e['event'] == EV_PUBLISH
            and e['role'] == ROLE_X
            and e['gen'] == gen
            and e['serial'] > min_serial
            and e['src'] == source_id
            and e['dst'] == target_dst
        ),
    )
    if publish is None:
        fail(f'd2_{code_prefix}_missing_target_publish')
    completed = first_after(
        events, publish['seq'],
        lambda e: (
            in_window(e)
            and e['event'] == EV_COMPLETED
            and e['role'] == ROLE_RENDERER
            and e['gen'] == gen
            and e['serial'] >= publish['serial']
            and e['src'] == source_id
            and e['dst'] == target_dst
        ),
    )
    if completed is None:
        fail(f'd2_{code_prefix}_missing_target_completion')
    success = first_after(
        events, completed['seq'],
        lambda e: (
            in_window(e)
            and e['event'] == EV_SUCCESS
            and e['role'] == ROLE_X
            and e['gen'] == gen
            and e['serial'] == publish['serial']
            and e['src'] == source_id
            and e['dst'] == target_dst
        ),
    )
    if success is None:
        fail(f'd2_{code_prefix}_missing_target_success')
    return {
        'lease': lease,
        'publish': publish,
        'completed': completed,
        'success': success,
        'src': source_id,
        'dst': target_dst,
    }


def judge_d1(events: list[dict], out: str) -> str:
    if 'RESULT p_r6_d1_queued CLIENT_OK' not in out:
        fail('d1_client_result')
    if 'PASS D1-composite-dst' not in out or 'got0=00804000' not in out:
        fail('d1_pixels')
    comp_req = next((e for e in events
                     if e['event'] == EV_REQUEST and is_composite_req(e['src'])), None)
    if comp_req is None:
        fail('d1_missing_composite_request')
    cb3 = first_after(events, comp_req['seq'],
                      lambda e: e['event'] == EV_CALLBACK and e['src'] == XOP_COMPOSITE)
    if cb3 is None:
        fail('d1_missing_composite_callback')
    first_success = first_after(events, cb3['seq'],
                                lambda e: e['event'] == EV_SUCCESS)
    if first_success is None:
        fail('d1_no_semantic_success_after_composite')
    need_req = {
        'copy': lambda maj, mn: maj == MAJOR_COPY,
        'solid': lambda maj, mn: maj == MAJOR_SOLID,
        'getimage': lambda maj, mn: maj == MAJOR_GETIMAGE,
        'present': lambda maj, mn: mn == 1 and maj not in (MAJOR_COPY, MAJOR_SOLID, MAJOR_GETIMAGE),
    }
    need_cb = {
        'copy': XOP_COPY, 'solid': XOP_SOLID, 'getimage': XOP_PREPARE, 'present': XOP_PRESENT,
    }
    for name, pred in need_req.items():
        req = next((e for e in events
                    if e['event'] == EV_REQUEST and pred(*major_minor(e['src']))), None)
        if req is None:
            fail(f'd1_missing_request_{name}')
        if req['seq'] < comp_req['seq']:
            fail(f'd1_schedule_second_before_composite_{name}')
        if req['seq'] < first_success['seq']:
            fail(f'd1_request_pumped_during_wait_{name}')
        cb = first_after(events, req['seq'],
                         lambda e, xop=need_cb[name]: e['event'] == EV_CALLBACK and e['src'] == xop)
        if cb is None:
            fail(f'd1_missing_callback_after_request_{name}')
    return 'R6_D1_PASS'


def judge_d2(events: list[dict], out: str, variant: str) -> str:
    if 'RESULT p_r6_d2_present CLIENT_OK' not in out:
        fail('d2_client_result')
    if 'PASS D2-later-composite' not in out or 'got0=00804000' not in out:
        fail('d2_later_pixels')

    present_cb = next((e for e in events
                       if e['event'] == EV_CALLBACK and e['src'] == XOP_PRESENT), None)
    if present_cb is None:
        fail('d2_missing_present_callback')
    s = present_cb['serial']
    gen = present_cb['gen']
    pcb_seq = present_cb['seq']
    client_seq = present_cb['dst']
    present_req = next((
        e for e in events
        if e['event'] == EV_REQUEST and is_present_req(e['src'])
        and e['dst'] == client_seq and e['seq'] < pcb_seq
    ), None)
    if present_req is None:
        fail('d2_present_request_callback_unpaired')

    cover = completion_cover(events, pcb_seq, gen, s)
    if cover is None:
        fail('d2_missing_completion_cover', f'serial>={s} gen={gen} role={ROLE_RENDERER}')

    dest_id = 0
    source_id = 0
    gate_seq = cover['seq']
    if variant == 'd2-oom':
        if any(e['event'] == EV_EARLY_ACK for e in events):
            fail('d2_oom_unexpected_early_ack')
        requeue = first_after(
            events, pcb_seq,
            lambda e: (
                e['event'] == EV_REQUEUE_FAILED
                and e['gen'] == gen
                and e['serial'] == s
            ),
        )
        if requeue is None:
            fail('d2_oom_missing_requeue_failed')
        ack = first_after(
            events, pcb_seq,
            lambda e: (
                e['event'] == EV_ACK_AFTER_COMPLETED
                and e['gen'] == gen
                and e['serial'] == s
            ),
        )
        if ack is None:
            fail('d2_oom_missing_ack_after_completed')
        if ack['seq'] <= cover['seq'] or ack['seq'] <= requeue['seq']:
            fail('d2_oom_ack_before_cover_or_requeue')
        dest_id = ack['dst'] or requeue['dst']
        if dest_id == 0:
            fail('d2_oom_missing_dst')
        gate_seq = ack['seq']
        later_req, later_cb = paired_composite(events, gate_seq, 'oom')
        direct_lifecycle(
            events,
            later_cb['seq'],
            gen,
            s,
            'oom',
            dest_id=dest_id,
        )
    else:
        if any(e['event'] == EV_EARLY_ACK for e in events):
            fail('d2_inflight_unexpected_early_ack')
        comp_req, comp_cb = paired_composite(events, pcb_seq, 'immediate')

        for e in events:
            if not (pcb_seq < e['seq'] < cover['seq']):
                continue
            if (
                e['event'] == EV_LEASE
                and e['role'] == ROLE_X
                and e['gen'] == gen
            ) or (
                e['event'] in (EV_PUBLISH, EV_SUCCESS)
                and e['gen'] == gen
                and e['serial'] > s
            ):
                fail('d2_lease_or_publish_before_completed', str(e))

        rej = next((
            e for e in events
            if e['event'] == EV_REJECT
            and e['src'] == 1
            and e['gen'] == gen
            and e['seq'] > comp_cb['seq']
        ), None)
        if rej is not None and rej['seq'] < cover['seq']:
            dest_id = rej['dst']
            if dest_id == 0:
                fail('d2_reject_missing_dst')
            later_req, later_cb = paired_composite(events, cover['seq'], 'later')
            direct_lifecycle(
                events,
                later_cb['seq'],
                gen,
                s,
                'later',
                dest_id=dest_id,
            )
        else:
            next_comp_req = first_after(
                events,
                comp_req['seq'],
                lambda e: e['event'] == EV_REQUEST and is_composite_req(e['src']),
            )
            if next_comp_req is None:
                fail('d2_missing_later_composite_request')
            first_lease = first_after(
                events,
                comp_cb['seq'],
                lambda e: (
                    e['event'] == EV_LEASE
                    and e['role'] == ROLE_X
                    and e['gen'] == gen
                    and e['serial'] == 0
                    and e['src'] != 0
                    and e['dst'] != 0
                ),
            )
            if first_lease is None or first_lease['seq'] >= next_comp_req['seq']:
                fail('d2_immediate_missing_target_lease_before_next_request')
            if first_lease['seq'] <= cover['seq']:
                fail('d2_direct_lease_before_completion_cover')
            immediate = direct_lifecycle(
                events,
                comp_cb['seq'],
                gen,
                s,
                'immediate',
                before_seq=next_comp_req['seq'],
            )
            later_req, later_cb = paired_composite(
                events, immediate['success']['seq'], 'later'
            )
            direct_lifecycle(
                events,
                later_cb['seq'],
                gen,
                immediate['publish']['serial'],
                'later',
                dest_id=immediate['dst'],
            )

    if variant != 'd2-oom' and any(
        e['event'] == EV_REJECT and e['src'] == 1 and e['gen'] == gen
        and e['seq'] > comp_cb['seq'] and e['seq'] >= cover['seq']
        for e in events
    ):
        fail('d2_conflicting_reject_after_cover')
    return f'R6_D2_PASS {variant}'


def load_ordered_events(cell: Path) -> list[dict]:
    follow = (cell / 'logcat-follow.txt').read_text(errors='replace') if (
        cell / 'logcat-follow.txt').exists() else ''
    ring = (cell / 'gatea-ring.txt').read_text(errors='replace') if (
        cell / 'gatea-ring.txt').exists() else ''
    follow_events = parse(follow)
    try:
        return order_events(follow_events)
    except JudgeFail as exc:
        if exc.code not in ('telemetry_seq_gap', 'telemetry_seq_prefix') or not ring:
            raise
        merged = merge_by_seq(follow_events, parse(ring))
        return order_events(merged)


def judge_cell(cell: Path, variant: str, fix_rc: int) -> str:
    follow = (cell / 'logcat-follow.txt').read_text(errors='replace') if (
        cell / 'logcat-follow.txt').exists() else ''
    out = (cell / 'r6-fixture.out').read_text(errors='replace') if (
        cell / 'r6-fixture.out').exists() else ''
    envx = (cell / 'x-environ-gatea.txt').read_text(errors='replace') if (
        cell / 'x-environ-gatea.txt').exists() else ''
    events = load_ordered_events(cell)
    counts = Counter(e['event'] for e in events)
    max_seq = max((e['seq'] for e in events), default=-1)
    lines = [
        f'variant={variant}',
        f'fixture_rc={fix_rc}',
        f'event_lines={len(events)}',
        f'max_seq={max_seq}',
        f'counts={dict(sorted(counts.items()))}',
    ]
    (cell / 'gatea-event-counts.txt').write_text('\n'.join(lines) + '\n')
    print('\n'.join(lines))

    if 'GATEA_FATAL_HALT' in follow or 'x-ready-timeout' in follow or 'Fatal signal' in follow:
        fail('fatal_or_timeout', follow[-2000:])
    if counts[EV_FAILED] or counts[EV_FATAL]:
        fail('firstFailed_or_genFatal')
    if max_seq >= CAP:
        fail('telemetry_overflow', f'max_seq={max_seq}')
    if fix_rc != 0:
        fail('fixture_rc')

    oom_line = [ln for ln in envx.splitlines() if ln.startswith('TERMUX_X11_GATEA_R6_PRESENT_REQUEUE_FAIL=')]
    if variant == 'd2-oom':
        if oom_line != ['TERMUX_X11_GATEA_R6_PRESENT_REQUEUE_FAIL=1']:
            fail('oom_env_not_exact_1', envx)
    else:
        if oom_line:
            fail('oom_env_armed_on_non_oom', envx)

    if variant == 'd1':
        return judge_d1(events, out)
    if variant not in ('d2-inflight', 'd2-oom'):
        fail('unknown_variant', variant)
    return judge_d2(events, out, variant)


def main() -> int:
    cell = Path(sys.argv[1])
    variant = sys.argv[2]
    fix_rc = int(sys.argv[3])
    try:
        result = judge_cell(cell, variant, fix_rc)
    except JudgeFail as exc:
        print(f'R6_DESIGN_FAIL {exc.code}')
        if exc.extra:
            print(exc.extra)
        return 2
    print(result)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
