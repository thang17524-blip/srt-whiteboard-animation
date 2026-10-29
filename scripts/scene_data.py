"""Kiểm tra cấu hình vùng vẽ dùng chung cho giao diện và lệnh gốc."""
from __future__ import annotations

import copy
import math


def number(value, label, minimum=0):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < minimum:
        raise ValueError(f"{label} phải là số hữu hạn, tối thiểu {minimum}.")
    return value


def integer(value, label, minimum=0):
    number(value, label, minimum)
    if int(value) != value:
        raise ValueError(f"{label} phải là số nguyên.")
    return int(value)


def validate_annotation(annotation, image_size=None, total_ms=None, fps=30):
    """Giữ JSON cũ; từ chối thời gian chồng lấn thay vì âm thầm kéo dài video."""
    ann = copy.deepcopy(annotation)
    if not isinstance(ann, dict) or not isinstance(ann.get('canvas'), dict):
        raise ValueError('Thiếu thông tin khung hình canvas.')
    w = integer(ann['canvas'].get('width'), 'Chiều rộng', 16)
    h = integer(ann['canvas'].get('height'), 'Chiều cao', 16)
    if image_size is not None and (w, h) != tuple(image_size):
        raise ValueError('Kích thước canvas phải trùng kích thước ảnh gốc.')
    fps = integer(fps, 'Số khung hình/giây', 1)
    elements = ann.get('elements')
    if not isinstance(elements, list) or not elements:
        raise ValueError('Cảnh cần có ít nhất một vùng vẽ.')

    def rectangle(rect):
        if not isinstance(rect, dict):
            raise ValueError('Vùng vẽ phải có x, y, width, height.')
        x = integer(rect.get('x'), 'Tọa độ x')
        y = integer(rect.get('y'), 'Tọa độ y')
        rw = integer(rect.get('width'), 'Chiều rộng vùng', 1)
        rh = integer(rect.get('height'), 'Chiều cao vùng', 1)
        if x + rw > w or y + rh > h:
            raise ValueError('Vùng vẽ hoặc vùng bảo vệ vượt khỏi ảnh.')

    for e in elements:
        if not isinstance(e, dict) or not isinstance(e.get('reveal'), dict):
            raise ValueError('Vùng vẽ thiếu thông tin reveal.')
        rectangle(e.get('region'))
        for protected in e['reveal'].get('protectedRegions', []):
            rectangle(protected)
        number(e['reveal'].get('startMs'), 'Thời điểm bắt đầu')
        number(e['reveal'].get('durationMs'), 'Thời lượng vùng', 2000 / fps)
    elements.sort(key=lambda e: e['reveal']['startMs'])
    previous_end = 0
    for i, e in enumerate(elements, 1):
        start = e['reveal']['startMs']
        if start < previous_end:
            raise ValueError('Thời gian các vùng vẽ bị chồng lấn. Hãy sửa thời điểm bắt đầu.')
        previous_end = start + e['reveal']['durationMs']
        e['sequence'] = i
    duration = total_ms if total_ms is not None else ann.get('sceneDurationMs', previous_end + 500)
    number(duration, 'Thời lượng cảnh', 1)
    if round(duration * fps / 1000) < round(previous_end * fps / 1000) + round(0.5 * fps):
        raise ValueError('Thời lượng cảnh cần đủ thời gian vẽ và ít nhất 0,5 giây xem hình cuối.')
    ann['sceneDurationMs'] = duration
    return ann
