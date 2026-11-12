#!/usr/bin/env python3
"""Negative and positive tests for judge-r6-design.py. No ADB. No source mutation."""
from __future__ import annotations

import importlib.util
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

JUDGE_DIR = Path('/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-xpump-runtime')
_spec = importlib.util.spec_from_file_location('judge_r6_design', JUDGE_DIR / 'judge-r6-design.py')
J = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(J)

HIST = JUDGE_DIR / 'runtime-9369553'
CURRENT = JUDGE_DIR / 'runtime-95e6f96'
COMP_SRC = (138 << 32) | 8
PRESENT_SRC = (140 << 32) | 1
CLIENT_SEQ = 42
DST = 5
SRC_BUF = 7


def ev(seq, role, event, gen, serial, src, dst=0):
    return (f'I gatea-telemetry: GATEA_EVENT seq={seq} role={role} event={event} '
            f'generation={gen} serial={serial} src={src} dst={dst}\n')


def write_cell(root: Path, follow: str, variant: str, *, oom=False, out=None, ring=None):
    root.mkdir(parents=True, exist_ok=True)
    (root / 'logcat-follow.txt').write_text(follow)
    if out is None:
        if variant == 'd1':
            out = ('PASS D1-composite-dst exact_px=64 maxΔ=0 got0=00804000\n'
                   'RESULT p_r6_d1_queued CLIENT_OK pixels exact\n')
        else:
            out = ('PASS D2-later-composite exact_px=64 maxΔ=0 got0=00804000\n'
                   'RESULT p_r6_d2_present CLIENT_OK mode=inflight later pixels exact\n')
    (root / 'r6-fixture.out').write_text(out)
    env = 'TERMUX_X11_GATEA_PROTO=1\nTERMUX_X11_GATEA_TELEMETRY=1\n'
    if oom:
        env += 'TERMUX_X11_GATEA_R6_PRESENT_REQUEUE_FAIL=1\n'
    (root / 'x-environ-gatea.txt').write_text(env)
    if ring is not None:
        (root / 'gatea-ring.txt').write_text(ring)
    return root


def direct_lifecycle(start_seq, serial, client_seq, *, src=SRC_BUF, dst=DST):
    """Production schema: LEASE serial=0; PUBLISH assigns the transaction serial."""
    return [
        ev(start_seq, 1, 2, 1, 0, src, dst),
        ev(start_seq + 1, 1, 6, 1, serial, src, dst),
        ev(start_seq + 2, 2, 14, 1, serial, src, dst),
        ev(start_seq + 3, 1, 17, 1, serial, src, dst),
    ]


def inflight_ok(cover_serial=7):
    """Busy immediate Composite rejects; a paired later Composite succeeds."""
    return ''.join([
        ev(0, 1, 29, 1, 0, PRESENT_SRC, CLIENT_SEQ),
        ev(1, 1, 30, 1, 6, 4, CLIENT_SEQ),
        ev(2, 1, 29, 1, 0, COMP_SRC, 43),
        ev(3, 1, 30, 1, 0, 3, 43),
        ev(4, 1, 31, 1, 6, 1, DST),
        ev(5, 2, 14, 1, cover_serial, 0, 0),
        ev(6, 1, 29, 1, 0, COMP_SRC, 44),
        ev(7, 1, 30, 1, 0, 3, 44),
        *direct_lifecycle(8, 8, 44),
    ])


def inflight_quiescent_ok(cover_serial=7, *, cover_src=0, cover_dst=0):
    """Immediate and later Composites each have a bound direct lifecycle."""
    return ''.join([
        ev(0, 1, 29, 1, 0, PRESENT_SRC, CLIENT_SEQ),
        ev(1, 1, 30, 1, 6, 4, CLIENT_SEQ),
        ev(2, 1, 29, 1, 0, COMP_SRC, 43),
        ev(3, 1, 30, 1, 0, 3, 43),
        ev(4, 2, 14, 1, cover_serial, cover_src, cover_dst),
        *direct_lifecycle(5, 8, 43),
        ev(9, 1, 29, 1, 0, COMP_SRC, 44),
        ev(10, 1, 30, 1, 0, 3, 44),
        *direct_lifecycle(11, 9, 44),
    ])


