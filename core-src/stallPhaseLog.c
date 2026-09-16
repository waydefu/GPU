/* Observe-only excerpt from
 * src/f8-ahb-gatea-stall-diag/lorie/src/main/cpp/lorie/renderer.cpp
 * HEAD 27d8d1b4fcfc5456bac8720d36110eeeb7cbc9d3
 *
 * Markers wrap eglSwapBuffers and the post-swap next-buffer
 * eglClientWaitSync(..., EGL_FOREVER). No timeout / ABI / Present change.
 */

static uint64_t stallPhaseMonoNs(void) {
    struct timespec ts;
    if (clock_gettime(CLOCK_MONOTONIC, &ts) != 0)
        return 0;
    return (uint64_t) ts.tv_sec * 1000000000ull + (uint64_t) ts.tv_nsec;
}

static void stallPhaseLog(struct lorie_shared_server_state *st, const char *phase,
                          const int *result) {
    uint64_t completed = 0;
    uint32_t rd = 0, wr = 0;
    if (st) {
        completed = lorieGateAObserveCompleted(&st->gpuCopyQueue.completedSerial);
        rd = lorieGateAObserveReadIndex(&st->gpuCopyQueue.readIndex);
        wr = lorieGateAObserveWriteIndex(&st->gpuCopyQueue.writeIndex);
    }
    if (result)
        __android_log_print(ANDROID_LOG_INFO, "LorieNative",
            "STALL_PHASE phase=%s mono_ns=%llu tid=%d result=%d completedSerial=%llu readIndex=%u writeIndex=%u",
            phase, (unsigned long long) stallPhaseMonoNs(), (int) gettid(), *result,
            (unsigned long long) completed, rd, wr);
    else
        __android_log_print(ANDROID_LOG_INFO, "LorieNative",
            "STALL_PHASE phase=%s mono_ns=%llu tid=%d completedSerial=%llu readIndex=%u writeIndex=%u",
            phase, (unsigned long long) stallPhaseMonoNs(), (int) gettid(),
            (unsigned long long) completed, rd, wr);
}

/* redrawLocked presentation tail (semantics unchanged): */
#if 0
    stallPhaseLog(state, "SWAP_ENTER", nullptr);
    swap_result = eglSwapBuffers(egl_display, sfc);
    stallPhaseLog(state, "SWAP_EXIT", &swap_result_i);
    /* 1x1 glClear */
    stallPhaseLog(state, "NEXT_FENCE_ENTER", nullptr);
    wait_result = lorieEglClientWaitSyncKHR(..., EGL_FOREVER);
    stallPhaseLog(state, "NEXT_FENCE_EXIT", &wait_result_i);
#endif
