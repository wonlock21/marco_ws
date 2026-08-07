"""Mali GPU uzerinde serit maskesi ureten OpenCL islem hatti."""

import numpy as np
import pyopencl as cl


_KERNEL_SOURCE = r"""
__kernel void dark_mask(
    __global const uchar *bgr,
    __global uchar *mask,
    const int width,
    const int height,
    const uchar value_max)
{
    const int x = get_global_id(0);
    const int y = get_global_id(1);
    if (x >= width || y >= height) return;

    const int pixel = y * width + x;
    const int base = pixel * 3;
    const uchar b = bgr[base];
    const uchar g = bgr[base + 1];
    const uchar r = bgr[base + 2];
    mask[pixel] = (b <= value_max && g <= value_max && r <= value_max)
        ? (uchar)255 : (uchar)0;
}

__kernel void erode5(
    __global const uchar *src,
    __global uchar *dst,
    const int width,
    const int height)
{
    const int x = get_global_id(0);
    const int y = get_global_id(1);
    if (x >= width || y >= height) return;

    uchar result = 255;
    for (int dy = -2; dy <= 2; ++dy) {
        const int yy = y + dy;
        if (yy < 0 || yy >= height) continue;
        for (int dx = -2; dx <= 2; ++dx) {
            const int xx = x + dx;
            if (xx < 0 || xx >= width) continue;
            result = min(result, src[yy * width + xx]);
        }
    }
    dst[y * width + x] = result;
}

__kernel void dilate5(
    __global const uchar *src,
    __global uchar *dst,
    const int width,
    const int height)
{
    const int x = get_global_id(0);
    const int y = get_global_id(1);
    if (x >= width || y >= height) return;

    uchar result = 0;
    for (int dy = -2; dy <= 2; ++dy) {
        const int yy = y + dy;
        if (yy < 0 || yy >= height) continue;
        for (int dx = -2; dx <= 2; ++dx) {
            const int xx = x + dx;
            if (xx < 0 || xx >= width) continue;
            result = max(result, src[yy * width + xx]);
        }
    }
    dst[y * width + x] = result;
}
"""


class OpenClLaneMask:
    """BGR kareden ikili serit maskesini Mali GPU ile uretir."""

    def __init__(self):
        gpu_devices = []
        for platform in cl.get_platforms():
            gpu_devices.extend(platform.get_devices(
                device_type=cl.device_type.GPU))
        if not gpu_devices:
            raise RuntimeError('OpenCL GPU aygiti bulunamadi')

        self.device = gpu_devices[0]
        self.context = cl.Context([self.device])
        self.queue = cl.CommandQueue(self.context)
        program = cl.Program(self.context, _KERNEL_SOURCE).build()
        self._dark_mask = program.dark_mask
        self._erode5 = program.erode5
        self._dilate5 = program.dilate5

        self._shape = None
        self._src = None
        self._mask = None
        self._temp = None
        self._result = None

    @property
    def device_name(self):
        return self.device.name.strip()

    def process(self, frame, value_max=50):
        frame = np.ascontiguousarray(frame, dtype=np.uint8)
        height, width, channels = frame.shape
        if channels != 3:
            raise ValueError('OpenCL serit maskesi 3 kanalli BGR kare bekler')
        self._ensure_buffers(height, width)

        cl.enqueue_copy(self.queue, self._src, frame, is_blocking=False)
        global_size = (width, height)
        dims = (np.int32(width), np.int32(height))
        self._dark_mask(
            self.queue, global_size, None, self._src, self._mask,
            *dims, np.uint8(value_max))
        self._erode5(
            self.queue, global_size, None, self._mask, self._temp, *dims)
        self._dilate5(
            self.queue, global_size, None, self._temp, self._mask, *dims)
        cl.enqueue_copy(
            self.queue, self._result, self._mask, is_blocking=True)
        return self._result

    def _ensure_buffers(self, height, width):
        shape = (height, width)
        if shape == self._shape:
            return

        flags = cl.mem_flags
        pixel_count = height * width
        self._src = cl.Buffer(
            self.context, flags.READ_ONLY, size=pixel_count * 3)
        self._mask = cl.Buffer(
            self.context, flags.READ_WRITE, size=pixel_count)
        self._temp = cl.Buffer(
            self.context, flags.READ_WRITE, size=pixel_count)
        self._result = np.empty(shape, dtype=np.uint8)
        self._shape = shape
