/* Excerpt from InitOutput.c at fdfb1ce. Not the full file. */

static LorieGateAResult gateAWaitTerminal(uint64_t serial) {
    struct lorie_shared_server_state *st = pvfb->state;
    struct timespec t0, now;
    long elapsed;
    if (!st || serial == 0)
        return LORIE_GATEA_RESULT_FATAL;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (;;) {
        uint32_t fatal = lorieGateAObserveFatal(&st->gateA);
        uint64_t done = lorieGateAObserveCompleted(&st->gpuCopyQueue.completedSerial);
        uint64_t failed = lorieGateAObserveFirstFailed(&st->gateA);
        LorieGateAResult r = lorieGateADeriveResult(done, failed, fatal, serial);
        if (r != LORIE_GATEA_RESULT_NONE)
            return r;
        if (!lorieConnectionAlive() || !lorieRendererAvailable())
            return LORIE_GATEA_RESULT_FATAL;
        clock_gettime(CLOCK_MONOTONIC, &now);
        elapsed = (now.tv_sec - t0.tv_sec) * 1000L
            + (now.tv_nsec - t0.tv_nsec) / 1000000L;
        if (elapsed > 2000)
            return LORIE_GATEA_RESULT_FATAL;
        usleep(200);
    }
}
