// X3-DIRECT-FEAS-01 diagnostic (run after run-01; does not re-judge it).
// Reuses the probe's helpers. Adds:
//   GLEXT_ALL      full GL extension string
//   EGLT           error for an unknown EGLImage target vs EGL_LINUX_DMA_BUF_EXT variants
//                  (same error => the driver does not know the target at all)
//   MO             GL_EXT_memory_object_fd: import the dma-buf as an opaque fd into GL,
//                  (a) as a buffer object -> glTexSubImage2D from it as PIXEL_UNPACK (GPU copy,
//                      no CPU pixel work), check PIX and LIVE
//                  (b) as linear texture storage, check PIX against pitch 4864
//                  red control: memfd import
//   VKI            system Vulkan: vkGetMemoryFdPropertiesKHR(DMA_BUF) + vkAllocateMemory import,
//                  LINEAR image row pitch for 1200 px
#define main probe01_main
#include "egl_dmabuf_probe.c"
#undef main
#include <GLES3/gl3.h>

/* GLES3 entry points resolved from the system library, never linked */
static __typeof__(&glGenBuffers) q_glGenBuffers;
static __typeof__(&glBindBuffer) q_glBindBuffer;
static __typeof__(&glTexStorage2D) q_glTexStorage2D;
static __typeof__(&glTexSubImage2D) q_glTexSubImage2D;
#define glGenBuffers q_glGenBuffers
#define glBindBuffer q_glBindBuffer
#define glTexStorage2D q_glTexStorage2D
#define glTexSubImage2D q_glTexSubImage2D
#define glPixelStorei p_glPixelStorei

typedef void (*PFN_glCreateMemoryObjectsEXT)(GLsizei, GLuint *);
typedef void (*PFN_glImportMemoryFdEXT)(GLuint, GLuint64, GLenum, GLint);
typedef void (*PFN_glBufferStorageMemEXT)(GLenum, GLsizeiptr, GLuint, GLuint64);
typedef void (*PFN_glTexStorageMem2DEXT)(GLenum, GLsizei, GLenum, GLsizei, GLsizei, GLuint, GLuint64);
typedef void (*PFN_glMemoryObjectParameterivEXT)(GLuint, GLenum, const GLint *);
#ifndef GL_HANDLE_TYPE_OPAQUE_FD_EXT
#define GL_HANDLE_TYPE_OPAQUE_FD_EXT 0x9586
#endif
#ifndef GL_TEXTURE_TILING_EXT
#define GL_TEXTURE_TILING_EXT 0x9580
#define GL_LINEAR_TILING_EXT 0x9585
#endif
#ifndef GL_DEDICATED_MEMORY_OBJECT_EXT
#define GL_DEDICATED_MEMORY_OBJECT_EXT 0x9581
#endif

static void eglt(int fd) {
    EGLint a[] = { EGL_WIDTH, W, EGL_HEIGHT, H, EGL_NONE };
    EGLImageKHR img = p_eglCreateImageKHR(dpy, EGL_NO_CONTEXT, 0x31FE /* unassigned */, NULL, a);
    printf("EGLT unknown_target img=%d err=0x%x\n", !!img, p_eglGetError());
    struct { const char *name; int w, pitch, mod; } v[] = {
        { "w1200_p4800", 1200, 4800, 0 }, { "w1024_p4096", 1024, 4096, 0 },
        { "w1200_p4864_mod0", 1200, 4864, 1 }, { "w64_p256", 64, 256, 0 } };
    for (unsigned i = 0; i < 4; i++) {
        EGLint at[32]; int k = 0;
        at[k++] = EGL_WIDTH; at[k++] = v[i].w; at[k++] = EGL_HEIGHT; at[k++] = 64;
        at[k++] = EGL_LINUX_DRM_FOURCC_EXT; at[k++] = DRM_FORMAT_ABGR8888;
        at[k++] = EGL_DMA_BUF_PLANE0_FD_EXT; at[k++] = fd;
        at[k++] = EGL_DMA_BUF_PLANE0_OFFSET_EXT; at[k++] = 0;
        at[k++] = EGL_DMA_BUF_PLANE0_PITCH_EXT; at[k++] = v[i].pitch;
        if (v[i].mod) {
            at[k++] = EGL_DMA_BUF_PLANE0_MODIFIER_LO_EXT; at[k++] = 0;
            at[k++] = EGL_DMA_BUF_PLANE0_MODIFIER_HI_EXT; at[k++] = 0;
        }
        at[k++] = EGL_NONE;
        img = p_eglCreateImageKHR(dpy, EGL_NO_CONTEXT, EGL_LINUX_DMA_BUF_EXT, NULL, at);
        printf("EGLT dmabuf_%s img=%d err=0x%x\n", v[i].name, !!img, p_eglGetError());
    }
}

