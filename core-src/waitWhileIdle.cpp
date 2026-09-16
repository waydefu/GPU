/* Excerpt of CASE_LOOP wakeup policy from 7549e36.
 * Not a buildable unit. Device still has observational feeaa56; this SHA is
 * not installed. EXA 2000 ms budget is unchanged. Clock is CLOCK_MONOTONIC. */
#define LORIE_GATEA_FENCE_TIMEOUT_NS 2000000000ull
#define LORIE_RENDERER_FRAME_WAIT_NS 8000000L

void Renderer::waitWhileIdle(bool *waitingForBuffers) {
    while (shouldWait(waitingForBuffers)) {
        /* Sticky GPU-copy predicate. X publishes writeIndex without stateLock,
         * then signals rendererCond. Recheck after shouldWait() closed most of
         * the lost-wakeup window; the timed wait bounds the rest. */
        if (state && lorieGateAObserveReadIndex(&state->gpuCopyQueue.readIndex)
                != lorieGateAObserveWriteIndex(&state->gpuCopyQueue.writeIndex))
            break;
        if (state && state->waitForNextFrame) {
            struct timespec deadline;
            /* stateCond is initialized CLOCK_MONOTONIC. Signal does not use
             * the clock; X can keep signaling. Do not fall back to unbounded
             * wait if the deadline cannot be formed. */
            if (clock_gettime(CLOCK_MONOTONIC, &deadline) != 0)
                abort();
            deadline.tv_nsec += LORIE_RENDERER_FRAME_WAIT_NS;
            if (deadline.tv_nsec >= 1000000000L) {
                deadline.tv_sec++;
                deadline.tv_nsec -= 1000000000L;
            }
            pthread_cond_timedwait(stateCond, &stateLock, &deadline);
        } else {
            pthread_cond_wait(stateCond, &stateLock);
        }
    }
}
