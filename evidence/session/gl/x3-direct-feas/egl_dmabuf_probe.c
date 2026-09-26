// X3-DIRECT-FEAS-01 probe: can Android's system EGL (the one lorie's renderer uses) sample a
// client dma-buf with zero copy?
//
// The dma-buf comes from /dev/dma_heap/system, the same heap Turnip's KGSL backend allocates
// every shareable (DRI3-exported) BO from (tu_knl_kgsl.cc bo_init_new_dmaheap), laid out the way
// X3 receives it: LINEAR, 32bpp, pitch aligned like Turnip (1200 px -> 4864 bytes).
//
// Checks, in order:
//   EXT   display extension string (EGL_EXT_image_dma_buf_import etc.)
//   IMP   eglCreateImageKHR(EGL_LINUX_DMA_BUF_EXT) per fourcc, even if not advertised
//   PIX   sampled pixels == what the CPU wrote (exact, every pixel)
//   LIVE  CPU rewrites the buffer after import; resampling shows the new bytes
//         (zero-copy) or the old ones (import-time copy)
//   C1    red control: a memfd of the same size must NOT import
//   C2    red control: comparator must report mismatches against the wrong pattern
//   VK    system Vulkan driver's external-memory extensions (info only)
//   AHB   AHardwareBuffer_createFromHandle resolvable in libnativewindow (info only)
//
// Output is line-oriented KEY=VALUE for the result doc. No X, no app, no Stable.
#define _GNU_SOURCE
#include <dlfcn.h>
#include <errno.h>
#include <fcntl.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <sys/syscall.h>
#include <unistd.h>
#include <linux/dma-buf.h>
#include <linux/dma-heap.h>
#include <drm/drm_fourcc.h>
#include <EGL/egl.h>
#include <EGL/eglext.h>
#include <GLES2/gl2.h>
#include <GLES2/gl2ext.h>
#include <vulkan/vulkan_core.h>

#define W 1200
#define H 128
#define PITCH 4864

static void *egl_lib, *gles_lib;
#define EGLF(name) static __typeof__(&name) p_##name;
#define GLF(name) static __typeof__(&name) p_##name;
EGLF(eglGetDisplay) EGLF(eglInitialize) EGLF(eglQueryString) EGLF(eglChooseConfig)
EGLF(eglCreateContext) EGLF(eglCreatePbufferSurface) EGLF(eglMakeCurrent) EGLF(eglGetError)
EGLF(eglGetProcAddress) EGLF(eglBindAPI)
GLF(glGetString) GLF(glGetError) GLF(glGenTextures) GLF(glBindTexture) GLF(glTexParameteri)
GLF(glTexImage2D) GLF(glGenFramebuffers) GLF(glBindFramebuffer) GLF(glFramebufferTexture2D)
GLF(glCheckFramebufferStatus) GLF(glViewport) GLF(glCreateShader) GLF(glShaderSource)
GLF(glCompileShader) GLF(glGetShaderiv) GLF(glGetShaderInfoLog) GLF(glCreateProgram)
GLF(glAttachShader) GLF(glLinkProgram) GLF(glGetProgramiv) GLF(glUseProgram)
GLF(glBindAttribLocation) GLF(glVertexAttribPointer) GLF(glEnableVertexAttribArray)
GLF(glDrawArrays) GLF(glReadPixels) GLF(glFinish) GLF(glUniform1i) GLF(glGetUniformLocation)
GLF(glActiveTexture) GLF(glDeleteTextures) GLF(glPixelStorei)
static PFNEGLCREATEIMAGEKHRPROC p_eglCreateImageKHR;
static PFNEGLDESTROYIMAGEKHRPROC p_eglDestroyImageKHR;
static PFNGLEGLIMAGETARGETTEXTURE2DOESPROC p_glEGLImageTargetTexture2DOES;
static EGLDisplay dpy;