static PFN_glCreateMemoryObjectsEXT p_cmo;
static PFN_glImportMemoryFdEXT p_imfd;
static PFN_glBufferStorageMemEXT p_bsm;
static PFN_glTexStorageMem2DEXT p_tsm;
static PFN_glMemoryObjectParameterivEXT p_mop;

/* import fd (ownership passes to GL on success) */
static GLuint mo_import(int fd, int dedicated, GLenum *err) {
    GLuint mo = 0;
    while (p_glGetError()) {}
    p_cmo(1, &mo);
    if (dedicated) { GLint d = GL_TRUE; p_mop(mo, GL_DEDICATED_MEMORY_OBJECT_EXT, &d); }
    p_imfd(mo, (GLuint64) buf_size(), GL_HANDLE_TYPE_OPAQUE_FD_EXT, fd);
    *err = p_glGetError();
    return mo;
}

static void mo_buffer_path(int fd) {
    GLenum err;
    GLuint mo = mo_import(dup(fd), 0, &err);
    printf("MO_IMPORT[buffer] gl_err=0x%x\n", err);
    if (err) return;
    GLuint pbo;
    glGenBuffers(1, &pbo);
    glBindBuffer(GL_PIXEL_UNPACK_BUFFER, pbo);
    p_bsm(GL_PIXEL_UNPACK_BUFFER, (GLsizeiptr) buf_size(), mo, 0);
    err = p_glGetError();
    printf("MO_BUFSTORAGE gl_err=0x%x\n", err);
    if (err) { glBindBuffer(GL_PIXEL_UNPACK_BUFFER, 0); return; }

    GLuint tex;
    p_glGenTextures(1, &tex);
    p_glBindTexture(GL_TEXTURE_2D, tex);
    glTexStorage2D(GL_TEXTURE_2D, 1, GL_RGBA8, W, H);
    p_glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
    p_glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
    /* memory bytes are R,G,B,A per pixel = AB24; GL RGBA/UNSIGNED_BYTE reads them in that order */
    for (int v = 0; v < 3; v++) {
        fill(fd, v, v != 2);            /* v=2: no DMA_BUF_IOCTL_SYNC */
        glBindBuffer(GL_PIXEL_UNPACK_BUFFER, pbo);
        glPixelStorei(GL_UNPACK_ROW_LENGTH, PITCH / 4);
        p_glBindTexture(GL_TEXTURE_2D, tex);
        glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, W, H, GL_RGBA, GL_UNSIGNED_BYTE, (const void *) 0);
        GLenum e1 = p_glGetError();
        glPixelStorei(GL_UNPACK_ROW_LENGTH, 0);
        glBindBuffer(GL_PIXEL_UNPACK_BUFFER, 0);
        int de = draw_read(GL_TEXTURE_2D, tex);
        printf("MO_PBO_UPLOAD v=%d%s upload_err=0x%x draw_err=0x%x mismatch=%ld mismatch_flipped=%ld of=%d wrong_pattern_mismatch=%ld\n",
               v, v == 2 ? "(nosync)" : "", e1, de, compare(DRM_FORMAT_ABGR8888, v, 0),
               compare(DRM_FORMAT_ABGR8888, v, 1), W * H, compare(DRM_FORMAT_ABGR8888, (v + 1) % 3, 0));
    }
    p_glDeleteTextures(1, &tex);
}

