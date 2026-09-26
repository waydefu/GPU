// X3-DIRECT-FEAS-02 probe: system Vulkan (Adreno) imports a client dma-buf and GPU-copies it
// into an AHardwareBuffer of the kind X3 uses for root/pixmaps. See X3-DIRECT-FEAS-02-FREEZE.md.
#define VK_USE_PLATFORM_ANDROID_KHR
#include <vulkan/vulkan.h>
#include <android/hardware_buffer.h>
#include <time.h>
#include "probe01_body.inc" /* egl_dmabuf_probe.c with main renamed: pat/fill/compare/gl helpers */

typedef int (*PFN_AHB_allocate)(const AHardwareBuffer_Desc *, AHardwareBuffer **);
typedef void (*PFN_AHB_describe)(const AHardwareBuffer *, AHardwareBuffer_Desc *);
typedef int (*PFN_AHB_lock)(AHardwareBuffer *, uint64_t, int32_t, const ARect *, void **);
typedef int (*PFN_AHB_unlock)(AHardwareBuffer *, int32_t *);
typedef EGLClientBuffer (*PFN_eglGetNativeClientBufferANDROID_)(const struct AHardwareBuffer *);
static PFN_AHB_allocate ahb_allocate;
static PFN_AHB_describe ahb_describe;
static PFN_AHB_lock ahb_lock;
static PFN_AHB_unlock ahb_unlock;

#define AHB_USAGE (AHARDWAREBUFFER_USAGE_CPU_READ_OFTEN | AHARDWAREBUFFER_USAGE_CPU_WRITE_OFTEN | \
                   AHARDWAREBUFFER_USAGE_GPU_SAMPLED_IMAGE | AHARDWAREBUFFER_USAGE_GPU_FRAMEBUFFER)
#define BIG_H 2464

static PFN_vkGetDeviceProcAddr g_gdpa;
static VkDevice dev;
static VkQueue queue;
static uint32_t qf;
static float ts_period;
static uint32_t foreign_qf = VK_QUEUE_FAMILY_FOREIGN_EXT;
#define VKD(name) static PFN_##name v_##name;
VKD(vkGetDeviceQueue) VKD(vkGetMemoryFdPropertiesKHR) VKD(vkGetAndroidHardwareBufferPropertiesANDROID)
VKD(vkCreateBuffer) VKD(vkGetBufferMemoryRequirements) VKD(vkAllocateMemory) VKD(vkBindBufferMemory)
VKD(vkCreateImage) VKD(vkBindImageMemory) VKD(vkCreateCommandPool) VKD(vkAllocateCommandBuffers)
VKD(vkBeginCommandBuffer) VKD(vkEndCommandBuffer) VKD(vkCmdPipelineBarrier) VKD(vkCmdCopyBufferToImage)
VKD(vkQueueSubmit) VKD(vkCreateFence) VKD(vkWaitForFences) VKD(vkResetFences) VKD(vkCmdWriteTimestamp)
VKD(vkCreateQueryPool) VKD(vkGetQueryPoolResults) VKD(vkCmdResetQueryPool) VKD(vkResetCommandBuffer)

static double now_ms(clockid_t c) {
    struct timespec t;
    clock_gettime(c, &t);
    return t.tv_sec * 1e3 + t.tv_nsec / 1e6;
}

static int cmp_d(const void *a, const void *b) {
    double x = *(const double *) a, y = *(const double *) b;
    return x < y ? -1 : x > y;
}

