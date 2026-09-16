/* Excerpt from lorie/src/main/cpp/lorie/InitOutput.c
 * Repair lineage: src/f8-ahb-gatea-exa-timeout
 * branch fix/gatea-exa-composite-timeout-20260916 (uncommitted on workstation)
 *
 * Invariant: no GPU completion proof -> no client-visible Composite Done.
 */

void lorieGpuCopyWaitForPresentOrFatal(uint64_t serial) {
    if (serial == 0)
        gateAXFatal("x-present-copy-wait", LORIE_GATEA_FAIL_PROTOCOL, 0);
    if (!lorieGpuCopyWait(serial, 2000))
        gateAXFatal("x-present-copy-wait", LORIE_GATEA_FAIL_TIMEOUT, serial);
}

static void lorieGpuCopyWaitForCompositeOrFatal(uint64_t serial, int scheduled) {
    if (serial == 0)
        gateAXFatal("x-exa-composite-wait", LORIE_GATEA_FAIL_PROTOCOL, 0);
    if (!lorieGpuCopyWait(serial, 2000)) {
        log(ERROR, "EXA GPU composite wait timeout serial=%llu scheduled=%d",
            (unsigned long long) serial, scheduled);
        gateAXFatal("x-exa-composite-wait", LORIE_GATEA_FAIL_TIMEOUT, serial);
    }
}

/*
 * lorieExaDoneComposite scheduled path (legacy, not Gate A direct):
 *
 *     if (exaGpuComp.scheduled) {
 *         lorieGpuCopyWaitForCompositeOrFatal(exaGpuComp.lastSerial, exaGpuComp.scheduled);
 *         // repair / ack / Gcomp Done only after wait success
 *     }
 *
 * Replaces:
 *     if (!lorieGpuCopyWait(exaGpuComp.lastSerial, 2000))
 *         log(ERROR, "EXA GPU composite wait timeout ...");
 *     // then repair/ack/Done even on timeout  <-- FORBIDDEN
 */
