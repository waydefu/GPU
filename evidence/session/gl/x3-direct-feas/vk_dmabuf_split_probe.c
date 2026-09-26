// X3-DIRECT-FEAS-03 probe (see X3-DIRECT-FEAS-03-FREEZE.md): GPU copy of a client dma-buf into an
// X3-style AHB via the system Vulkan driver, working around the driver's +5300-byte requirement on
// external-memory resources.
//   S: dma-buf with slack  -> whole VkBuffer, GPU copies every row (spec-clean)
//   T: exact-size dma-buf  -> VkBuffer covers the first R rows, CPU copies the tail rows (spec-clean)
//   O: exact-size dma-buf  -> whole VkBuffer bound although req > allocation (spec-violating, info)
#include "feas02_body.inc"

static PFN_vkDestroyBuffer v_destroy_buffer;
static PFN_vkFreeMemory v_free_memory;

static int mem_type_for(int fd, uint32_t *type) {
    VkMemoryFdPropertiesKHR mp = { VK_STRUCTURE_TYPE_MEMORY_FD_PROPERTIES_KHR };
    if (v_vkGetMemoryFdPropertiesKHR(dev, VK_EXTERNAL_MEMORY_HANDLE_TYPE_DMA_BUF_BIT_EXT, fd, &mp)) return -1;
    VkExternalMemoryBufferCreateInfo ext = { VK_STRUCTURE_TYPE_EXTERNAL_MEMORY_BUFFER_CREATE_INFO, NULL,
                                             VK_EXTERNAL_MEMORY_HANDLE_TYPE_DMA_BUF_BIT_EXT };
    VkBufferCreateInfo bci = { VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO, &ext, 0, 4096, VK_BUFFER_USAGE_TRANSFER_SRC_BIT,
                               VK_SHARING_MODE_EXCLUSIVE, 0, NULL };
    VkBuffer b; VkMemoryRequirements q;
    if (v_vkCreateBuffer(dev, &bci, NULL, &b)) return -1;
    v_vkGetBufferMemoryRequirements(dev, b, &q);
    v_destroy_buffer(dev, b, NULL);
    uint32_t bits = q.memoryTypeBits & mp.memoryTypeBits, t = 0;
    while (t < 32 && !(bits & (1u << t))) t++;
    if (t == 32) return -1;
    *type = t;
    return 0;
}

static VkResult import_mem(int fd, VkDeviceSize alloc, VkDeviceMemory *mem) {
    uint32_t t;
    if (mem_type_for(fd, &t)) return VK_ERROR_INVALID_EXTERNAL_HANDLE;
    int d = dup(fd);
    VkImportMemoryFdInfoKHR imp = { VK_STRUCTURE_TYPE_IMPORT_MEMORY_FD_INFO_KHR, NULL,
                                    VK_EXTERNAL_MEMORY_HANDLE_TYPE_DMA_BUF_BIT_EXT, d };
    VkMemoryAllocateInfo mai = { VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO, &imp, alloc, t };
    VkResult r = v_vkAllocateMemory(dev, &mai, NULL, mem);
    if (r) close(d);
    return r;
}

/* ext buffer of `size` bytes; reports its requirement */
static VkResult make_buffer(VkDeviceSize size, VkBuffer *b, VkDeviceSize *req) {
    VkExternalMemoryBufferCreateInfo ext = { VK_STRUCTURE_TYPE_EXTERNAL_MEMORY_BUFFER_CREATE_INFO, NULL,
                                             VK_EXTERNAL_MEMORY_HANDLE_TYPE_DMA_BUF_BIT_EXT };
    VkBufferCreateInfo bci = { VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO, &ext, 0, size, VK_BUFFER_USAGE_TRANSFER_SRC_BIT,
                               VK_SHARING_MODE_EXCLUSIVE, 0, NULL };
    VkResult r = v_vkCreateBuffer(dev, &bci, NULL, b);
    if (r) return r;
    VkMemoryRequirements q; v_vkGetBufferMemoryRequirements(dev, *b, &q);
    *req = q.size;
    return VK_SUCCESS;
}

static VkDeviceSize rows_bytes(int rows) { return (VkDeviceSize) (rows - 1) * PITCH + (VkDeviceSize) W * 4; }