static int vk_init(void) {
    void *vk = dlopen("/system/lib64/libvulkan.so", RTLD_NOW | RTLD_LOCAL);
    if (!vk) { printf("VK=LOAD_FAIL\n"); return -1; }
    PFN_vkGetInstanceProcAddr gipa = dlsym(vk, "vkGetInstanceProcAddr");
    PFN_vkCreateInstance ci = (PFN_vkCreateInstance) gipa(NULL, "vkCreateInstance");
    VkApplicationInfo ai = { VK_STRUCTURE_TYPE_APPLICATION_INFO, NULL, "feas02", 1, NULL, 0, VK_API_VERSION_1_1 };
    VkInstanceCreateInfo ici = { VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO, NULL, 0, &ai, 0, NULL, 0, NULL };
    VkInstance inst;
    VkResult r = ci(&ici, NULL, &inst);
    if (r) { printf("VK=INSTANCE_FAIL %d\n", r); return -1; }
    PFN_vkEnumeratePhysicalDevices epd = (PFN_vkEnumeratePhysicalDevices) gipa(inst, "vkEnumeratePhysicalDevices");
    PFN_vkGetPhysicalDeviceQueueFamilyProperties qfp =
        (PFN_vkGetPhysicalDeviceQueueFamilyProperties) gipa(inst, "vkGetPhysicalDeviceQueueFamilyProperties");
    PFN_vkGetPhysicalDeviceProperties gpp = (PFN_vkGetPhysicalDeviceProperties) gipa(inst, "vkGetPhysicalDeviceProperties");
    PFN_vkEnumerateDeviceExtensionProperties ede =
        (PFN_vkEnumerateDeviceExtensionProperties) gipa(inst, "vkEnumerateDeviceExtensionProperties");
    PFN_vkCreateDevice cd = (PFN_vkCreateDevice) gipa(inst, "vkCreateDevice");
    PFN_vkGetDeviceProcAddr gdpa = (PFN_vkGetDeviceProcAddr) gipa(inst, "vkGetDeviceProcAddr"); g_gdpa = gdpa;
    uint32_t n = 1; VkPhysicalDevice pd;
    epd(inst, &n, &pd);
    if (!n) { printf("VK=NO_DEVICE\n"); return -1; }
    VkPhysicalDeviceProperties pp; gpp(pd, &pp);
    ts_period = pp.limits.timestampPeriod;
    uint32_t nq = 0; qfp(pd, &nq, NULL);
    VkQueueFamilyProperties qps[8]; if (nq > 8) nq = 8; qfp(pd, &nq, qps);
    for (qf = 0; qf < nq && !(qps[qf].queueFlags & VK_QUEUE_GRAPHICS_BIT); qf++) {}
    if (qf == nq) { printf("VK=NO_QUEUE\n"); return -1; }
    uint32_t ne = 0; ede(pd, NULL, &ne, NULL);
    VkExtensionProperties *ex = calloc(ne, sizeof *ex); ede(pd, NULL, &ne, ex);
    const char *want[] = { "VK_ANDROID_external_memory_android_hardware_buffer", "VK_KHR_external_memory_fd",
                           "VK_EXT_external_memory_dma_buf", "VK_EXT_queue_family_foreign" };
    const char *en[4]; uint32_t nen = 0;
    for (unsigned i = 0; i < 4; i++) {
        int f = 0;
        for (uint32_t j = 0; j < ne; j++) if (!strcmp(ex[j].extensionName, want[i])) f = 1;
        printf("VK_EXT %s=%d\n", want[i], f);
        if (f) en[nen++] = want[i];
        else if (i < 3) return -1;
        else foreign_qf = VK_QUEUE_FAMILY_EXTERNAL;
    }
    float prio = 1.0f;
    VkDeviceQueueCreateInfo qci = { VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO, NULL, 0, qf, 1, &prio };
    VkDeviceCreateInfo dci = { VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO, NULL, 0, 1, &qci, 0, NULL, nen, en, NULL };
    r = cd(pd, &dci, NULL, &dev);
    if (r) { printf("VK=DEVICE_FAIL %d\n", r); return -1; }
#define LD(name) if (!(v_##name = (PFN_##name) gdpa(dev, #name))) { printf("VK=PROC_FAIL %s\n", #name); return -1; }
    LD(vkGetDeviceQueue) LD(vkGetMemoryFdPropertiesKHR) LD(vkGetAndroidHardwareBufferPropertiesANDROID)
    LD(vkCreateBuffer) LD(vkGetBufferMemoryRequirements) LD(vkAllocateMemory) LD(vkBindBufferMemory)
    LD(vkCreateImage) LD(vkBindImageMemory) LD(vkCreateCommandPool) LD(vkAllocateCommandBuffers)
    LD(vkBeginCommandBuffer) LD(vkEndCommandBuffer) LD(vkCmdPipelineBarrier) LD(vkCmdCopyBufferToImage)
    LD(vkQueueSubmit) LD(vkCreateFence) LD(vkWaitForFences) LD(vkResetFences) LD(vkCmdWriteTimestamp)
    LD(vkCreateQueryPool) LD(vkGetQueryPoolResults) LD(vkCmdResetQueryPool) LD(vkResetCommandBuffer)
    v_vkGetDeviceQueue(dev, qf, 0, &queue);
    printf("VK_INIT=OK device=%s qf=%u ts_valid_bits=%u ts_period=%.3f foreign_qf=0x%x\n", pp.deviceName, qf,
           qps[qf].timestampValidBits, ts_period, foreign_qf);
    return 0;
}