static int load(void) {
    egl_lib = dlopen("/system/lib64/libEGL.so", RTLD_NOW | RTLD_LOCAL);
    gles_lib = dlopen("/system/lib64/libGLESv2.so", RTLD_NOW | RTLD_LOCAL);
    if (!egl_lib || !gles_lib) { printf("LOAD=FAIL %s\n", dlerror()); return -1; }
#define LE(name) if (!(p_##name = dlsym(egl_lib, #name))) { printf("LOAD=FAIL %s\n", #name); return -1; }
#define LG(name) if (!(p_##name = dlsym(gles_lib, #name))) { printf("LOAD=FAIL %s\n", #name); return -1; }
    LE(eglGetDisplay) LE(eglInitialize) LE(eglQueryString) LE(eglChooseConfig) LE(eglCreateContext)
    LE(eglCreatePbufferSurface) LE(eglMakeCurrent) LE(eglGetError) LE(eglGetProcAddress) LE(eglBindAPI)
    LG(glGetString) LG(glGetError) LG(glGenTextures) LG(glBindTexture) LG(glTexParameteri)
    LG(glTexImage2D) LG(glGenFramebuffers) LG(glBindFramebuffer) LG(glFramebufferTexture2D)
    LG(glCheckFramebufferStatus) LG(glViewport) LG(glCreateShader) LG(glShaderSource)
    LG(glCompileShader) LG(glGetShaderiv) LG(glGetShaderInfoLog) LG(glCreateProgram)
    LG(glAttachShader) LG(glLinkProgram) LG(glGetProgramiv) LG(glUseProgram)
    LG(glBindAttribLocation) LG(glVertexAttribPointer) LG(glEnableVertexAttribArray)
    LG(glDrawArrays) LG(glReadPixels) LG(glFinish) LG(glUniform1i) LG(glGetUniformLocation)
    LG(glActiveTexture) LG(glDeleteTextures) LG(glPixelStorei)
    printf("LOAD=OK\n");
    return 0;
}

static int has_token(const char *list, const char *tok) {
    size_t n = strlen(tok);
    for (const char *p = list; p && (p = strstr(p, tok)); p += n)
        if ((p == list || p[-1] == ' ') && (p[n] == ' ' || p[n] == '\0'))
            return 1;
    return 0;
}

/* ---- dma-buf ---- */
static size_t buf_size(void) { return ((size_t) PITCH * H + 4095) & ~(size_t) 4095; }

static int heap_alloc(void) {
    int heap = open("/dev/dma_heap/system", O_RDONLY | O_CLOEXEC);
    if (heap < 0) { printf("HEAP=FAIL open errno=%d\n", errno); return -1; }
    struct dma_heap_allocation_data a = { .len = buf_size(), .fd_flags = O_RDWR | O_CLOEXEC };
    int r = ioctl(heap, DMA_HEAP_IOCTL_ALLOC, &a);
    close(heap);
    if (r < 0) { printf("HEAP=FAIL alloc errno=%d\n", errno); return -1; }
    char path[64], target[256] = "";
    snprintf(path, sizeof path, "/proc/self/fd/%d", (int) a.fd);
    ssize_t n = readlink(path, target, sizeof target - 1);
    if (n > 0) target[n] = 0;
    printf("HEAP=OK fd_target=%s size=%zu\n", target, buf_size());
    return (int) a.fd;
}

/* pattern bytes for memory position (x,y), variant v; 4 bytes b0..b3 in memory order */
static void pat(int x, int y, int v, uint8_t b[4]) {
    b[0] = (uint8_t) (x * 7 + v * 91);
    b[1] = (uint8_t) (y * 13 + v * 37);
    b[2] = (uint8_t) ((x ^ y) + v * 53);
    b[3] = (uint8_t) (x + y * 3 + v * 17 + 1);
}