/* largest R such that the requirement of a buffer covering rows [0,R) fits in dsize */
static int rows_fitting(int height, VkDeviceSize dsize, VkDeviceSize *overhead) {
    VkBuffer b; VkDeviceSize req;
    make_buffer(rows_bytes(height), &b, &req);
    v_destroy_buffer(dev, b, NULL);
    *overhead = req - rows_bytes(height);
    int r = height;
    while (r > 0 && rows_bytes(r) + *overhead > dsize) r--;
    return r;
}

static void tail_copy(int fd, size_t map_len, AHardwareBuffer *ahb, int r0, int r1, int sync) {
    if (r0 >= r1) return;
    uint8_t *m = mmap(NULL, map_len, PROT_READ, MAP_SHARED, fd, 0);
    struct dma_buf_sync s = { DMA_BUF_SYNC_START | DMA_BUF_SYNC_READ };
    if (sync) ioctl(fd, DMA_BUF_IOCTL_SYNC, &s);
    AHardwareBuffer_Desc d; ahb_describe(ahb, &d);
    void *p;
    if (!ahb_lock(ahb, AHARDWAREBUFFER_USAGE_CPU_WRITE_OFTEN | AHARDWAREBUFFER_USAGE_CPU_READ_OFTEN, -1, NULL, &p)) {
        for (int y = r0; y < r1; y++)
            memcpy((uint8_t *) p + (size_t) y * d.stride * 4, m + (size_t) y * PITCH, (size_t) W * 4);
        ahb_unlock(ahb, NULL);
    }
    s.flags = DMA_BUF_SYNC_END | DMA_BUF_SYNC_READ;
    if (sync) ioctl(fd, DMA_BUF_IOCTL_SYNC, &s);
    munmap(m, map_len);
}

enum { MODE_S, MODE_T, MODE_O };

static void split_case(const char *tag, int mode, AHardwareBuffer *ahb, VkImage img, GLuint tex, int have_gl,
                     VkCommandBuffer cb, VkFence f) {
    size_t exact = buf_size(); /* PITCH*H page aligned = 622592 */
    size_t dsize = mode == MODE_S ? exact + 8192 : exact;
    int fd = heap_alloc_size(dsize);
    if (fd < 0) { printf("CASE[%s] HEAP=FAIL\n", tag); return; }
    VkDeviceMemory mem;
    VkResult r = import_mem(fd, dsize, &mem);
    VkDeviceSize overhead = 0;
    int R = mode == MODE_T ? rows_fitting(H, dsize, &overhead) : H;
    if (mode != MODE_T) { int dummy = rows_fitting(H, dsize, &overhead); (void) dummy; }
    VkBuffer buf; VkDeviceSize req = 0;
    VkResult rb = r ? r : make_buffer(rows_bytes(R), &buf, &req);
    VkResult rbind = rb ? rb : v_vkBindBufferMemory(dev, buf, mem, 0);
    printf("CASE[%s] dmabuf=%zu import=%d overhead=%llu rows_gpu=%d tail_rows=%d buffer=%llu req=%llu req_fits=%d bind=%d\n",
           tag, dsize, r, (unsigned long long) overhead, R, H - R, (unsigned long long) rows_bytes(R),
           (unsigned long long) req, req <= dsize, rbind);
    if (rbind) { printf("CASE[%s] CPY=FAIL\n", tag); return; }
    for (int v = 0; v < 3; v++) {
        fill(fd, v, v != 2);
        ahb_clear(ahb);
        record(cb, buf, img, W, (uint32_t) R, PITCH / 4, 1, VK_NULL_HANDLE);
        VkResult rs = submit_wait(cb, f);
        tail_copy(fd, exact, ahb, R, H, v != 2);
        long xo = 0, bad = ahb_cpu_compare(ahb, v, &xo), gl_bad = -1, gl_badf = -1;
        if (have_gl) {
            draw_read(GL_TEXTURE_2D, tex);
            gl_bad = compare(DRM_FORMAT_XBGR8888, v, 0);
            gl_badf = compare(DRM_FORMAT_XBGR8888, v, 1);
        }
        printf("CASE[%s] v=%d%s submit=%d PIX_CPU mismatch=%ld (x_byte_only=%ld) PIX_GL mismatch=%ld mismatch_flipped=%ld of=%d C2_wrong_pattern_cpu_mismatch=%ld\n",
               tag, v, v == 2 ? "(nosync)" : "", rs, bad, xo, gl_bad, gl_badf, W * H, ahb_cpu_compare(ahb, (v + 1) % 3, NULL));
    }
    if (mode == MODE_S) {
        /* C1: cleared AHB + command buffer without the copy must not match */
        fill(fd, 0, 1);
        ahb_clear(ahb);
        record(cb, buf, img, W, (uint32_t) R, PITCH / 4, 0, VK_NULL_HANDLE);
        VkResult rs = submit_wait(cb, f);
        printf("C1_NO_COPY submit=%d cpu_mismatch=%ld of=%d (expected > 0)\n", rs, ahb_cpu_compare(ahb, 0, NULL), W * H);
    }
    v_destroy_buffer(dev, buf, NULL);
    v_free_memory(dev, mem, NULL);
    close(fd);
}

