// FEAS-02 diagnostic: memory requirements of dma-buf-backed VkBuffer / LINEAR VkImage on the
// system Adreno driver (FEAS-02 run-01 stopped at req.size 627892 > dma-buf 622592).
#include "feas02_body.inc"
int main(void) {
    if (vk_init()) return 1;
    PFN_vkGetImageMemoryRequirements gimr = (PFN_vkGetImageMemoryRequirements) g_gdpa(dev, "vkGetImageMemoryRequirements");
    PFN_vkGetImageSubresourceLayout gisl = (PFN_vkGetImageSubresourceLayout) g_gdpa(dev, "vkGetImageSubresourceLayout");
    VkDeviceSize sizes[] = { 4096, 65536, 622528, 622592, 1048576, 11984896 };
    for (int ext = 0; ext < 2; ext++)
        for (unsigned i = 0; i < sizeof sizes / sizeof *sizes; i++) {
            VkExternalMemoryBufferCreateInfo e = { VK_STRUCTURE_TYPE_EXTERNAL_MEMORY_BUFFER_CREATE_INFO, NULL,
                                                   VK_EXTERNAL_MEMORY_HANDLE_TYPE_DMA_BUF_BIT_EXT };
            VkBufferCreateInfo bci = { VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO, ext ? &e : NULL, 0, sizes[i],
                                       VK_BUFFER_USAGE_TRANSFER_SRC_BIT, VK_SHARING_MODE_EXCLUSIVE, 0, NULL };
            VkBuffer b; VkResult r = v_vkCreateBuffer(dev, &bci, NULL, &b);
            VkMemoryRequirements q = { 0 }; if (!r) v_vkGetBufferMemoryRequirements(dev, b, &q);
            printf("BUFREQ ext=%d size=%llu -> req=%llu (+%lld) align=%llu bits=0x%x\n", ext, (unsigned long long) sizes[i],
                   (unsigned long long) q.size, (long long) (q.size - sizes[i]), (unsigned long long) q.alignment, q.memoryTypeBits);
        }
    struct { uint32_t w, h; } iv[] = { { 1200, 128 }, { 1216, 128 }, { 1216, 2464 }, { 1200, 2464 }, { 640, 480 }, { 656, 480 } };
    VkFormat fmts[] = { VK_FORMAT_B8G8R8A8_UNORM, VK_FORMAT_R8G8B8A8_UNORM };
    for (int f = 0; f < 2; f++)
        for (unsigned i = 0; i < sizeof iv / sizeof *iv; i++) {
            VkExternalMemoryImageCreateInfo e = { VK_STRUCTURE_TYPE_EXTERNAL_MEMORY_IMAGE_CREATE_INFO, NULL,
                                                  VK_EXTERNAL_MEMORY_HANDLE_TYPE_DMA_BUF_BIT_EXT };
            VkImageCreateInfo ici = { VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO, &e, 0, VK_IMAGE_TYPE_2D, fmts[f], { iv[i].w, iv[i].h, 1 },
                                      1, 1, VK_SAMPLE_COUNT_1_BIT, VK_IMAGE_TILING_LINEAR, VK_IMAGE_USAGE_TRANSFER_SRC_BIT,
                                      VK_SHARING_MODE_EXCLUSIVE, 0, NULL, VK_IMAGE_LAYOUT_UNDEFINED };
            VkImage im; VkResult r = v_vkCreateImage(dev, &ici, NULL, &im);
            VkMemoryRequirements q = { 0 }; VkSubresourceLayout sl = { 0 };
            if (!r) {
                gimr(dev, im, &q);
                VkImageSubresource sr = { VK_IMAGE_ASPECT_COLOR_BIT, 0, 0 };
                gisl(dev, im, &sr, &sl);
            }
            printf("IMGREQ fmt=%s %ux%u create=%d rowPitch=%llu size=%llu offset=%llu req=%llu (pitch*h=%llu, +%lld) align=%llu\n",
                   f ? "RGBA" : "BGRA", iv[i].w, iv[i].h, r, (unsigned long long) sl.rowPitch, (unsigned long long) sl.size,
                   (unsigned long long) sl.offset, (unsigned long long) q.size,
                   (unsigned long long) sl.rowPitch * iv[i].h, (long long) (q.size - sl.rowPitch * iv[i].h),
                   (unsigned long long) q.alignment);
        }
    printf("DONE\n");
    return 0;
}
