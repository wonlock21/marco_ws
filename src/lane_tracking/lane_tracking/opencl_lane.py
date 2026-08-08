"""Mali GPU uzerinde adaptif serit maskesi ureten OpenCL islem hatti."""

import numpy as np
import pyopencl as cl


_KERNEL_SOURCE = r"""
__kernel void bgr_to_gray(
    __global const uchar *bgr,
    __global uchar *gray,
    const int width,
    const int height)
{
    const int x = get_global_id(0);
    const int y = get_global_id(1);
    if (x >= width || y >= height) return;

    const int pixel = y * width + x;
    const int base = pixel * 3;
    const int value = 29 * (int)bgr[base]
        + 150 * (int)bgr[base + 1]
        + 77 * (int)bgr[base + 2] + 128;
    gray[pixel] = (uchar)(value >> 8);
}

__kernel void horizontal_sum(
    __global const uchar *gray,
    __global int *sums,
    const int width,
    const int height,
    const int radius)
{
    const int x = get_global_id(0);
    const int y = get_global_id(1);
    if (x >= width || y >= height) return;

    int total = 0;
    for (int dx = -radius; dx <= radius; ++dx) {
        const int xx = clamp(x + dx, 0, width - 1);
        total += (int)gray[y * width + xx];
    }
    sums[y * width + x] = total;
}

__kernel void adaptive_dark_mask(
    __global const uchar *gray,
    __global const int *horizontal,
    __global uchar *mask,
    const int width,
    const int height,
    const int radius,
    const int offset,
    const int value_max)
{
    const int x = get_global_id(0);
    const int y = get_global_id(1);
    if (x >= width || y >= height) return;

    int total = 0;
    for (int dy = -radius; dy <= radius; ++dy) {
        const int yy = clamp(y + dy, 0, height - 1);
        total += horizontal[yy * width + x];
    }
    const int pixel = y * width + x;
    const int side = radius * 2 + 1;
    const int area = side * side;
    const int value = (int)gray[pixel];
    mask[pixel] = (value <= value_max && (value + offset) * area < total)
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
    """BGR kareden yerel aydinlatmaya dayali ikili maske uretir."""

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
        self._bgr_to_gray = program.bgr_to_gray
        self._horizontal_sum = program.horizontal_sum
        self._adaptive_dark_mask = program.adaptive_dark_mask
        self._erode5 = program.erode5
        self._dilate5 = program.dilate5

        self._shape = None
        self._src = None
        self._gray = None
        self._horizontal = None
        self._mask = None
        self._temp = None
        self._result = None

    @property
    def device_name(self):
        return self.device.name.strip()

    def process(self, frame, value_max=100, block_size=81, offset=23):
        frame = np.ascontiguousarray(frame, dtype=np.uint8)
        height, width, channels = frame.shape
        if channels != 3:
            raise ValueError('OpenCL serit maskesi 3 kanalli BGR kare bekler')
        self._ensure_buffers(height, width)

        radius = max(1, (int(block_size) - 1) // 2)
        cl.enqueue_copy(self.queue, self._src, frame, is_blocking=False)
        global_size = (width, height)
        dims = (np.int32(width), np.int32(height))
        self._bgr_to_gray(
            self.queue, global_size, None, self._src, self._gray, *dims)
        self._horizontal_sum(
            self.queue, global_size, None, self._gray, self._horizontal,
            *dims, np.int32(radius))
        self._adaptive_dark_mask(
            self.queue, global_size, None, self._gray, self._horizontal,
            self._mask, *dims, np.int32(radius), np.int32(offset),
            np.int32(value_max))
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
        self._gray = cl.Buffer(
            self.context, flags.READ_WRITE, size=pixel_count)
        self._horizontal = cl.Buffer(
            self.context, flags.READ_WRITE, size=pixel_count * 4)
        self._mask = cl.Buffer(
            self.context, flags.READ_WRITE, size=pixel_count)
        self._temp = cl.Buffer(
            self.context, flags.READ_WRITE, size=pixel_count)
        self._result = np.empty(shape, dtype=np.uint8)
        self._shape = shape
