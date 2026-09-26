// FEAS-03 info addendum (not judged): where the CPU time of the Vulkan split copy goes.
// 1200x2464 exact-size dma-buf -> AHB, per iteration:
//   rec   vkResetCommandBuffer + record         (thread CPU)
//   sub   vkQueueSubmit                          (thread CPU)
//   waitF vkWaitForFences                        (wall / thread CPU)  -- set 1
//   waitP vkGetFenceStatus poll + 100us sleep   (wall / thread CPU)  -- set 2
//   tail  2-row memcpy into an already-locked AHB (thread CPU)
//   lock  AHardwareBuffer_lock+unlock of the 12 MB AHB (thread CPU) -- what FEAS-03 timing paid per frame
#include <time.h>
#include "feas03_body.inc"
static PFN_vkGetFenceStatus v_fence_status;
#define N 41
static double med(double *a) { qsort(a + 1, N - 1, sizeof(double), cmp_d); return a[N / 2]; }
int main(void) {
    if (load()) return 1;
    void *nw = dlopen("/system/lib64/libnativewindow.so", RTLD_NOW | RTLD_LOCAL);
    ahb_allocate = dlsym(nw, "AHardwareBuffer_allocate"); ahb_describe = dlsym(nw, "AHardwareBuffer_describe");
    ahb_lock = dlsym(nw, "AHardwareBuffer_lock"); ahb_unlock = dlsym(nw, "AHardwareBuffer_unlock");
    if (vk_init()) return 1;
    v_destroy_buffer = (PFN_vkDestroyBuffer) g_gdpa(dev, "vkDestroyBuffer");
    v_free_memory = (PFN_vkFreeMemory) g_gdpa(dev, "vkFreeMemory");
    v_fence_status = (PFN_vkGetFenceStatus) g_gdpa(dev, "vkGetFenceStatus");
    VkCommandPoolCreateInfo cpi = { VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO, NULL, VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT, qf };
    VkCommandPool pool; v_vkCreateCommandPool(dev, &cpi, NULL, &pool);
    VkCommandBufferAllocateInfo cai = { VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO, NULL, pool, VK_COMMAND_BUFFER_LEVEL_PRIMARY, 1 };
    VkCommandBuffer cb; v_vkAllocateCommandBuffers(dev, &cai, &cb);
    VkFenceCreateInfo fci = { VK_STRUCTURE_TYPE_FENCE_CREATE_INFO, NULL, 0 };
    VkFence f; v_vkCreateFence(dev, &fci, NULL, &f);
    size_t dsize = ((size_t) PITCH * BIG_H + 4095) & ~(size_t) 4095;
    int fd = heap_alloc_size(dsize);
    AHardwareBuffer *ahb = ahb_new(W, BIG_H);
    uint8_t *src = mmap(NULL, dsize, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    for (size_t i = 0; i < dsize; i++) src[i] = (uint8_t) (i * 2654435761u >> 13);
    VkDeviceMemory mem, imem; VkBuffer buf; VkDeviceSize req, oh; VkImage img;
    int R = rows_fitting(BIG_H, dsize, &oh);
    if (import_mem(fd, dsize, &mem) || make_buffer(rows_bytes(R), &buf, &req) || v_vkBindBufferMemory(dev, buf, mem, 0) ||
        import_ahb(ahb, W, BIG_H, &img, &imem, "big")) { printf("SETUP=FAIL\n"); return 1; }
    AHardwareBuffer_Desc d; ahb_describe(ahb, &d);
    double rec[N], sub[N], ww[N], wc[N], tail[N], lk[N], lkw[N];
    for (int set = 0; set < 2; set++) {
        for (int i = 0; i < N; i++) {
            double c0 = now_ms(CLOCK_THREAD_CPUTIME_ID);
            record(cb, buf, img, W, (uint32_t) R, PITCH / 4, 1, VK_NULL_HANDLE);
            double c1 = now_ms(CLOCK_THREAD_CPUTIME_ID);
            VkSubmitInfo si = { VK_STRUCTURE_TYPE_SUBMIT_INFO, NULL, 0, NULL, NULL, 1, &cb, 0, NULL };
            v_vkQueueSubmit(queue, 1, &si, f);
            double c2 = now_ms(CLOCK_THREAD_CPUTIME_ID), w2 = now_ms(CLOCK_MONOTONIC);
            if (set == 0) v_vkWaitForFences(dev, 1, &f, VK_TRUE, 5000000000ull);
            else while (v_fence_status(dev, f) == VK_NOT_READY) { struct timespec t = { 0, 100000 }; nanosleep(&t, NULL); }
            ww[i] = now_ms(CLOCK_MONOTONIC) - w2; wc[i] = now_ms(CLOCK_THREAD_CPUTIME_ID) - c2;
            v_vkResetFences(dev, 1, &f);
            rec[i] = c1 - c0; sub[i] = c2 - c1;
        }
        printf("SPLIT_%s rows_gpu=%d rec_cpu_ms=%.3f submit_cpu_ms=%.3f wait_wall_ms=%.3f wait_cpu_ms=%.3f (median of %d)\n",
               set ? "POLL100US" : "WAITFENCES", R, med(rec), med(sub), med(ww), med(wc), N - 1);
    }
    void *p;
    ahb_lock(ahb, AHARDWAREBUFFER_USAGE_CPU_WRITE_OFTEN | AHARDWAREBUFFER_USAGE_CPU_READ_OFTEN, -1, NULL, &p);
    for (int i = 0; i < N; i++) {
        double c0 = now_ms(CLOCK_THREAD_CPUTIME_ID);
        for (int y = R; y < BIG_H; y++) memcpy((uint8_t *) p + (size_t) y * d.stride * 4, src + (size_t) y * PITCH, (size_t) W * 4);
        tail[i] = now_ms(CLOCK_THREAD_CPUTIME_ID) - c0;
    }
    ahb_unlock(ahb, NULL);
    for (int i = 0; i < N; i++) {
        double c0 = now_ms(CLOCK_THREAD_CPUTIME_ID), w0 = now_ms(CLOCK_MONOTONIC);
        ahb_lock(ahb, AHARDWAREBUFFER_USAGE_CPU_WRITE_OFTEN | AHARDWAREBUFFER_USAGE_CPU_READ_OFTEN, -1, NULL, &p);
        ahb_unlock(ahb, NULL);
        lk[i] = now_ms(CLOCK_THREAD_CPUTIME_ID) - c0; lkw[i] = now_ms(CLOCK_MONOTONIC) - w0;
    }
    printf("TAIL_2ROWS_LOCKED cpu_ms=%.4f | AHB_LOCK_UNLOCK_12MB cpu_ms=%.3f wall_ms=%.3f (median of %d)\n", med(tail), med(lk), med(lkw), N - 1);
    printf("DONE\n");
    return 0;
}