static int fill(int fd, int v, int use_sync) {
    uint8_t *m = mmap(NULL, buf_size(), PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    if (m == MAP_FAILED) { printf("MMAP=FAIL errno=%d\n", errno); return -1; }
    struct dma_buf_sync s = { DMA_BUF_SYNC_START | DMA_BUF_SYNC_WRITE };
    if (use_sync && ioctl(fd, DMA_BUF_IOCTL_SYNC, &s) < 0) printf("SYNC_START=FAIL errno=%d\n", errno);
    for (int y = 0; y < H; y++)
        for (int x = 0; x < W; x++)
            pat(x, y, v, m + (size_t) y * PITCH + (size_t) x * 4);
    s.flags = DMA_BUF_SYNC_END | DMA_BUF_SYNC_WRITE;
    if (use_sync && ioctl(fd, DMA_BUF_IOCTL_SYNC, &s) < 0) printf("SYNC_END=FAIL errno=%d\n", errno);
    munmap(m, buf_size());
    return 0;
}

/* ---- GL ---- */
static GLuint prog_ext, prog_2d, fbo, fbo_tex;
static const GLfloat quad[] = { -1, -1, 0, 0,  1, -1, 1, 0,  -1, 1, 0, 1,  1, 1, 1, 1 };

static GLuint build(const char *fs_src) {
    static const char *vs_src =
        "attribute vec2 p; attribute vec2 t; varying vec2 v;\n"
        "void main() { v = t; gl_Position = vec4(p, 0.0, 1.0); }\n";
    GLuint vs = p_glCreateShader(GL_VERTEX_SHADER), fs = p_glCreateShader(GL_FRAGMENT_SHADER);
    p_glShaderSource(vs, 1, &vs_src, NULL); p_glCompileShader(vs);
    p_glShaderSource(fs, 1, &fs_src, NULL); p_glCompileShader(fs);
    GLint ok = 0; char log[512] = "";
    p_glGetShaderiv(fs, GL_COMPILE_STATUS, &ok);
    if (!ok) { p_glGetShaderInfoLog(fs, sizeof log, NULL, log); printf("SHADER=FAIL %s\n", log); return 0; }
    GLuint pr = p_glCreateProgram();
    p_glAttachShader(pr, vs); p_glAttachShader(pr, fs);
    p_glBindAttribLocation(pr, 0, "p"); p_glBindAttribLocation(pr, 1, "t");
    p_glLinkProgram(pr);
    p_glGetProgramiv(pr, GL_LINK_STATUS, &ok);
    return ok ? pr : 0;
}

static int gl_setup(void) {
    prog_ext = build("#extension GL_OES_EGL_image_external : require\n"
                     "precision mediump float; varying vec2 v; uniform samplerExternalOES s;\n"
                     "void main() { gl_FragColor = texture2D(s, v); }\n");
    prog_2d = build("precision mediump float; varying vec2 v; uniform sampler2D s;\n"
                    "void main() { gl_FragColor = texture2D(s, v); }\n");
    p_glGenTextures(1, &fbo_tex);
    p_glBindTexture(GL_TEXTURE_2D, fbo_tex);
    p_glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, W, H, 0, GL_RGBA, GL_UNSIGNED_BYTE, NULL);
    p_glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
    p_glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
    p_glGenFramebuffers(1, &fbo);
    p_glBindFramebuffer(GL_FRAMEBUFFER, fbo);
    p_glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, fbo_tex, 0);
    GLenum st = p_glCheckFramebufferStatus(GL_FRAMEBUFFER);
    printf("GL_SETUP prog_ext=%s prog_2d=%s fbo=0x%x\n", prog_ext ? "ok" : "fail",
           prog_2d ? "ok" : "fail", st);
    return st == GL_FRAMEBUFFER_COMPLETE ? 0 : -1;
}

static uint8_t readback[W * H * 4];

static int draw_read(GLenum target, GLuint tex) {
    GLuint pr = target == GL_TEXTURE_EXTERNAL_OES ? prog_ext : prog_2d;
    if (!pr) return -1;
    p_glBindFramebuffer(GL_FRAMEBUFFER, fbo);
    p_glViewport(0, 0, W, H);
    p_glUseProgram(pr);
    p_glActiveTexture(GL_TEXTURE0);
    p_glBindTexture(target, tex);
    p_glUniform1i(p_glGetUniformLocation(pr, "s"), 0);
    p_glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 16, quad);
    p_glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 16, quad + 2);
    p_glEnableVertexAttribArray(0); p_glEnableVertexAttribArray(1);
    p_glDrawArrays(GL_TRIANGLE_STRIP, 0, 4);
    p_glPixelStorei(GL_PACK_ALIGNMENT, 1);
    p_glReadPixels(0, 0, W, H, GL_RGBA, GL_UNSIGNED_BYTE, readback);
    p_glFinish();
    return (int) p_glGetError();
}

/* expected sampled RGBA for memory bytes under a fourcc; returns mismatch count.
 * flip: compare readback row y against memory row H-1-y. */