static void mo_texture_path(int fd) {
    GLenum err;
    GLuint mo = mo_import(dup(fd), 0, &err);
    printf("MO_IMPORT[texture] gl_err=0x%x\n", err);
    if (err) return;
    GLuint tex;
    p_glGenTextures(1, &tex);
    p_glBindTexture(GL_TEXTURE_2D, tex);
    p_glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_TILING_EXT, GL_LINEAR_TILING_EXT);
    p_glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
    p_glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
    p_tsm(GL_TEXTURE_2D, 1, GL_RGBA8, W, H, mo, 0);
    err = p_glGetError();
    printf("MO_TEXSTORAGE gl_err=0x%x\n", err);
    if (err) return;
    fill(fd, 0, 1);
    int de = draw_read(GL_TEXTURE_2D, tex);
    printf("MO_TEX v=0 draw_err=0x%x mismatch=%ld mismatch_flipped=%ld of=%d\n", de,
           compare(DRM_FORMAT_ABGR8888, 0, 0), compare(DRM_FORMAT_ABGR8888, 0, 1), W * H);
    fill(fd, 1, 1);
    draw_read(GL_TEXTURE_2D, tex);
    printf("MO_TEX_LIVE v=1 mismatch_vs_new=%ld mismatch_vs_old=%ld\n",
           compare(DRM_FORMAT_ABGR8888, 1, 0), compare(DRM_FORMAT_ABGR8888, 0, 0));
    p_glDeleteTextures(1, &tex);
}