static int heap_alloc_size(size_t size) {
    int heap = open("/dev/dma_heap/system", O_RDONLY | O_CLOEXEC);
    if (heap < 0) return -1;
    struct dma_heap_allocation_data a = { .len = size, .fd_flags = O_RDWR | O_CLOEXEC };
    int r = ioctl(heap, DMA_HEAP_IOCTL_ALLOC, &a);
    close(heap);
    return r < 0 ? -1 : (int) a.fd;
}

static VkResult import_dmabuf(int fd, VkDeviceSize bytes, VkBuffer *buf, VkDeviceMemory *mem, const char *tag) {
    VkMemoryFdPropertiesKHR mp = { VK_STRUCTURE_TYPE_MEMORY_FD_PROPERTIES_KHR };
    VkResult r = v_vkGetMemoryFdPropertiesKHR(dev, VK_EXTERNAL_MEMORY_HANDLE_TYPE_DMA_BUF_BIT_EXT, fd, &mp);
    printf("DMABUF_FDPROPS[%s]=%d bits=0x%x\n", tag, r, mp.memoryTypeBits);
    if (r) return r;
    VkExternalMemoryBufferCreateInfo ext = { VK_STRUCTURE_TYPE_EXTERNAL_MEMORY_BUFFER_CREATE_INFO, NULL,
                                             VK_EXTERNAL_MEMORY_HANDLE_TYPE_DMA_BUF_BIT_EXT };
    VkBufferCreateInfo bci = { VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO, &ext, 0, bytes, VK_BUFFER_USAGE_TRANSFER_SRC_BIT,
                               VK_SHARING_MODE_EXCLUSIVE, 0, NULL };
    if ((r = v_vkCreateBuffer(dev, &bci, NULL, buf))) return r;
    VkMemoryRequirements req; v_vkGetBufferMemoryRequirements(dev, *buf, &req);
    uint32_t bits = req.memoryTypeBits & mp.memoryTypeBits, t = 0;
    while (t < 32 && !(bits & (1u << t))) t++;
    off_t dsize = lseek(fd, 0, SEEK_END);
    lseek(fd, 0, SEEK_SET);
    if (t == 32 || dsize < (off_t) req.size) {
        printf("DMABUF_IMPORT[%s]=NO_TYPE bits=0x%x req=%llu dmabuf=%lld\n", tag, bits,
               (unsigned long long) req.size, (long long) dsize);
        return VK_ERROR_UNKNOWN;
    }
    int d = dup(fd);
    VkImportMemoryFdInfoKHR imp = { VK_STRUCTURE_TYPE_IMPORT_MEMORY_FD_INFO_KHR, NULL,
                                    VK_EXTERNAL_MEMORY_HANDLE_TYPE_DMA_BUF_BIT_EXT, d };
    VkMemoryAllocateInfo mai = { VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO, &imp, (VkDeviceSize) dsize, t };
    r = v_vkAllocateMemory(dev, &mai, NULL, mem);
    if (r) { close(d); printf("DMABUF_IMPORT[%s]=ALLOC_FAIL %d\n", tag, r); return r; }
    r = v_vkBindBufferMemory(dev, *buf, *mem, 0);
    printf("DMABUF_IMPORT[%s]=%s type=%u req=%llu dmabuf=%lld bind=%d\n", tag, r ? "FAIL" : "OK", t,
           (unsigned long long) req.size, (long long) dsize, r);
    return r;
}

