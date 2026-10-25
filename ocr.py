"""Small wrapper around the Windows built-in OCR engine."""
import asyncio
import cv2
import numpy as np
from winrt.windows.media.ocr import OcrEngine
from winrt.windows.globalization import Language
from winrt.windows.graphics.imaging import SoftwareBitmap, BitmapPixelFormat, BitmapAlphaMode
from winrt.windows.storage.streams import DataWriter

_engine = OcrEngine.try_create_from_language(Language("en-US"))


def _to_bitmap(bgr):
    bgra = cv2.cvtColor(bgr, cv2.COLOR_BGR2BGRA)
    h, w = bgra.shape[:2]
    writer = DataWriter()
    writer.write_bytes(bgra.tobytes())
    buf = writer.detach_buffer()
    return SoftwareBitmap.create_copy_from_buffer(buf, BitmapPixelFormat.BGRA8, w, h, BitmapAlphaMode.PREMULTIPLIED)


async def _recognize(bgr):
    return await _engine.recognize_async(_to_bitmap(bgr))


def read_words(bgr, scale=1.0):
    """Returns a list of (text, x, y, w, h) in the coordinates of the given image."""
    img = bgr if scale == 1.0 else cv2.resize(bgr, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    result = asyncio.run(_recognize(img))
    words = []
    for line in result.lines:
        for w in line.words:
            r = w.bounding_rect
            words.append((w.text, r.x / scale, r.y / scale, r.width / scale, r.height / scale))
    return words


def read_text(bgr, scale=1.0):
    return " ".join(w[0] for w in read_words(bgr, scale))