static long compare(uint32_t fourcc, int v, int flip) {
    long bad = 0;
    for (int y = 0; y < H; y++)
        for (int x = 0; x < W; x++) {
            uint8_t m[4], e[4];
            pat(x, flip ? H - 1 - y : y, v, m);
            switch (fourcc) {
            case DRM_FORMAT_ABGR8888: e[0] = m[0]; e[1] = m[1]; e[2] = m[2]; e[3] = m[3]; break;
            case DRM_FORMAT_XBGR8888: e[0] = m[0]; e[1] = m[1]; e[2] = m[2]; e[3] = 255; break;
            case DRM_FORMAT_ARGB8888: e[0] = m[2]; e[1] = m[1]; e[2] = m[0]; e[3] = m[3]; break;
            case DRM_FORMAT_XRGB8888: e[0] = m[2]; e[1] = m[1]; e[2] = m[0]; e[3] = 255; break;
            default: return -1;
            }
            const uint8_t *r = readback + ((size_t) y * W + x) * 4;
            if (r[0] != e[0] || r[1] != e[1] || r[2] != e[2] || r[3] != e[3]) bad++;
        }
    return bad;
}

static EGLImageKHR import(int fd, uint32_t fourcc, EGLint *err) {
    EGLint attrs[] = {
        EGL_WIDTH, W, EGL_HEIGHT, H, EGL_LINUX_DRM_FOURCC_EXT, (EGLint) fourcc,
        EGL_DMA_BUF_PLANE0_FD_EXT, fd, EGL_DMA_BUF_PLANE0_OFFSET_EXT, 0,
        EGL_DMA_BUF_PLANE0_PITCH_EXT, PITCH, EGL_NONE };
    EGLImageKHR img = p_eglCreateImageKHR(dpy, EGL_NO_CONTEXT, EGL_LINUX_DMA_BUF_EXT, NULL, attrs);
    *err = p_eglGetError();
    return img;
}

static const char *fcc_name(uint32_t f) {
    switch (f) {
    case DRM_FORMAT_ARGB8888: return "AR24"; case DRM_FORMAT_XRGB8888: return "XR24";
    case DRM_FORMAT_ABGR8888: return "AB24"; case DRM_FORMAT_XBGR8888: return "XB24";
    }
    return "?";
}