static VkResult import_ahb(AHardwareBuffer *ahb, uint32_t w, uint32_t h, VkImage *img, VkDeviceMemory *mem, const char *tag) {
    VkAndroidHardwareBufferFormatPropertiesANDROID fp = { VK_STRUCTURE_TYPE_ANDROID_HARDWARE_BUFFER_FORMAT_PROPERTIES_ANDROID };
    VkAndroidHardwareBufferPropertiesANDROID ap = { VK_STRUCTURE_TYPE_ANDROID_HARDWARE_BUFFER_PROPERTIES_ANDROID, &fp };
    VkResult r = v_vkGetAndroidHardwareBufferPropertiesANDROID(dev, ahb, &ap);
    printf("AHB_PROPS[%s]=%d vkformat=%d external=%llu alloc=%llu bits=0x%x\n", tag, r, fp.format,
           (unsigned long long) fp.externalFormat, (unsigned long long) ap.allocationSize, ap.memoryTypeBits);
    if (r || fp.format == VK_FORMAT_UNDEFINED) return r ? r : VK_ERROR_FORMAT_NOT_SUPPORTED;
    VkExternalMemoryImageCreateInfo ext = { VK_STRUCTURE_TYPE_EXTERNAL_MEMORY_IMAGE_CREATE_INFO, NULL,
                                            VK_EXTERNAL_MEMORY_HANDLE_TYPE_ANDROID_HARDWARE_BUFFER_BIT_ANDROID };
    VkImageCreateInfo ici = { VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO, &ext, 0, VK_IMAGE_TYPE_2D, fp.format, { w, h, 1 },
                              1, 1, VK_SAMPLE_COUNT_1_BIT, VK_IMAGE_TILING_OPTIMAL,
                              VK_IMAGE_USAGE_TRANSFER_DST_BIT | VK_IMAGE_USAGE_SAMPLED_BIT,
                              VK_SHARING_MODE_EXCLUSIVE, 0, NULL, VK_IMAGE_LAYOUT_UNDEFINED };
    if ((r = v_vkCreateImage(dev, &ici, NULL, img))) { printf("AHB_IMAGE[%s]=FAIL %d\n", tag, r); return r; }
    VkMemoryDedicatedAllocateInfo ded = { VK_STRUCTURE_TYPE_MEMORY_DEDICATED_ALLOCATE_INFO, NULL, *img, VK_NULL_HANDLE };
    VkImportAndroidHardwareBufferInfoANDROID imp = { VK_STRUCTURE_TYPE_IMPORT_ANDROID_HARDWARE_BUFFER_INFO_ANDROID, &ded, ahb };
    uint32_t t = 0;
    while (t < 32 && !(ap.memoryTypeBits & (1u << t))) t++;
    VkMemoryAllocateInfo mai = { VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO, &imp, ap.allocationSize, t };
    if ((r = v_vkAllocateMemory(dev, &mai, NULL, mem))) { printf("AHB_IMPORT[%s]=ALLOC_FAIL %d\n", tag, r); return r; }
    r = v_vkBindImageMemory(dev, *img, *mem, 0);
    printf("AHB_IMPORT[%s]=%s type=%u bind=%d\n", tag, r ? "FAIL" : "OK", t, r);
    return r;
}

