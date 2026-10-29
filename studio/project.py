from __future__ import annotations

import copy
import json
import math
import os
import shutil
import uuid
from pathlib import Path

import av
from PIL import Image, ImageOps

SCHEMA_VERSION = 1
SIZES = {'16:9': (1920, 1080), '9:16': (1080, 1920)}
PAPER = '#F6F1E3'


def new_project(name='Dự án mới'):
    return {'schemaVersion': SCHEMA_VERSION, 'name': name, 'aspectRatio': '16:9',
            'fps': 30, 'paper': PAPER, 'showHand': True, 'scenes': []}


def new_scene(script=''):
    return {'id': uuid.uuid4().hex, 'name': 'Cảnh mới', 'script': script,
            'image': '', 'audio': '', 'annotation': '', 'durationMs': 5000}


def resolve_asset(root, name):
    return (Path(root) / name).resolve() if name else None


def import_asset(source, root):
    source = Path(source).resolve()
    if not source.is_file():
        raise ValueError('Tệp được chọn không tồn tại.')
    folder = Path(root) / 'media'
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / (uuid.uuid4().hex[:12] + source.suffix.lower())
    shutil.copy2(source, target)
    return target.relative_to(root).as_posix()


def audio_duration_ms(path):
    with av.open(str(path)) as container:
        if not container.streams.audio:
            raise ValueError('Tệp không chứa giọng đọc/âm thanh.')
        stream = container.streams.audio[0]
        # Đếm mẫu thật để không tin metadata thời lượng MP3 không chính xác.
        seconds = sum(frame.samples / frame.sample_rate for frame in container.decode(stream))
    if not math.isfinite(seconds) or seconds <= 0:
        raise ValueError('Tệp âm thanh rỗng hoặc không đọc được.')
    return math.ceil(seconds * 30) * 1000 // 30 + 1


def validate_project(project, root, require_images=True):
    if not isinstance(project, dict) or project.get('schemaVersion') != SCHEMA_VERSION:
        raise ValueError('Phiên bản tệp dự án không được hỗ trợ.')
    if project.get('aspectRatio') not in SIZES or project.get('fps') != 30:
        raise ValueError('Chọn tỷ lệ 16:9 hoặc 9:16 và tốc độ 30 hình/giây.')
    if project.get('paper') != PAPER:
        raise ValueError('Phiên bản này dùng giấy màu kem cố định để các cảnh nhất quán.')
    scenes = project.get('scenes')
    if not isinstance(scenes, list) or (require_images and not scenes):
        raise ValueError('Hãy thêm ít nhất một cảnh.')
    ids = set()
    for i, scene in enumerate(scenes, 1):
        if not isinstance(scene, dict) or not scene.get('id') or scene['id'] in ids:
            raise ValueError('Mã cảnh thiếu hoặc bị trùng.')
        ids.add(scene['id'])
        duration = scene.get('durationMs')
        if isinstance(duration, bool) or not isinstance(duration, (float, int)) or not math.isfinite(duration) or not 1000 <= duration <= 3600000:
            raise ValueError(f'Cảnh {i}: thời lượng phải từ 1 đến 3600 giây.')
        for field in ['script', 'name', 'image', 'audio', 'annotation']:
            if not isinstance(scene.get(field, ''), str):
                raise ValueError(f'Cảnh {i}: trường {field} không hợp lệ.')
        for field in ['image', 'audio', 'annotation']:
            name = scene.get(field)
            if name and not resolve_asset(root, name).is_file():
                raise ValueError(f'Cảnh {i}: không tìm thấy tệp {field}: {name}')
        if require_images and not scene.get('image'):
            raise ValueError(f'Cảnh {i}: hãy thêm hình ảnh trước khi tạo video.')
        if scene.get('image'):
            with Image.open(resolve_asset(root, scene['image'])) as image:
                image.verify()
        if scene.get('audio'):
            voice_ms = audio_duration_ms(resolve_asset(root, scene['audio']))
            if voice_ms > duration + 1000 / 30:
                raise ValueError(f'Cảnh {i}: thời lượng ngắn hơn giọng đọc. Hãy tăng thời lượng.')
    return project


def save_project(project, filename):
    filename = Path(filename)
    validate_project(project, filename.parent, require_images=False)
    temporary = filename.with_suffix('.json.tmp')
    temporary.write_text(json.dumps(project, ensure_ascii=False, indent=2), encoding='utf-8')
    os.replace(temporary, filename)


def load_project(filename):
    filename = Path(filename)
    data = json.loads(filename.read_text(encoding='utf-8-sig'))
    return validate_project(data, filename.parent, require_images=False)


def prepared_scene(scene, root, size, fps=30):
    """Không kéo giãn ảnh; tọa độ JSON cũ được chuyển theo đúng phép ghép ảnh."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
    from scene_data import validate_annotation
    with Image.open(resolve_asset(root, scene['image'])) as source:
        image = ImageOps.exif_transpose(source).convert('RGBA')
        original = image.size
        if min(original) < 16:
            raise ValueError('Ảnh cần có chiều rộng và chiều cao tối thiểu 16 pixel.')
        background = Image.new('RGBA', original, PAPER)
        background.alpha_composite(image)
        image = background.convert('RGB')
    width, height = size
    factor = min(width / original[0], height / original[1])
    fitted = image.resize((max(1, round(original[0]*factor)), max(1, round(original[1]*factor))), Image.Resampling.LANCZOS)
    x, y = (width-fitted.width)//2, (height-fitted.height)//2
    canvas = Image.new('RGB', size, PAPER)
    canvas.paste(fitted, (x, y))
    frame_count = round(scene['durationMs'] * fps / 1000)
    duration = frame_count * 1000 / fps
    if scene.get('annotation'):
        ann = json.loads(resolve_asset(root, scene['annotation']).read_text(encoding='utf-8-sig'))
        ann = validate_annotation(ann, original, fps=fps)
        source_duration = ann['sceneDurationMs']
        for element in ann['elements']:
            for rect in [element['region'], *element['reveal'].get('protectedRegions', [])]:
                left = x + round(rect['x'] * fitted.width / original[0])
                top = y + round(rect['y'] * fitted.height / original[1])
                right = x + round((rect['x']+rect['width']) * fitted.width / original[0])
                bottom = y + round((rect['y']+rect['height']) * fitted.height / original[1])
                rect.update(x=left, y=top, width=max(1, right-left), height=max(1,bottom-top))
            # Giữ đúng 0,5 giây cuối; co lịch vẽ vào phần còn lại.
            ratio = (duration-500) / (source_duration-500)
            element['reveal']['startMs'] *= ratio
            element['reveal']['durationMs'] *= ratio
    else:
        ann = {'elements': [{'id': 'whole', 'label': 'Toàn bộ hình', 'sequence': 1,
                'subtitle': scene.get('script', ''), 'region': {'x': x, 'y': y, 'width': fitted.width, 'height': fitted.height},
                'reveal': {'startMs': 100, 'durationMs': duration-600, 'protectedRegions': []}}]}
    ann.update(canvas={'width': width, 'height': height}, sceneDurationMs=duration)
    return canvas, validate_annotation(ann, size, fps=fps)