/* one fourcc x one texture target: IMP, PIX, LIVE */
static void run_case(int fd, uint32_t fourcc, GLenum target) {
    const char *tn = target == GL_TEXTURE_EXTERNAL_OES ? "EXT" : "2D";
    fill(fd, 0, 1);
    EGLint err;
    EGLImageKHR img = import(fd, fourcc, &err);
    printf("IMP[%s/%s]=%s egl_err=0x%x\n", fcc_name(fourcc), tn, img ? "OK" : "FAIL", err);
    if (!img) return;
    GLuint tex;
    p_glGenTextures(1, &tex);
    p_glBindTexture(target, tex);
    p_glTexParameteri(target, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
    p_glTexParameteri(target, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
    while (p_glGetError()) {}
    p_glEGLImageTargetTexture2DOES(target, img);
    GLenum gerr = p_glGetError();
    printf("BIND[%s/%s]=%s gl_err=0x%x\n", fcc_name(fourcc), tn, gerr ? "FAIL" : "OK", gerr);
    if (gerr) { p_glDeleteTextures(1, &tex); p_eglDestroyImageKHR(dpy, img); return; }

    int de = draw_read(target, tex);
    long bad = compare(fourcc, 0, 0), badf = compare(fourcc, 0, 1);
    long c2 = compare(fourcc, 1, 0); /* C2: wrong pattern must mismatch */
    printf("PIX[%s/%s] draw_err=0x%x mismatch=%ld mismatch_flipped=%ld of=%d c2_wrong_pattern_mismatch=%ld\n",
           fcc_name(fourcc), tn, de, bad, badf, W * H, c2);
    uint8_t *r = readback;
    uint8_t m0[4]; pat(0, 0, 0, m0);
    printf("PIX_SAMPLE[%s/%s] mem00=%02x%02x%02x%02x read00=%02x%02x%02x%02x\n", fcc_name(fourcc), tn,
           m0[0], m0[1], m0[2], m0[3], r[0], r[1], r[2], r[3]);
    int flip = badf < bad;

    /* LIVE: rewrite after import, resample without rebinding, then after rebinding */
    fill(fd, 1, 1);
    draw_read(target, tex);
    long l_nb_new = compare(fourcc, 1, flip), l_nb_old = compare(fourcc, 0, flip);
    p_glBindTexture(target, tex);
    p_glEGLImageTargetTexture2DOES(target, img);
    draw_read(target, tex);
    long l_rb_new = compare(fourcc, 1, flip), l_rb_old = compare(fourcc, 0, flip);
    printf("LIVE[%s/%s] no_rebind: mismatch_vs_new=%ld mismatch_vs_old=%ld | rebind: mismatch_vs_new=%ld mismatch_vs_old=%ld\n",
           fcc_name(fourcc), tn, l_nb_new, l_nb_old, l_rb_new, l_rb_old);

    /* LIVE without DMA_BUF_IOCTL_SYNC (what X3 does today when reading client buffers) */
    fill(fd, 2, 0);
    draw_read(target, tex);
    printf("LIVE_NOSYNC[%s/%s] mismatch_vs_new=%ld\n", fcc_name(fourcc), tn, compare(fourcc, 2, flip));
    p_glDeleteTextures(1, &tex);
    p_eglDestroyImageKHR(dpy, img);
}

static void vk_probe(void) {
    void *vk = dlopen("/system/lib64/libvulkan.so", RTLD_NOW | RTLD_LOCAL);
    if (!vk) { printf("VK=LOAD_FAIL\n"); return; }
    PFN_vkGetInstanceProcAddr gipa = dlsym(vk, "vkGetInstanceProcAddr");
    PFN_vkCreateInstance ci = (PFN_vkCreateInstance) gipa(NULL, "vkCreateInstance");
    VkApplicationInfo ai = { VK_STRUCTURE_TYPE_APPLICATION_INFO, NULL, "probe", 1, NULL, 0, VK_API_VERSION_1_1 };
    VkInstanceCreateInfo ici = { VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO, NULL, 0, &ai, 0, NULL, 0, NULL };
    VkInstance inst;
    VkResult r = ci(&ici, NULL, &inst);
    if (r != VK_SUCCESS) { printf("VK=INSTANCE_FAIL %d\n", r); return; }
    PFN_vkEnumeratePhysicalDevices epd = (PFN_vkEnumeratePhysicalDevices) gipa(inst, "vkEnumeratePhysicalDevices");
    PFN_vkGetPhysicalDeviceProperties gpp = (PFN_vkGetPhysicalDeviceProperties) gipa(inst, "vkGetPhysicalDeviceProperties");
    PFN_vkEnumerateDeviceExtensionProperties ede =
        (PFN_vkEnumerateDeviceExtensionProperties) gipa(inst, "vkEnumerateDeviceExtensionProperties");
    uint32_t n = 1; VkPhysicalDevice pd;
    epd(inst, &n, &pd);
    if (!n) { printf("VK=NO_DEVICE\n"); return; }
    VkPhysicalDeviceProperties pp; gpp(pd, &pp);
    uint32_t ne = 0; ede(pd, NULL, &ne, NULL);
    VkExtensionProperties *ex = calloc(ne, sizeof *ex); ede(pd, NULL, &ne, ex);
    const char *want[] = { "VK_EXT_external_memory_dma_buf", "VK_EXT_image_drm_format_modifier",
                           "VK_KHR_external_memory_fd", "VK_ANDROID_external_memory_android_hardware_buffer" };
    printf("VK_DEVICE=%s api=%u.%u.%u driver=0x%x ext_count=%u\n", pp.deviceName, VK_VERSION_MAJOR(pp.apiVersion),
           VK_VERSION_MINOR(pp.apiVersion), VK_VERSION_PATCH(pp.apiVersion), pp.driverVersion, ne);
    for (unsigned i = 0; i < sizeof want / sizeof *want; i++) {
        int f = 0;
        for (uint32_t j = 0; j < ne; j++) if (!strcmp(ex[j].extensionName, want[i])) f = 1;
        printf("VK_EXT %s=%d\n", want[i], f);
    }
}

int main(void) {
    if (load()) return 1;
    dpy = p_eglGetDisplay(EGL_DEFAULT_DISPLAY);
    EGLint maj = 0, min = 0;
    if (!p_eglInitialize(dpy, &maj, &min)) { printf("EGL_INIT=FAIL 0x%x\n", p_eglGetError()); return 1; }
    const char *ext = p_eglQueryString(dpy, EGL_EXTENSIONS);
    printf("EGL_INIT=OK %d.%d vendor=%s\n", maj, min, p_eglQueryString(dpy, EGL_VENDOR));
    printf("EGL_EXTENSIONS=%s\n", ext);
    const char *toks[] = { "EGL_EXT_image_dma_buf_import", "EGL_EXT_image_dma_buf_import_modifiers",
                           "EGL_ANDROID_image_native_buffer", "EGL_ANDROID_get_native_client_buffer",
                           "EGL_KHR_image_base", "EGL_ANDROID_native_fence_sync" };
    for (unsigned i = 0; i < sizeof toks / sizeof *toks; i++)
        printf("EXT %s=%d\n", toks[i], has_token(ext, toks[i]));

    p_eglBindAPI(EGL_OPENGL_ES_API);
    EGLint cattr[] = { EGL_RENDERABLE_TYPE, EGL_OPENGL_ES2_BIT, EGL_SURFACE_TYPE, EGL_PBUFFER_BIT,
                       EGL_RED_SIZE, 8, EGL_GREEN_SIZE, 8, EGL_BLUE_SIZE, 8, EGL_ALPHA_SIZE, 8, EGL_NONE };
    EGLConfig cfg; EGLint nc = 0;
    if (!p_eglChooseConfig(dpy, cattr, &cfg, 1, &nc) || !nc) { printf("EGL_CONFIG=FAIL\n"); return 1; }
    EGLint xattr[] = { EGL_CONTEXT_CLIENT_VERSION, 2, EGL_NONE };
    EGLContext ctx = p_eglCreateContext(dpy, cfg, EGL_NO_CONTEXT, xattr);
    EGLint sattr[] = { EGL_WIDTH, 16, EGL_HEIGHT, 16, EGL_NONE };
    EGLSurface surf = p_eglCreatePbufferSurface(dpy, cfg, sattr);
    if (!ctx || !surf || !p_eglMakeCurrent(dpy, surf, surf, ctx)) { printf("EGL_CONTEXT=FAIL 0x%x\n", p_eglGetError()); return 1; }
    const char *gext = (const char *) p_glGetString(GL_EXTENSIONS);
    printf("GL_RENDERER=%s | %s\n", p_glGetString(GL_RENDERER), p_glGetString(GL_VERSION));
    printf("GLEXT GL_OES_EGL_image=%d GL_OES_EGL_image_external=%d GL_OES_EGL_image_external_essl3=%d\n",
           has_token(gext, "GL_OES_EGL_image"), has_token(gext, "GL_OES_EGL_image_external"),
           has_token(gext, "GL_OES_EGL_image_external_essl3"));

    p_eglCreateImageKHR = (PFNEGLCREATEIMAGEKHRPROC) p_eglGetProcAddress("eglCreateImageKHR");
    p_eglDestroyImageKHR = (PFNEGLDESTROYIMAGEKHRPROC) p_eglGetProcAddress("eglDestroyImageKHR");
    p_glEGLImageTargetTexture2DOES = (PFNGLEGLIMAGETARGETTEXTURE2DOESPROC) p_eglGetProcAddress("glEGLImageTargetTexture2DOES");
    printf("PROCS eglCreateImageKHR=%d glEGLImageTargetTexture2DOES=%d\n",
           !!p_eglCreateImageKHR, !!p_glEGLImageTargetTexture2DOES);
    if (!p_eglCreateImageKHR || !p_glEGLImageTargetTexture2DOES || gl_setup()) return 1;

    int fd = heap_alloc();
    if (fd >= 0) {
        const uint32_t fccs[] = { DRM_FORMAT_XRGB8888, DRM_FORMAT_ARGB8888, DRM_FORMAT_XBGR8888, DRM_FORMAT_ABGR8888 };
        for (unsigned i = 0; i < 4; i++) {
            run_case(fd, fccs[i], GL_TEXTURE_EXTERNAL_OES);
            run_case(fd, fccs[i], GL_TEXTURE_2D);
        }
    }

    /* C1: memfd is not a dma-buf; importing it must fail or the IMP result means nothing */
    int mfd = (int) syscall(__NR_memfd_create, "probe-c1", 0);
    if (mfd >= 0 && ftruncate(mfd, (off_t) buf_size()) == 0) {
        EGLint err;
        EGLImageKHR img = import(mfd, DRM_FORMAT_XRGB8888, &err);
        printf("C1_MEMFD_IMPORT=%s egl_err=0x%x (expected FAIL)\n", img ? "OK" : "FAIL", err);
        if (img) p_eglDestroyImageKHR(dpy, img);
    } else {
        printf("C1_MEMFD_IMPORT=NOT_RUN errno=%d\n", errno);
    }

    vk_probe();
    void *nw = dlopen("/system/lib64/libnativewindow.so", RTLD_NOW | RTLD_LOCAL);
    printf("AHB AHardwareBuffer_createFromHandle=%d\n", nw && dlsym(nw, "AHardwareBuffer_createFromHandle"));
    printf("DONE\n");
    return 0;
}