static void record(VkCommandBuffer cb, VkBuffer src, VkImage dst, uint32_t w, uint32_t h, uint32_t row_len,
                   int do_copy, VkQueryPool qp) {
    v_vkResetCommandBuffer(cb, 0);
    VkCommandBufferBeginInfo bi = { VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO, NULL, 0, NULL };
    v_vkBeginCommandBuffer(cb, &bi);
    if (qp) {
        v_vkCmdResetQueryPool(cb, qp, 0, 2);
        v_vkCmdWriteTimestamp(cb, VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT, qp, 0);
    }
    VkImageSubresourceRange rng = { VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1 };
    /* acquire: the dma-buf was written outside Vulkan (CPU / another process), the AHB is shared */
    VkBufferMemoryBarrier bb = { VK_STRUCTURE_TYPE_BUFFER_MEMORY_BARRIER, NULL, 0, VK_ACCESS_TRANSFER_READ_BIT,
                                 foreign_qf, qf, src, 0, VK_WHOLE_SIZE };
    VkImageMemoryBarrier ib = { VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER, NULL, 0, VK_ACCESS_TRANSFER_WRITE_BIT,
                                VK_IMAGE_LAYOUT_UNDEFINED, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, foreign_qf, qf, dst, rng };
    v_vkCmdPipelineBarrier(cb, VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT, 0, 0, NULL, 1, &bb, 1, &ib);
    if (do_copy) {
        VkBufferImageCopy reg = { 0, row_len, 0, { VK_IMAGE_ASPECT_COLOR_BIT, 0, 0, 1 }, { 0, 0, 0 }, { w, h, 1 } };
        v_vkCmdCopyBufferToImage(cb, src, dst, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, 1, &reg);
    }
    /* release both back to the foreign owner (GL / CPU lock) */
    VkBufferMemoryBarrier rbb = { VK_STRUCTURE_TYPE_BUFFER_MEMORY_BARRIER, NULL, VK_ACCESS_TRANSFER_READ_BIT, 0,
                                  qf, foreign_qf, src, 0, VK_WHOLE_SIZE };
    VkImageMemoryBarrier rb = { VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER, NULL, VK_ACCESS_TRANSFER_WRITE_BIT, 0,
                                VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, VK_IMAGE_LAYOUT_GENERAL, qf, foreign_qf, dst, rng };
    v_vkCmdPipelineBarrier(cb, VK_PIPELINE_STAGE_TRANSFER_BIT, VK_PIPELINE_STAGE_BOTTOM_OF_PIPE_BIT, 0, 0, NULL, 1, &rbb, 1, &rb);
    if (qp)
        v_vkCmdWriteTimestamp(cb, VK_PIPELINE_STAGE_BOTTOM_OF_PIPE_BIT, qp, 1);
    v_vkEndCommandBuffer(cb);
}

static VkResult submit_wait(VkCommandBuffer cb, VkFence f) {
    VkSubmitInfo si = { VK_STRUCTURE_TYPE_SUBMIT_INFO, NULL, 0, NULL, NULL, 1, &cb, 0, NULL };
    VkResult r = v_vkQueueSubmit(queue, 1, &si, f);
    if (r) return r;
    r = v_vkWaitForFences(dev, 1, &f, VK_TRUE, 5000000000ull);
    v_vkResetFences(dev, 1, &f);
    return r;
}

/* PIX_CPU: raw bytes of the AHB (as X3 reads root) vs the pattern the CPU put in the dma-buf */
static long ahb_cpu_compare(AHardwareBuffer *ahb, int v, long *bad_x_only) {
    AHardwareBuffer_Desc d; ahb_describe(ahb, &d);
    void *p;
    if (ahb_lock(ahb, AHARDWAREBUFFER_USAGE_CPU_READ_OFTEN, -1, NULL, &p)) return -1;
    long bad = 0, xo = 0;
    for (int y = 0; y < H; y++)
        for (int x = 0; x < W; x++) {
            uint8_t e[4]; pat(x, y, v, e);
            const uint8_t *a = (const uint8_t *) p + ((size_t) y * d.stride + x) * 4;
            if (memcmp(a, e, 4)) {
                bad++;
                if (!memcmp(a, e, 3)) xo++;
            }
        }
    ahb_unlock(ahb, NULL);
    if (bad_x_only) *bad_x_only = xo;
    return bad;
}

static void ahb_clear(AHardwareBuffer *ahb) {
    AHardwareBuffer_Desc d; ahb_describe(ahb, &d);
    void *p;
    if (ahb_lock(ahb, AHARDWAREBUFFER_USAGE_CPU_WRITE_OFTEN, -1, NULL, &p)) return;
    memset(p, 0, (size_t) d.stride * d.height * 4);
    ahb_unlock(ahb, NULL);
}

static AHardwareBuffer *ahb_new(uint32_t w, uint32_t h) {
    AHardwareBuffer_Desc d = { .width = w, .height = h, .layers = 1,
                               .format = AHARDWAREBUFFER_FORMAT_R8G8B8X8_UNORM, .usage = AHB_USAGE };
    AHardwareBuffer *b = NULL;
    int r = ahb_allocate(&d, &b);
    if (r || !b) { printf("AHB_ALLOC=FAIL %d\n", r); return NULL; }
    ahb_describe(b, &d);
    printf("AHB_ALLOC=OK %ux%u stride=%u format=%u\n", d.width, d.height, d.stride, d.format);
    return b;
}

