/* Excerpt from InitOutput.c at fdfb1ce. Not the full file. */

static void gateADoneDirect(PixmapPtr dst) {
    LorieGateAResult r;
    uint32_t reason;
    LorieGateADoneClass cls;
    if (exaGpuComp.scheduled == 0) {
        /* Nothing published (all-CPU or empty op): ownership never left. */
        gateAPairUndoReserve();
        exaCompDone++;
        memset(&exaGpuComp, 0, sizeof(exaGpuComp));
        return;
    }
    r = gateAWaitTerminal(exaGpuComp.lastSerial);
    cls = lorieGateAClassifyDirectDone(
            r,
            lorieGateAObserveFatal(&pvfb->state->gateA),
            lorieGateAObserveFirstFailureCode(&pvfb->state->gateA),
            &reason);
    if (cls != LORIE_GATEA_DONE_SUCCESS) {
        gateAXFatal("x-direct-not-success", reason, exaGpuComp.lastSerial);
    }
    lorieGateATrace(pvfb->state, LORIE_GATEA_ROLE_X,
                    LORIE_GATEA_EVENT_SEMANTIC_SUCCESS,
                    gateAPair.generation, exaGpuComp.lastSerial,
                    gateAPair.srcId, gateAPair.dstId);
    gateAPairRelockCpu();
    if (dst && dst->drawable.depth < 32) {
        gateAInternalRepair = 1;
        if (exaGpuComp.nrepair > 0 && exaGpuComp.nrepair < 32)
            lorieExaRepairDestXByteZero(dst, exaGpuComp.repair, exaGpuComp.nrepair);
        else
            lorieExaRepairDestXByteZero(dst, &exaGpuComp.repairUnion, 1);
        gateAInternalRepair = 0;
        lorieGateATrace(pvfb->state, LORIE_GATEA_ROLE_X,
                        LORIE_GATEA_EVENT_REPAIR,
                        gateAPair.generation, exaGpuComp.lastSerial,
                        gateAPair.srcId, gateAPair.dstId);
    }
    lorieGpuCopyAck(exaGpuComp.src, exaGpuComp.dstBuf);
    lorieGateATrace(pvfb->state, LORIE_GATEA_ROLE_X,
                    LORIE_GATEA_EVENT_ACK,
                    gateAPair.generation, exaGpuComp.lastSerial,
                    gateAPair.srcId, gateAPair.dstId);
    lorieGateATrace(pvfb->state, LORIE_GATEA_ROLE_X,
                    LORIE_GATEA_EVENT_PENDING_DEC,
                    gateAPair.generation, exaGpuComp.lastSerial,
                    gateAPair.srcId, 0);
    lorieGateATrace(pvfb->state, LORIE_GATEA_ROLE_X,
                    LORIE_GATEA_EVENT_PENDING_DEC,
                    gateAPair.generation, exaGpuComp.lastSerial,
                    0, gateAPair.dstId);
    if (lorieGateARegistryMarkPairReleased(gateAPair.srcId, gateAPair.dstId,
                                            exaGpuComp.lastSerial) != 0)
        gateAXFatal("x-release-registry", LORIE_GATEA_FAIL_PROTOCOL,
                    exaGpuComp.lastSerial);
    gateAPair.srcBuf = NULL;
    gateAPair.dstBuf = NULL;
    gateAPair.dstIsRoot = 0;
    lorieGateATrace(pvfb->state, LORIE_GATEA_ROLE_X,
                    LORIE_GATEA_EVENT_LEASE_RELEASE,
                    gateAPair.generation, exaGpuComp.lastSerial,
                    gateAPair.srcId, gateAPair.dstId);
    lorieGateACounterAdd(pvfb->state, LORIE_GATEA_COUNTER_LEASE_CURRENT, -1);
    gateAPair.state = GATEA_PAIR_NONE;
    gateAPair.srcId = gateAPair.dstId = 0;
    gateAPair.nonce = gateAPair.generation = 0;
    exaCompDone++;
    memset(&exaGpuComp, 0, sizeof(exaGpuComp));
}