static void split_timing(VkCommandBuffer cb, VkFence f) {
    size_t dsize = ((size_t) PITCH * BIG_H + 4095) & ~(size_t) 4095; /* 11984896, exact */
    int fd = heap_alloc_size(dsize);
    AHardwareBuffer *ahb = ahb_new(W, BIG_H);
    if (fd < 0 || !ahb) { printf("TIMING=NOT_RUN\n"); return; }
    uint8_t *src = mmap(NULL, dsize, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    for (size_t i = 0; i < dsize; i++) src[i] = (uint8_t) (i * 2654435761u >> 13);
    AHardwareBuffer_Desc d; ahb_describe(ahb, &d);
    enum { N = 21 };
    double wall[N], cpu[N], gpu[N];
    for (int mode = 0; mode < 2; mode++) {
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
    VkDeviceMemory mem; VkBuffer buf; VkDeviceSize req, overhead; VkImage img; VkDeviceMemory imem;
    int R = rows_fitting(BIG_H, dsize, &overhead);
    if (import_mem(fd, dsize, &mem) || make_buffer(rows_bytes(R), &buf, &req) || v_vkBindBufferMemory(dev, buf, mem, 0) ||
        import_ahb(ahb, W, BIG_H, &img, &imem, "big")) { printf("TIMING_VK=NOT_RUN\n"); return; }
    VkQueryPoolCreateInfo qpi = { VK_STRUCTURE_TYPE_QUERY_POOL_CREATE_INFO, NULL, 0, VK_QUERY_TYPE_TIMESTAMP, 2, 0 };
    VkQueryPool qp; v_vkCreateQueryPool(dev, &qpi, NULL, &qp);
    for (int i = 0; i < N; i++) {
        double w0 = now_ms(CLOCK_MONOTONIC), c0 = now_ms(CLOCK_THREAD_CPUTIME_ID);
        record(cb, buf, img, W, (uint32_t) R, PITCH / 4, 1, qp);
        VkResult r = submit_wait(cb, f);
        tail_copy(fd, dsize, ahb, R, BIG_H, 1);
        wall[i] = now_ms(CLOCK_MONOTONIC) - w0; cpu[i] = now_ms(CLOCK_THREAD_CPUTIME_ID) - c0;
        uint64_t ts[2] = { 0, 0 };
        v_vkGetQueryPoolResults(dev, qp, 0, 2, sizeof ts, ts, sizeof(uint64_t), VK_QUERY_RESULT_64_BIT | VK_QUERY_RESULT_WAIT_BIT);
        gpu[i] = (double) (ts[1] - ts[0]) * ts_period / 1e6;
        if (r) { printf("TIMING_VK submit=%d\n", r); return; }
    }
    qsort(wall + 1, N - 1, sizeof(double), cmp_d); qsort(cpu + 1, N - 1, sizeof(double), cmp_d);
    qsort(gpu + 1, N - 1, sizeof(double), cmp_d);
    printf("TIMING_VK_SPLIT %ux%d rows_gpu=%d tail_rows=%d wall_median_ms=%.3f cpu_median_ms=%.3f gpu_median_ms=%.3f "
           "(n=%d, first dropped; includes command re-record + tail lock/copy)\n",
           W, BIG_H, R, BIG_H - R, wall[N / 2], cpu[N / 2], gpu[N / 2], N - 1);
    void *p; long bad = 0;
    if (!ahb_lock(ahb, AHARDWAREBUFFER_USAGE_CPU_READ_OFTEN, -1, NULL, &p)) {
        for (int y = 0; y < BIG_H; y++)
            for (int x = 0; x < W; x++)
                if (memcmp((uint8_t *) p + ((size_t) y * d.stride + x) * 4, src + (size_t) y * PITCH + x * 4, 4)) bad++;
        ahb_unlock(ahb, NULL);
    }
    printf("TIMING_VK_SPLIT_CHECK mismatch=%ld of=%d\n", bad, W * BIG_H);
}

int main(void) {
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
    p_glEGLImageTargetTexture2DOES = (PFNGLEGLIMAGETARGETTEXTURE2DOESPROC) p_eglGetProcAddress("glEGLImageTargetTexture2DOES");
    PFN_eglGetNativeClientBufferANDROID_ gncb =
        (PFN_eglGetNativeClientBufferANDROID_) p_eglGetProcAddress("eglGetNativeClientBufferANDROID");
    if (!p_eglCreateImageKHR || !p_glEGLImageTargetTexture2DOES || !gncb || gl_setup()) { printf("GL=FAIL\n"); return 1; }
    if (vk_init()) return 1;
    v_destroy_buffer = (PFN_vkDestroyBuffer) g_gdpa(dev, "vkDestroyBuffer");
    v_free_memory = (PFN_vkFreeMemory) g_gdpa(dev, "vkFreeMemory");
    VkCommandPoolCreateInfo cpi = { VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO, NULL,
                                    VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT, qf };
    VkCommandPool pool; v_vkCreateCommandPool(dev, &cpi, NULL, &pool);
    VkCommandBufferAllocateInfo cai = { VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO, NULL, pool,
                                        VK_COMMAND_BUFFER_LEVEL_PRIMARY, 1 };
    VkCommandBuffer cb; v_vkAllocateCommandBuffers(dev, &cai, &cb);
    VkFenceCreateInfo fci = { VK_STRUCTURE_TYPE_FENCE_CREATE_INFO, NULL, 0 };
    VkFence fence; v_vkCreateFence(dev, &fci, NULL, &fence);

    AHardwareBuffer *ahb = ahb_new(W, H);
    VkImage img; VkDeviceMemory imem;
    if (!ahb || import_ahb(ahb, W, H, &img, &imem, "small")) { printf("AHB_IMPORT=FAIL\n"); return 1; }
    EGLint iattr[] = { EGL_IMAGE_PRESERVED_KHR, EGL_TRUE, EGL_NONE };
    EGLImageKHR eimg = p_eglCreateImageKHR(dpy, EGL_NO_CONTEXT, EGL_NATIVE_BUFFER_ANDROID, gncb(ahb), iattr);
    GLuint tex; p_glGenTextures(1, &tex);
    p_glBindTexture(GL_TEXTURE_2D, tex);
    p_glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
    p_glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
    while (p_glGetError()) {}
    if (eimg) p_glEGLImageTargetTexture2DOES(GL_TEXTURE_2D, eimg);
    GLenum ge = p_glGetError();
    printf("GL_AHB_EGLIMAGE=%s gl_err=0x%x\n", eimg ? "OK" : "FAIL", ge);
    int have_gl = eimg && !ge;

    split_case("S", MODE_S, ahb, img, tex, have_gl, cb, fence);
    split_case("T", MODE_T, ahb, img, tex, have_gl, cb, fence);
    split_case("O", MODE_O, ahb, img, tex, have_gl, cb, fence);

    int mfd = (int) syscall(__NR_memfd_create, "feas03-c3", 0);
    if (mfd >= 0 && ftruncate(mfd, (off_t) buf_size()) == 0) {
        VkDeviceMemory m3;
        VkResult r3 = import_mem(mfd, buf_size(), &m3);
        printf("C3_MEMFD_IMPORT result=%d (expected nonzero)\n", r3);
    }
    split_timing(cb, fence);
    printf("DONE\n");
    return 0;
}