static void timing(VkCommandBuffer cb, VkFence f) {
    size_t bytes = ((size_t) PITCH * BIG_H + 4095) & ~(size_t) 4095;
    int fd = heap_alloc_size(bytes);
    AHardwareBuffer *ahb = ahb_new(W, BIG_H);
    if (fd < 0 || !ahb) { printf("TIMING=NOT_RUN\n"); return; }
    uint8_t *src = mmap(NULL, bytes, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    memset(src, 0x5a, bytes);
    AHardwareBuffer_Desc d; ahb_describe(ahb, &d);
    enum { N = 21 };
    double wall[N], cpu[N], gpu[N];
    for (int mode = 0; mode < 2; mode++) { /* 0: no DMA_BUF_IOCTL_SYNC (X3 today), 1: with sync */
        void *dst;
        ahb_lock(ahb, AHARDWAREBUFFER_USAGE_CPU_WRITE_OFTEN | AHARDWAREBUFFER_USAGE_CPU_READ_OFTEN, -1, NULL, &dst);
        for (int i = 0; i < N; i++) {
            double w0 = now_ms(CLOCK_MONOTONIC), c0 = now_ms(CLOCK_THREAD_CPUTIME_ID);
            struct dma_buf_sync s = { DMA_BUF_SYNC_START | DMA_BUF_SYNC_READ };
            if (mode) ioctl(fd, DMA_BUF_IOCTL_SYNC, &s);
            for (int y = 0; y < BIG_H; y++)
                memcpy((uint8_t *) dst + (size_t) y * d.stride * 4, src + (size_t) y * PITCH, (size_t) W * 4);
            s.flags = DMA_BUF_SYNC_END | DMA_BUF_SYNC_READ;
            if (mode) ioctl(fd, DMA_BUF_IOCTL_SYNC, &s);
            wall[i] = now_ms(CLOCK_MONOTONIC) - w0; cpu[i] = now_ms(CLOCK_THREAD_CPUTIME_ID) - c0;
        }
        ahb_unlock(ahb, NULL);
        qsort(wall + 1, N - 1, sizeof(double), cmp_d); qsort(cpu + 1, N - 1, sizeof(double), cmp_d);
        printf("TIMING_CPU_MEMCPY[%s] %ux%d wall_median_ms=%.3f cpu_median_ms=%.3f (n=%d, first dropped)\n",
               mode ? "sync" : "nosync", W, BIG_H, wall[N / 2], cpu[N / 2], N - 1);
    }
    VkBuffer vb; VkDeviceMemory vbm; VkImage vi; VkDeviceMemory vim;
    if (import_dmabuf(fd, (VkDeviceSize) PITCH * BIG_H, &vb, &vbm, "big") ||
        import_ahb(ahb, W, BIG_H, &vi, &vim, "big")) { printf("TIMING_VK=NOT_RUN\n"); return; }
    VkQueryPoolCreateInfo qpi = { VK_STRUCTURE_TYPE_QUERY_POOL_CREATE_INFO, NULL, 0, VK_QUERY_TYPE_TIMESTAMP, 2, 0 };
    VkQueryPool qp; v_vkCreateQueryPool(dev, &qpi, NULL, &qp);
    for (int i = 0; i < N; i++) {
        double w0 = now_ms(CLOCK_MONOTONIC), c0 = now_ms(CLOCK_THREAD_CPUTIME_ID);
        record(cb, vb, vi, W, BIG_H, PITCH / 4, 1, qp);
        VkResult r = submit_wait(cb, f);
        wall[i] = now_ms(CLOCK_MONOTONIC) - w0; cpu[i] = now_ms(CLOCK_THREAD_CPUTIME_ID) - c0;
        uint64_t ts[2] = { 0, 0 };
        v_vkGetQueryPoolResults(dev, qp, 0, 2, sizeof ts, ts, sizeof(uint64_t), VK_QUERY_RESULT_64_BIT | VK_QUERY_RESULT_WAIT_BIT);
        gpu[i] = (double) (ts[1] - ts[0]) * ts_period / 1e6;
        if (r) { printf("TIMING_VK submit=%d\n", r); return; }
    }
    qsort(wall + 1, N - 1, sizeof(double), cmp_d); qsort(cpu + 1, N - 1, sizeof(double), cmp_d);
    qsort(gpu + 1, N - 1, sizeof(double), cmp_d);
    printf("TIMING_VK_COPY %ux%d wall_median_ms=%.3f cpu_median_ms=%.3f gpu_median_ms=%.3f (n=%d, first dropped; includes command re-record)\n",
           W, BIG_H, wall[N / 2], cpu[N / 2], gpu[N / 2], N - 1);
    /* spot-check the big copy too */
    void *p; long bad = 0;
    if (!ahb_lock(ahb, AHARDWAREBUFFER_USAGE_CPU_READ_OFTEN, -1, NULL, &p)) {
        for (int y = 0; y < BIG_H; y++)
            for (int x = 0; x < W; x++)
                if (memcmp((uint8_t *) p + ((size_t) y * d.stride + x) * 4, src + (size_t) y * PITCH + x * 4, 4)) bad++;
        ahb_unlock(ahb, NULL);
    }
    printf("TIMING_VK_COPY_CHECK mismatch=%ld of=%d\n", bad, W * BIG_H);
}

__attribute__((unused)) static int feas02_main(void) {
    if (load()) return 1;
    void *nw = dlopen("/system/lib64/libnativewindow.so", RTLD_NOW | RTLD_LOCAL);
    ahb_allocate = nw ? dlsym(nw, "AHardwareBuffer_allocate") : NULL;
    ahb_describe = nw ? dlsym(nw, "AHardwareBuffer_describe") : NULL;
    ahb_lock = nw ? dlsym(nw, "AHardwareBuffer_lock") : NULL;
    ahb_unlock = nw ? dlsym(nw, "AHardwareBuffer_unlock") : NULL;
    if (!ahb_allocate || !ahb_describe || !ahb_lock || !ahb_unlock) { printf("AHB=LOAD_FAIL\n"); return 1; }

    dpy = p_eglGetDisplay(EGL_DEFAULT_DISPLAY);
    EGLint maj, min;
    if (!p_eglInitialize(dpy, &maj, &min)) { printf("EGL_INIT=FAIL\n"); return 1; }
    p_eglBindAPI(EGL_OPENGL_ES_API);
    EGLint cattr[] = { EGL_RENDERABLE_TYPE, EGL_OPENGL_ES2_BIT, EGL_SURFACE_TYPE, EGL_PBUFFER_BIT,
                       EGL_RED_SIZE, 8, EGL_GREEN_SIZE, 8, EGL_BLUE_SIZE, 8, EGL_ALPHA_SIZE, 8, EGL_NONE };
    EGLConfig cfg; EGLint nc = 0; p_eglChooseConfig(dpy, cattr, &cfg, 1, &nc);
    EGLint xattr[] = { EGL_CONTEXT_CLIENT_VERSION, 2, EGL_NONE };
    EGLContext ctx = p_eglCreateContext(dpy, cfg, EGL_NO_CONTEXT, xattr);
    EGLint sattr[] = { EGL_WIDTH, 16, EGL_HEIGHT, 16, EGL_NONE };
    EGLSurface surf = p_eglCreatePbufferSurface(dpy, cfg, sattr);
    if (!nc || !ctx || !surf || !p_eglMakeCurrent(dpy, surf, surf, ctx)) { printf("CTX=FAIL\n"); return 1; }
    p_eglCreateImageKHR = (PFNEGLCREATEIMAGEKHRPROC) p_eglGetProcAddress("eglCreateImageKHR");
    p_eglDestroyImageKHR = (PFNEGLDESTROYIMAGEKHRPROC) p_eglGetProcAddress("eglDestroyImageKHR");
    p_glEGLImageTargetTexture2DOES = (PFNGLEGLIMAGETARGETTEXTURE2DOESPROC) p_eglGetProcAddress("glEGLImageTargetTexture2DOES");
    PFN_eglGetNativeClientBufferANDROID_ gncb =
        (PFN_eglGetNativeClientBufferANDROID_) p_eglGetProcAddress("eglGetNativeClientBufferANDROID");
    if (!p_eglCreateImageKHR || !p_glEGLImageTargetTexture2DOES || !gncb || gl_setup()) { printf("GL=FAIL\n"); return 1; }

    if (vk_init()) return 1;
    VkCommandPoolCreateInfo cpi = { VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO, NULL,
                                    VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT, qf };
    VkCommandPool pool; v_vkCreateCommandPool(dev, &cpi, NULL, &pool);
    VkCommandBufferAllocateInfo cai = { VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO, NULL, pool,
                                        VK_COMMAND_BUFFER_LEVEL_PRIMARY, 1 };
    VkCommandBuffer cb; v_vkAllocateCommandBuffers(dev, &cai, &cb);
    VkFenceCreateInfo fci = { VK_STRUCTURE_TYPE_FENCE_CREATE_INFO, NULL, 0 };
    VkFence fence; v_vkCreateFence(dev, &fci, NULL, &fence);

    int fd = heap_alloc();
    AHardwareBuffer *ahb = ahb_new(W, H);
    if (fd < 0 || !ahb) return 1;
    VkBuffer buf; VkDeviceMemory bmem; VkImage img; VkDeviceMemory imem;
    if (import_dmabuf(fd, (VkDeviceSize) PITCH * H, &buf, &bmem, "small") || import_ahb(ahb, W, H, &img, &imem, "small")) {
        printf("VERDICT_INPUT CPY=FAIL\n");
        return 0;
    }

    /* C1: AHB cleared, command buffer without the copy -> must NOT match */
    fill(fd, 0, 1);
    ahb_clear(ahb);
    record(cb, buf, img, W, H, PITCH / 4, 0, VK_NULL_HANDLE);
    VkResult r = submit_wait(cb, fence);
    printf("C1_NO_COPY submit=%d cpu_mismatch=%ld of=%d (expected > 0)\n", r, ahb_cpu_compare(ahb, 0, NULL), W * H);

    /* CPY + PIX_CPU + PIX_GL, then LIVE (v=1 with sync, v=2 without sync) */
    EGLint iattr[] = { EGL_IMAGE_PRESERVED_KHR, EGL_TRUE, EGL_NONE };
    EGLImageKHR eimg = p_eglCreateImageKHR(dpy, EGL_NO_CONTEXT, EGL_NATIVE_BUFFER_ANDROID, gncb(ahb), iattr);
    GLuint tex; p_glGenTextures(1, &tex);
    p_glBindTexture(GL_TEXTURE_2D, tex);
    p_glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
    p_glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
    while (p_glGetError()) {}
    if (eimg) p_glEGLImageTargetTexture2DOES(GL_TEXTURE_2D, eimg);
    printf("GL_AHB_EGLIMAGE=%s egl_err=0x%x gl_err=0x%x\n", eimg ? "OK" : "FAIL", p_eglGetError(), p_glGetError());
    for (int v = 0; v < 3; v++) {
        fill(fd, v, v != 2);
        record(cb, buf, img, W, H, PITCH / 4, 1, VK_NULL_HANDLE);
        r = submit_wait(cb, fence);
        long xo = 0, bad = ahb_cpu_compare(ahb, v, &xo);
        long gl_bad = -1, gl_badf = -1;
        if (eimg) {
            draw_read(GL_TEXTURE_2D, tex);
            gl_bad = compare(DRM_FORMAT_XBGR8888, v, 0);
            gl_badf = compare(DRM_FORMAT_XBGR8888, v, 1);
        }
        printf("CPY v=%d%s submit=%d PIX_CPU mismatch=%ld (x_byte_only=%ld) PIX_GL mismatch=%ld mismatch_flipped=%ld of=%d "
               "C2_wrong_pattern_cpu_mismatch=%ld\n", v, v == 2 ? "(nosync)" : "", r, bad, xo, gl_bad, gl_badf, W * H,
               ahb_cpu_compare(ahb, (v + 1) % 3, NULL));
    }

    /* C3: memfd must not import as a dma-buf */
    int mfd = (int) syscall(__NR_memfd_create, "feas02-c3", 0);
    if (mfd >= 0 && ftruncate(mfd, (off_t) buf_size()) == 0) {
        VkBuffer b3; VkDeviceMemory m3;
        VkResult r3 = import_dmabuf(mfd, (VkDeviceSize) PITCH * H, &b3, &m3, "c3_memfd");
        printf("C3_MEMFD_IMPORT result=%d (expected nonzero)\n", r3);
    }

    timing(cb, fence);
    printf("DONE\n");
    return 0;
}
