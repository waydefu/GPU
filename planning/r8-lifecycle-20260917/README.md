# R8 lifecycle design entrypoint

**PROPOSED DESIGN / DOCUMENTATION ONLY. No source, CI, installation or device execution is authorized by this PR.**

Base: `waydefu/GPU/main ece9f3f228b0ea2e406544c85346246559fe5095`, merged PR #7. Product source binding: `waydefu/termux-x11 fdfb1ce44b429897eda17c43bf33fbd37afe67f3`. Current recorded state remains R7-04 PASS, R7 overall IN PROGRESS, R8 NOT RUN. R7 completion is a **runtime** prerequisite, not a reason to block this design.

Read only:
1. [R8-DESIGN.md](R8-DESIGN.md) — decisions, lifetime/ordering, coverage and exact source authority.
2. [fixture-interface.md](fixture-interface.md) — proposed support interface, collection and judge contract.
3. [lifecycle-cell-spec.json](lifecycle-cell-spec.json) — ten mandatory runtime subcells.
4. [judge-negative-cases.json](judge-negative-cases.json) — false-green and legal-boundary vectors.
5. [IMPLEMENTATION-PLAN.md](IMPLEMENTATION-PLAN.md) — bounded source/host/CI/device work packages and grant boundaries.

This resolves NEXT-014's design topics into explicit proposals. It does **not** assert DESIGN_FROZEN, HOST_VERIFIED or R8 PASS. Accept the decisions before NEXT-015 implementation. The first work package is R8-I01, host parser/oracle and source-bound observations; no R7-04/B-2 rerun follows from this docs PR.

Decisions: destroy before ACK; compare semantic partial order, not log arrival; capacity is **16 buffer slots**, pending imports8; test-only registration interface for C4/C5; P1 invokes the real destructor guard; live pending and final role-specific snapshots; Present event36 is entry evidence, not completion proof; R8-D requires a real deferred GPU_COPY_DONE and can be INVALID if overlap is not constructed.

No sleeps, renderer stalls, forged completion records, expanded pixel tolerance, silent retry, shared ABI change, ownerRef/LRU/root-ready redesign or Stable/HDMI mutation. No actual source mutation occurs here. Production lifecycle gaps, R9/R10 and dedicated UWQHD remain outside this PR.

Future runtime order: C1 → C2 → C3-window → C3-disconnect → C4 → C5-full → C5-overflow → D → P1 → P2. Each is a fresh X session and unique evidence directory. Fail-fast. A batch grant can name this exact list; no repeated confirmation is needed inside that already authorized list, but no unnamed retry is implied.