static void vki(int fd) {
    void *vk = dlopen("/system/lib64/libvulkan.so", RTLD_NOW | RTLD_LOCAL);
    PFN_vkGetInstanceProcAddr gipa = dlsym(vk, "vkGetInstanceProcAddr");
    PFN_vkCreateInstance ci = (PFN_vkCreateInstance) gipa(NULL, "vkCreateInstance");
    VkApplicationInfo ai = { VK_STRUCTURE_TYPE_APPLICATION_INFO, NULL, "diag", 1, NULL, 0, VK_API_VERSION_1_1 };
    VkInstanceCreateInfo ici = { VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO, NULL, 0, &ai, 0, NULL, 0, NULL };
    VkInstance inst;
    if (ci(&ici, NULL, &inst) != VK_SUCCESS) { printf("VKI=INSTANCE_FAIL\n"); return; }
    PFN_vkEnumeratePhysicalDevices epd = (PFN_vkEnumeratePhysicalDevices) gipa(inst, "vkEnumeratePhysicalDevices");
    PFN_vkGetPhysicalDeviceQueueFamilyProperties qfp =
        (PFN_vkGetPhysicalDeviceQueueFamilyProperties) gipa(inst, "vkGetPhysicalDeviceQueueFamilyProperties");
    PFN_vkCreateDevice cd = (PFN_vkCreateDevice) gipa(inst, "vkCreateDevice");
    PFN_vkGetDeviceProcAddr gdpa = (PFN_vkGetDeviceProcAddr) gipa(inst, "vkGetDeviceProcAddr");
    uint32_t n = 1; VkPhysicalDevice pd; epd(inst, &n, &pd);
    uint32_t nq = 1; VkQueueFamilyProperties qp; qfp(pd, &nq, &qp);
    float prio = 1.0f;
    VkDeviceQueueCreateInfo qci = { VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO, NULL, 0, 0, 1, &prio };
    const char *exts[] = { "VK_KHR_external_memory_fd", "VK_EXT_external_memory_dma_buf" };
    VkDeviceCreateInfo dci = { VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO, NULL, 0, 1, &qci, 0, NULL, 2, exts, NULL };
    VkDevice dev;
    VkResult r = cd(pd, &dci, NULL, &dev);
    if (r != VK_SUCCESS) { printf("VKI=DEVICE_FAIL %d\n", r); return; }
    PFN_vkGetMemoryFdPropertiesKHR gmfp = (PFN_vkGetMemoryFdPropertiesKHR) gdpa(dev, "vkGetMemoryFdPropertiesKHR");
    PFN_vkAllocateMemory am = (PFN_vkAllocateMemory) gdpa(dev, "vkAllocateMemory");
    PFN_vkCreateImage cimg = (PFN_vkCreateImage) gdpa(dev, "vkCreateImage");
    PFN_vkGetImageSubresourceLayout gisl = (PFN_vkGetImageSubresourceLayout) gdpa(dev, "vkGetImageSubresourceLayout");
    VkMemoryFdPropertiesKHR mp = { VK_STRUCTURE_TYPE_MEMORY_FD_PROPERTIES_KHR };
    r = gmfp(dev, VK_EXTERNAL_MEMORY_HANDLE_TYPE_DMA_BUF_BIT_EXT, fd, &mp);
    printf("VKI fd_props=%d memoryTypeBits=0x%x\n", r, mp.memoryTypeBits);
    uint32_t mt = 0;
    while (mt < 32 && !(mp.memoryTypeBits & (1u << mt))) mt++;
    if (r == VK_SUCCESS && mt < 32) {
        int d = dup(fd);
        VkImportMemoryFdInfoKHR imp = { VK_STRUCTURE_TYPE_IMPORT_MEMORY_FD_INFO_KHR, NULL,
                                        VK_EXTERNAL_MEMORY_HANDLE_TYPE_DMA_BUF_BIT_EXT, d };
        VkMemoryAllocateInfo mai = { VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO, &imp, buf_size(), mt };
        VkDeviceMemory mem;
        r = am(dev, &mai, NULL, &mem);
        printf("VKI import_alloc=%d type=%u\n", r, mt);
        if (r != VK_SUCCESS) close(d);
    }
    VkImageCreateInfo ic = { VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO, NULL, 0, VK_IMAGE_TYPE_2D,
                             VK_FORMAT_R8G8B8A8_UNORM, { W, H, 1 }, 1, 1, VK_SAMPLE_COUNT_1_BIT,
                             VK_IMAGE_TILING_LINEAR, VK_IMAGE_USAGE_SAMPLED_BIT | VK_IMAGE_USAGE_TRANSFER_DST_BIT,
                             VK_SHARING_MODE_EXCLUSIVE, 0, NULL, VK_IMAGE_LAYOUT_UNDEFINED };
    VkImage img;
    if (cimg(dev, &ic, NULL, &img) == VK_SUCCESS) {
        VkImageSubresource sr = { VK_IMAGE_ASPECT_COLOR_BIT, 0, 0 };
        VkSubresourceLayout sl; gisl(dev, img, &sr, &sl);
        printf("VKI linear_rowPitch[w=%d]=%llu offset=%llu\n", W, (unsigned long long) sl.rowPitch,
               (unsigned long long) sl.offset);
    }
}