def oom_ok(*, completed_first=False):
    if completed_first:
        mid = [
            ev(2, 2, 14, 1, 6, 0, 0),
            ev(3, 1, 33, 1, 6, 0, DST),
        ]
    else:
        mid = [
            ev(2, 1, 33, 1, 6, 0, DST),
            ev(3, 2, 14, 1, 6, 0, 0),
        ]
    return ''.join([
        ev(0, 1, 29, 1, 0, PRESENT_SRC, CLIENT_SEQ),
        ev(1, 1, 30, 1, 6, 4, CLIENT_SEQ),
        *mid,
        ev(4, 1, 34, 1, 6, 0, DST),
        ev(5, 1, 29, 1, 0, COMP_SRC, 99),
        ev(6, 1, 30, 1, 0, 3, 99),
        *direct_lifecycle(7, 8, 99),
    ])


class JudgeR6Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix='r6-judge-'))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_judge(self, follow, variant='d2-inflight', *, oom=False, out=None, ring=None, rc=0):
        cell = write_cell(self.tmp / variant, follow, variant, oom=oom, out=out, ring=ring)
        return J.judge_cell(cell, variant, rc)

    def fail_code(self, follow, variant='d2-inflight', **kw):
        with self.assertRaises(J.JudgeFail) as ctx:
            self.run_judge(follow, variant, **kw)
        return ctx.exception.code

    def test_false_green_no_completed_now_fails(self):
        follow = ''.join([
            ev(0, 1, 29, 1, 0, PRESENT_SRC, CLIENT_SEQ),
            ev(1, 1, 30, 1, 6, 4, CLIENT_SEQ),
            ev(2, 1, 31, 1, 6, 1, DST),
        ])
        self.assertEqual(self.fail_code(follow), 'd2_missing_completion_cover')

    def test_wrong_generation_completed_fails(self):
        follow = ''.join([
            ev(0, 1, 29, 1, 0, PRESENT_SRC, CLIENT_SEQ),
            ev(1, 1, 30, 1, 6, 4, CLIENT_SEQ),
            ev(2, 1, 29, 1, 0, COMP_SRC),
            ev(3, 1, 31, 1, 6, 1, DST),
            ev(4, 2, 14, 99, 6, 0, 0),
            ev(5, 1, 17, 1, 8, SRC_BUF, DST),
        ])
        self.assertEqual(self.fail_code(follow), 'd2_missing_completion_cover')

    def test_x_role_completed_does_not_cover(self):
        follow = ''.join([
            ev(0, 1, 29, 1, 0, PRESENT_SRC, CLIENT_SEQ),
            ev(1, 1, 30, 1, 6, 4, CLIENT_SEQ),
            ev(2, 1, 29, 1, 0, COMP_SRC),
            ev(3, 1, 31, 1, 6, 1, DST),
            ev(4, 1, 14, 1, 6, 0, 0),
            ev(5, 1, 17, 1, 8, SRC_BUF, DST),
        ])
        self.assertEqual(self.fail_code(follow), 'd2_missing_completion_cover')

    def test_watermark_serial_gt_s_passes(self):
        self.assertEqual(self.run_judge(inflight_ok(7)), 'R6_D2_PASS d2-inflight')

    def test_exact_serial_s_still_passes(self):
        self.assertEqual(self.run_judge(inflight_ok(6)), 'R6_D2_PASS d2-inflight')

    def test_inflight_quiescent_cover_before_lease_passes(self):
        self.assertEqual(
            self.run_judge(inflight_quiescent_ok()),
            'R6_D2_PASS d2-inflight',
        )

    def test_inflight_watermark_ids_describe_t_not_present_s(self):
        self.assertEqual(
            self.run_judge(inflight_quiescent_ok(7, cover_src=88, cover_dst=99)),
            'R6_D2_PASS d2-inflight',
        )

    def test_inflight_quiescent_later_transaction_not_immediate(self):
        follow = ''.join([
            ev(0, 1, 29, 1, 0, PRESENT_SRC, CLIENT_SEQ),
            ev(1, 1, 30, 1, 6, 4, CLIENT_SEQ),
            ev(2, 1, 29, 1, 0, COMP_SRC, 43),
            ev(3, 1, 30, 1, 0, 3, 43),
            ev(4, 2, 14, 1, 7, 0, 0),
            ev(5, 1, 29, 1, 0, COMP_SRC, 44),
            ev(6, 1, 30, 1, 0, 3, 44),
            *direct_lifecycle(7, 8, 44),
        ])
        self.assertEqual(
            self.fail_code(follow),
            'd2_immediate_missing_target_lease_before_next_request',
        )

    def test_inflight_busy_requires_later_request_callback(self):
        follow = ''.join([
            ev(0, 1, 29, 1, 0, PRESENT_SRC, CLIENT_SEQ),
            ev(1, 1, 30, 1, 6, 4, CLIENT_SEQ),
            ev(2, 1, 29, 1, 0, COMP_SRC, 43),
            ev(3, 1, 30, 1, 0, 3, 43),
            ev(4, 1, 31, 1, 6, 1, DST),
            ev(5, 2, 14, 1, 7, 0, 0),
            *direct_lifecycle(6, 8, 43),
        ])
        self.assertEqual(
            self.fail_code(follow),
            'd2_later_missing_composite_request',
        )

    def test_inflight_quiescent_lease_before_cover_fails(self):
        follow = ''.join([
            ev(0, 1, 29, 1, 0, PRESENT_SRC, CLIENT_SEQ),
            ev(1, 1, 30, 1, 6, 4, CLIENT_SEQ),
            ev(2, 1, 29, 1, 0, COMP_SRC, 43),
            ev(3, 1, 30, 1, 0, 3, 43),
            ev(4, 1, 2, 1, 0, SRC_BUF, DST),
            ev(5, 2, 14, 1, 7, 0, 0),
            ev(6, 1, 6, 1, 8, SRC_BUF, DST),
            ev(7, 2, 14, 1, 8, SRC_BUF, DST),
            ev(8, 1, 17, 1, 8, SRC_BUF, DST),
        ])
        self.assertEqual(
            self.fail_code(follow),
            'd2_lease_or_publish_before_completed',
        )

    def test_inflight_callback_without_reject_or_lifecycle_fails(self):
        follow = ''.join([
            ev(0, 1, 29, 1, 0, PRESENT_SRC, CLIENT_SEQ),
            ev(1, 1, 30, 1, 6, 4, CLIENT_SEQ),
            ev(2, 1, 29, 1, 0, COMP_SRC, 43),
            ev(3, 1, 30, 1, 0, 3, 43),
            ev(4, 2, 14, 1, 7, 0, 0),
            ev(5, 1, 29, 1, 0, COMP_SRC, 44),
            ev(6, 1, 30, 1, 0, 3, 44),
        ])
        self.assertEqual(
            self.fail_code(follow),
            'd2_immediate_missing_target_lease_before_next_request',
        )

    def test_inflight_quiescent_wrong_destination_success_fails(self):
        follow = ''.join([
            ev(0, 1, 29, 1, 0, PRESENT_SRC, CLIENT_SEQ),
            ev(1, 1, 30, 1, 6, 4, CLIENT_SEQ),
            ev(2, 1, 29, 1, 0, COMP_SRC, 43),
            ev(3, 1, 30, 1, 0, 3, 43),
            ev(4, 2, 14, 1, 7, 0, 0),
            ev(5, 1, 2, 1, 0, SRC_BUF, DST),
            ev(6, 1, 6, 1, 8, SRC_BUF, DST),
            ev(7, 2, 14, 1, 8, SRC_BUF, DST),
            ev(8, 1, 17, 1, 8, SRC_BUF, 99),
            ev(9, 1, 29, 1, 0, COMP_SRC, 44),
            ev(10, 1, 30, 1, 0, 3, 44),
            *direct_lifecycle(11, 9, 44),
        ])
        self.assertEqual(
            self.fail_code(follow),
            'd2_immediate_missing_target_success',
        )

    def test_inflight_quiescent_wrong_generation_cover_fails(self):
        follow = ''.join([
            ev(0, 1, 29, 1, 0, PRESENT_SRC, CLIENT_SEQ),
            ev(1, 1, 30, 1, 6, 4, CLIENT_SEQ),
            ev(2, 1, 29, 1, 0, COMP_SRC, 43),
            ev(3, 1, 30, 1, 0, 3, 43),
            ev(4, 2, 14, 99, 7, 0, 0),
            ev(5, 1, 2, 1, 0, SRC_BUF, DST),
        ])
        self.assertEqual(self.fail_code(follow), 'd2_missing_completion_cover')

    def test_inflight_direct_completion_wrong_destination_fails(self):
        follow = ''.join([
            ev(0, 1, 29, 1, 0, PRESENT_SRC, CLIENT_SEQ),
            ev(1, 1, 30, 1, 6, 4, CLIENT_SEQ),
            ev(2, 1, 29, 1, 0, COMP_SRC, 43),
            ev(3, 1, 30, 1, 0, 3, 43),
            ev(4, 2, 14, 1, 7, 88, 99),
            ev(5, 1, 2, 1, 0, SRC_BUF, DST),
            ev(6, 1, 6, 1, 8, SRC_BUF, DST),
            ev(7, 2, 14, 1, 8, SRC_BUF, 99),
            ev(8, 1, 17, 1, 8, SRC_BUF, DST),
            ev(9, 1, 29, 1, 0, COMP_SRC, 44),
            ev(10, 1, 30, 1, 0, 3, 44),
            *direct_lifecycle(11, 9, 44),
        ])
        self.assertEqual(
            self.fail_code(follow),
            'd2_immediate_missing_target_completion',
        )

    def test_publish_before_watermark_fails(self):
        follow = ''.join([
            ev(0, 1, 29, 1, 0, PRESENT_SRC, CLIENT_SEQ),
            ev(1, 1, 30, 1, 6, 4, CLIENT_SEQ),
            ev(2, 1, 29, 1, 0, COMP_SRC),
            ev(3, 1, 30, 1, 0, 3, 0),
            ev(4, 1, 31, 1, 6, 1, DST),
            ev(5, 1, 6, 1, 8, SRC_BUF, DST),
            ev(6, 2, 14, 1, 7, 0, 0),
            ev(7, 1, 17, 1, 8, SRC_BUF, DST),
        ])
        self.assertEqual(self.fail_code(follow), 'd2_lease_or_publish_before_completed')

    def test_logcat_line_reorder_sorts_by_seq(self):
        lines = inflight_ok(7).splitlines(True)
        follow = ''.join(reversed(lines))
        self.assertEqual(self.run_judge(follow), 'R6_D2_PASS d2-inflight')

    def test_duplicate_seq_fails(self):
        follow = inflight_ok(7) + ev(4, 2, 14, 1, 7, 0, 0)
        self.assertEqual(self.fail_code(follow), 'telemetry_seq_duplicate')

    def test_gap_without_ring_fails(self):
        follow = ''.join([
            ev(0, 1, 30, 1, 6, 4, CLIENT_SEQ),
            ev(2, 1, 31, 1, 6, 1, DST),
        ])
        self.assertEqual(self.fail_code(follow), 'telemetry_seq_gap')

    def test_gap_filled_by_ring_passes(self):
        lines = inflight_ok(7).splitlines(True)
        ring = next(line for line in lines if 'seq=5 ' in line)
        follow = ''.join(line for line in lines if 'seq=5 ' not in line)
        self.assertEqual(
            self.run_judge(follow, ring=ring),
            'R6_D2_PASS d2-inflight',
        )

    def test_pixels_only_without_later_success_fails(self):
        follow = ''.join([
            ev(0, 1, 29, 1, 0, PRESENT_SRC, CLIENT_SEQ),
            ev(1, 1, 30, 1, 6, 4, CLIENT_SEQ),
            ev(2, 1, 29, 1, 0, COMP_SRC, 43),
            ev(3, 1, 30, 1, 0, 3, 43),
            ev(4, 1, 31, 1, 6, 1, DST),
            ev(5, 2, 14, 1, 7, 0, 0),
            ev(6, 1, 29, 1, 0, COMP_SRC, 44),
            ev(7, 1, 30, 1, 0, 3, 44),
            ev(8, 1, 2, 1, 0, SRC_BUF, DST),
            ev(9, 1, 6, 1, 8, SRC_BUF, DST),
            ev(10, 2, 14, 1, 8, SRC_BUF, DST),
        ])
        self.assertEqual(
            self.fail_code(follow),
            'd2_later_missing_target_success',
        )

    def test_later_success_wrong_destination_fails(self):
        follow = ''.join([
            ev(0, 1, 29, 1, 0, PRESENT_SRC, CLIENT_SEQ),
            ev(1, 1, 30, 1, 6, 4, CLIENT_SEQ),
            ev(2, 1, 29, 1, 0, COMP_SRC, 43),
            ev(3, 1, 30, 1, 0, 3, 43),
            ev(4, 1, 31, 1, 6, 1, DST),
            ev(5, 2, 14, 1, 7, 0, 0),
            ev(6, 1, 29, 1, 0, COMP_SRC, 44),
            ev(7, 1, 30, 1, 0, 3, 44),
            ev(8, 1, 2, 1, 0, SRC_BUF, DST),
            ev(9, 1, 6, 1, 8, SRC_BUF, DST),
            ev(10, 2, 14, 1, 8, SRC_BUF, DST),
            ev(11, 1, 17, 1, 8, SRC_BUF, 99),
        ])
        self.assertEqual(
            self.fail_code(follow),
            'd2_later_missing_target_success',
        )

    def test_present_callback_unpaired_fails(self):
        follow = ''.join([
            ev(0, 1, 29, 1, 0, PRESENT_SRC, 99),
            ev(1, 1, 30, 1, 6, 4, CLIENT_SEQ),
            ev(2, 1, 31, 1, 6, 1, DST),
            ev(3, 2, 14, 1, 7, 0, 0),
            ev(4, 1, 17, 1, 8, SRC_BUF, DST),
        ])
        self.assertEqual(self.fail_code(follow), 'd2_present_request_callback_unpaired')

    def test_missing_prefix_without_ring_fails(self):
        lines = inflight_ok(7).splitlines(True)
        follow = ''.join(line for line in lines if 'seq=0 ' not in line)
        self.assertEqual(self.fail_code(follow), 'telemetry_seq_prefix')

    def test_missing_prefix_filled_by_ring_passes(self):
        lines = inflight_ok(7).splitlines(True)
        ring = next(line for line in lines if 'seq=0 ' in line)
        follow = ''.join(line for line in lines if 'seq=0 ' not in line)
        self.assertEqual(
            self.run_judge(follow, ring=ring),
            'R6_D2_PASS d2-inflight',
        )

    def test_oom_early_ack_now_fails(self):
        follow = ''.join([
            ev(0, 1, 29, 1, 0, PRESENT_SRC, CLIENT_SEQ),
            ev(1, 1, 30, 1, 6, 4, CLIENT_SEQ),
            ev(2, 1, 32, 1, 6, 0, 0),
            ev(3, 2, 14, 1, 6, 0, 0),
            ev(4, 1, 29, 1, 0, COMP_SRC),
        ])
        self.assertEqual(self.fail_code(follow, 'd2-oom', oom=True), 'd2_oom_unexpected_early_ack')

    def test_oom_env_without_requeue_marker_fails(self):
        follow = ''.join([
            ev(0, 1, 29, 1, 0, PRESENT_SRC, CLIENT_SEQ),
            ev(1, 1, 30, 1, 6, 4, CLIENT_SEQ),
            ev(2, 2, 14, 1, 6, 0, 0),
            ev(3, 1, 34, 1, 6, 0, DST),
            ev(4, 1, 29, 1, 0, COMP_SRC, 99),
            ev(5, 1, 30, 1, 8, 3, 99),
            ev(6, 1, 17, 1, 8, SRC_BUF, DST),
        ])
        self.assertEqual(self.fail_code(follow, 'd2-oom', oom=True), 'd2_oom_missing_requeue_failed')

    def test_oom_requeue_without_completion_fails(self):
        follow = ''.join([
            ev(0, 1, 29, 1, 0, PRESENT_SRC, CLIENT_SEQ),
            ev(1, 1, 30, 1, 6, 4, CLIENT_SEQ),
            ev(2, 1, 33, 1, 6, 0, DST),
        ])
        self.assertEqual(self.fail_code(follow, 'd2-oom', oom=True), 'd2_missing_completion_cover')

    def test_oom_completion_without_ack_fails(self):
        follow = ''.join([
            ev(0, 1, 29, 1, 0, PRESENT_SRC, CLIENT_SEQ),
            ev(1, 1, 30, 1, 6, 4, CLIENT_SEQ),
            ev(2, 1, 33, 1, 6, 0, DST),
            ev(3, 2, 14, 1, 6, 0, 0),
            ev(4, 1, 29, 1, 0, COMP_SRC, 99),
            ev(5, 1, 17, 1, 8, SRC_BUF, DST),
        ])
        self.assertEqual(self.fail_code(follow, 'd2-oom', oom=True), 'd2_oom_missing_ack_after_completed')

    def test_oom_ack_before_completion_fails(self):
        follow = ''.join([
            ev(0, 1, 29, 1, 0, PRESENT_SRC, CLIENT_SEQ),
            ev(1, 1, 30, 1, 6, 4, CLIENT_SEQ),
            ev(2, 1, 33, 1, 6, 0, DST),
            ev(3, 1, 34, 1, 6, 0, DST),
            ev(4, 2, 14, 1, 6, 0, 0),
            ev(5, 1, 29, 1, 0, COMP_SRC, 99),
            ev(6, 1, 30, 1, 8, 3, 99),
            ev(7, 1, 17, 1, 8, SRC_BUF, DST),
        ])
        self.assertEqual(self.fail_code(follow, 'd2-oom', oom=True), 'd2_oom_ack_before_cover_or_requeue')

    def test_oom_wait_shape_passes(self):
        self.assertEqual(self.run_judge(oom_ok(), 'd2-oom', oom=True), 'R6_D2_PASS d2-oom')

    def test_oom_completed_before_requeue_detection_passes(self):
        self.assertEqual(
            self.run_judge(oom_ok(completed_first=True), 'd2-oom', oom=True),
            'R6_D2_PASS d2-oom',
        )

    def test_oom_later_request_without_success_fails(self):
        follow = ''.join([
            ev(0, 1, 29, 1, 0, PRESENT_SRC, CLIENT_SEQ),
            ev(1, 1, 30, 1, 6, 4, CLIENT_SEQ),
            ev(2, 1, 33, 1, 6, 0, DST),
            ev(3, 2, 14, 1, 6, 0, 0),
            ev(4, 1, 34, 1, 6, 0, DST),
            ev(5, 1, 29, 1, 0, COMP_SRC, 99),
            ev(6, 1, 30, 1, 0, 3, 99),
        ])
        self.assertEqual(
            self.fail_code(follow, 'd2-oom', oom=True),
            'd2_oom_missing_target_lease',
        )

    def test_oom_success_before_later_request_fails(self):
        follow = ''.join([
            ev(0, 1, 29, 1, 0, PRESENT_SRC, CLIENT_SEQ),
            ev(1, 1, 30, 1, 6, 4, CLIENT_SEQ),
            ev(2, 1, 33, 1, 6, 0, DST),
            ev(3, 2, 14, 1, 6, 0, DST),
            ev(4, 1, 34, 1, 6, 0, DST),
            ev(5, 1, 17, 1, 8, SRC_BUF, DST),
            ev(6, 1, 29, 1, 0, COMP_SRC, 99),
            ev(7, 1, 30, 1, 0, 3, 99),
        ])
        self.assertEqual(
            self.fail_code(follow, 'd2-oom', oom=True),
            'd2_oom_missing_target_lease',
        )

    def test_oom_later_request_callback_must_pair(self):
        follow = ''.join([
            ev(0, 1, 29, 1, 0, PRESENT_SRC, CLIENT_SEQ),
            ev(1, 1, 30, 1, 6, 4, CLIENT_SEQ),
            ev(2, 1, 33, 1, 6, 0, DST),
            ev(3, 2, 14, 1, 6, 0, 0),
            ev(4, 1, 34, 1, 6, 0, DST),
            ev(5, 1, 29, 1, 0, COMP_SRC, 99),
            ev(6, 1, 30, 1, 0, 3, 100),
            *direct_lifecycle(7, 8, 100),
        ])
        self.assertEqual(
            self.fail_code(follow, 'd2-oom', oom=True),
            'd2_oom_composite_request_callback_unpaired',
        )

    def test_current_95e6f96_cells_take_quiescent_branch(self):
        cells = sorted(CURRENT.glob('r6-d2-inflight*'))
        self.assertEqual(len(cells), 5)
        for src in cells:
            with self.subTest(cell=src.name):
                cell = self.tmp / src.name
                shutil.copytree(src, cell, dirs_exist_ok=True)
                self.assertEqual(
                    J.judge_cell(cell, 'd2-inflight', 0),
                    'R6_D2_PASS d2-inflight',
                )

    def test_historical_retry1_still_fail(self):
        src = HIST / 'r6-d2-inflight-retry1'
        cell = self.tmp / 'retry1'
        shutil.copytree(src, cell, dirs_exist_ok=True)
        with self.assertRaises(J.JudgeFail) as ctx:
            J.judge_cell(cell, 'd2-inflight', 0)
        self.assertIn(ctx.exception.code, (
            'd2_missing_completion_cover',
            'd2_lease_or_publish_before_completed',
            'd2_present_request_callback_unpaired',
            'd2_missing_later_direct_success',
            'telemetry_seq_prefix',
        ))

    def test_historical_d1_retry5_still_pass(self):
        src = HIST / 'r6-d1-retry5'
        cell = self.tmp / 'd1'
        shutil.copytree(src, cell, dirs_exist_ok=True)
        self.assertEqual(J.judge_cell(cell, 'd1', 0), 'R6_D1_PASS')


if __name__ == '__main__':
    raise SystemExit(unittest.main(verbosity=2))