int main(void) {
    if (load()) return 1;
    q_glGenBuffers = dlsym(gles_lib, "glGenBuffers");
    q_glBindBuffer = dlsym(gles_lib, "glBindBuffer");
    q_glTexStorage2D = dlsym(gles_lib, "glTexStorage2D");
    q_glTexSubImage2D = dlsym(gles_lib, "glTexSubImage2D");
    if (!q_glGenBuffers || !q_glBindBuffer || !q_glTexStorage2D || !q_glTexSubImage2D) { printf("LOAD3=FAIL\n"); return 1; }
    dpy = p_eglGetDisplay(EGL_DEFAULT_DISPLAY);
    EGLint maj, min;
    p_eglInitialize(dpy, &maj, &min);
    p_eglBindAPI(EGL_OPENGL_ES_API);
    EGLint cattr[] = { EGL_RENDERABLE_TYPE, EGL_OPENGL_ES3_BIT_KHR, EGL_SURFACE_TYPE, EGL_PBUFFER_BIT,
                       EGL_RED_SIZE, 8, EGL_GREEN_SIZE, 8, EGL_BLUE_SIZE, 8, EGL_ALPHA_SIZE, 8, EGL_NONE };
    EGLConfig cfg; EGLint nc = 0;
    p_eglChooseConfig(dpy, cattr, &cfg, 1, &nc);
    EGLint xattr[] = { EGL_CONTEXT_CLIENT_VERSION, 3, EGL_NONE };
    EGLContext ctx = p_eglCreateContext(dpy, cfg, EGL_NO_CONTEXT, xattr);
    EGLint sattr[] = { EGL_WIDTH, 16, EGL_HEIGHT, 16, EGL_NONE };
    EGLSurface surf = p_eglCreatePbufferSurface(dpy, cfg, sattr);
    if (!nc || !ctx || !surf || !p_eglMakeCurrent(dpy, surf, surf, ctx)) { printf("CTX=FAIL 0x%x\n", p_eglGetError()); return 1; }
    printf("GL_VERSION=%s\n", p_glGetString(GL_VERSION));
    const char *gext = (const char *) p_glGetString(GL_EXTENSIONS);
    printf("GLEXT_ALL=%s\n", gext);
    printf("GLEXT GL_EXT_memory_object=%d GL_EXT_memory_object_fd=%d GL_EXT_semaphore_fd=%d GL_EXT_EGL_image_storage=%d\n",
           has_token(gext, "GL_EXT_memory_object"), has_token(gext, "GL_EXT_memory_object_fd"),
           has_token(gext, "GL_EXT_semaphore_fd"), has_token(gext, "GL_EXT_EGL_image_storage"));
    p_eglCreateImageKHR = (PFNEGLCREATEIMAGEKHRPROC) p_eglGetProcAddress("eglCreateImageKHR");
    p_eglDestroyImageKHR = (PFNEGLDESTROYIMAGEKHRPROC) p_eglGetProcAddress("eglDestroyImageKHR");
    p_glEGLImageTargetTexture2DOES = (PFNGLEGLIMAGETARGETTEXTURE2DOESPROC) p_eglGetProcAddress("glEGLImageTargetTexture2DOES");
    if (gl_setup()) return 1;

    int fd = heap_alloc();
    if (fd < 0) return 1;
    eglt(fd);

    p_cmo = (PFN_glCreateMemoryObjectsEXT) p_eglGetProcAddress("glCreateMemoryObjectsEXT");
    p_imfd = (PFN_glImportMemoryFdEXT) p_eglGetProcAddress("glImportMemoryFdEXT");
    p_bsm = (PFN_glBufferStorageMemEXT) p_eglGetProcAddress("glBufferStorageMemEXT");
    p_tsm = (PFN_glTexStorageMem2DEXT) p_eglGetProcAddress("glTexStorageMem2DEXT");
    p_mop = (PFN_glMemoryObjectParameterivEXT) p_eglGetProcAddress("glMemoryObjectParameterivEXT");
    printf("MO_PROCS create=%d importfd=%d bufstorage=%d texstorage=%d param=%d\n",
           !!p_cmo, !!p_imfd, !!p_bsm, !!p_tsm, !!p_mop);
    if (p_cmo && p_imfd && p_bsm && p_tsm && p_mop) {
        mo_buffer_path(fd);
        mo_texture_path(fd);
        /* red control: memfd imported as an opaque fd must not give usable memory */
        int mfd = (int) syscall(__NR_memfd_create, "diag-c1", 0);
        if (mfd >= 0 && ftruncate(mfd, (off_t) buf_size()) == 0) {
            GLenum err;
            mo_import(mfd, 0, &err);
            printf("MO_C1_MEMFD_IMPORT gl_err=0x%x (expected nonzero)\n", err);
        }
    }
    vki(fd);
    printf("DONE\n");
    return 0;
}
