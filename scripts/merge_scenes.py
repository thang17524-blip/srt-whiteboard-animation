#!/usr/bin/env python3
"""
多幕合并：把各场景的白板动画 MP4 按顺序硬切拼接成一条完整视频。

优先用系统 ffmpeg 无损拼接（-c copy，不重编码）；各片尺寸/编码不一致或无
ffmpeg 时，回退到 PyAV 逐帧重编码并缩放补边到第一段尺寸。单片仍保留。

用法：
  <ENV_PY> merge_scenes.py --inputs a.mp4 b.mp4 c.mp4 --output final.mp4
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def _ffmpeg_concat_copy(inputs: list[Path], output: Path) -> bool:
    from video_io import run_ffmpeg
    import av
    # Chuẩn hóa từng đoạn trước khi nối: giữ tỷ lệ, thời gian và mọi âm thanh.
    try:
        if not inputs or output.resolve() in {p.resolve() for p in inputs}:
            raise ValueError('Tệp đầu ra phải khác tệp đầu vào.')
        with av.open(str(inputs[0])) as first:
            vs = first.streams.video[0]
            width, height = vs.width // 2 * 2, vs.height // 2 * 2
            fps = vs.average_rate or 30
        with tempfile.TemporaryDirectory(prefix='whiteboard-merge-') as folder:
            clips = []
            for i, path in enumerate(inputs):
                with av.open(str(path)) as source:
                    has_audio = bool(source.streams.audio)
                    stream = source.streams.video[0]
                    duration = float(stream.duration * stream.time_base) if stream.duration is not None else float(source.duration / av.time_base)
                clip = Path(folder) / f'{i}.mov'
                audio = [] if has_audio else ['-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=stereo']
                audio_map = '0:a:0' if has_audio else '1:a:0'
                run_ffmpeg(['-i', path, *audio, '-map', '0:v:0', '-map', audio_map,
                            '-vf', f'scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1',
                            '-r', str(fps), '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p',
                            '-af', 'apad', '-c:a', 'pcm_s16le', '-ar', '48000', '-ac', '2', '-t', str(duration), clip])
                clips.append(clip)
            listing = Path(folder) / 'concat.txt'
            listing.write_text(''.join("file '" + p.as_posix().replace("'", "'\\''") + "'\n" for p in clips), encoding='utf-8')
            complete = Path(folder) / 'complete.mp4'
            run_ffmpeg(['-f', 'concat', '-safe', '0', '-i', listing, '-c:v', 'copy',
                        '-c:a', 'aac', '-ar', '48000', '-ac', '2', '-movflags', '+faststart', complete])
            import shutil as file_tools
            file_tools.copyfile(complete, output)
        return True
    except (RuntimeError, ValueError, OSError, av.error.FFmpegError) as exc:
        print(f'[warn] Không ghép được bằng FFmpeg: {exc}', file=sys.stderr)
        return False


def _legacy_ffmpeg_concat_copy(inputs: list[Path], output: Path) -> bool:
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        return False
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
        for p in inputs:
            f.write(f"file '{p.resolve().as_posix()}'\n")
        list_path = Path(f.name)
    try:
        res = subprocess.run(
            [ffmpeg, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
             "-i", str(list_path), "-c", "copy", str(output)],
            capture_output=True, text=True,
        )
        if res.returncode == 0:
            print(f"  ffmpeg 无损拼接完成: {output}")
            return True
        print(f"  [warn] ffmpeg -c copy 失败，尝试重编码: {res.stderr.strip()[:200]}")
        res = subprocess.run(
            [ffmpeg, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
             "-i", str(list_path), "-c:v", "libx264", "-crf", "20",
             "-pix_fmt", "yuv420p", "-vf", "scale='trunc(iw/2)*2':'trunc(ih/2)*2'", str(output)],
            capture_output=True, text=True,
        )
        if res.returncode == 0:
            print(f"  ffmpeg 重编码拼接完成: {output}")
            return True
        print(f"  [warn] ffmpeg 重编码也失败: {res.stderr.strip()[:200]}")
        return False
    finally:
        list_path.unlink(missing_ok=True)


def _pyav_concat(inputs: list[Path], output: Path) -> bool:
    try:
        import av
    except ImportError:
        return False
    for path in inputs:
        with av.open(str(path)) as probe:
            if probe.streams.audio:
                raise RuntimeError('Cần FFmpeg để ghép và giữ âm thanh. Hãy cài imageio-ffmpeg.')
    if output.resolve() in {p.resolve() for p in inputs}:
        raise ValueError('Tệp đầu ra phải khác tệp đầu vào.')
    import numpy as np  # noqa: F401
    first = av.open(str(inputs[0]))
    vs = first.streams.video[0]
    w, h = vs.codec_context.width, vs.codec_context.height
    rate = vs.average_rate
    first.close()

    out = av.open(str(output), mode="w")
    ostream = out.add_stream("h264", rate=rate)
    ostream.width, ostream.height = w, h
    ostream.pix_fmt = "yuv420p"
    ostream.options = {"crf": "24", "preset": "medium"}
    for p in inputs:
        cont = av.open(str(p))
        for frame in cont.decode(video=0):
            if frame.width != w or frame.height != h:
                frame = frame.reformat(width=w, height=h)
            for pkt in ostream.encode(frame):
                out.mux(pkt)
        cont.close()
    for pkt in ostream.encode(None):
        out.mux(pkt)
    out.close()
    print(f"  PyAV 拼接完成: {output}")
    return True


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="按顺序合并多幕白板动画 MP4")
    p.add_argument("--inputs", nargs="+", required=True, help="按播放顺序的 MP4 列表")
    p.add_argument("--output", required=True, help="合并输出路径")
    args = p.parse_args(argv)

    inputs = [Path(x) for x in args.inputs]
    missing = [str(x) for x in inputs if not x.exists()]
    if missing:
        print(f"[err] 缺少输入文件: {', '.join(missing)}", file=sys.stderr)
        return 1
    output = Path(args.output)
    if output.resolve() in {p.resolve() for p in inputs}:
        print('Lỗi: Tệp đầu ra phải khác tệp đầu vào.', file=sys.stderr)
        return 1
    output.parent.mkdir(parents=True, exist_ok=True)

    if _ffmpeg_concat_copy(inputs, output) or _pyav_concat(inputs, output):
        print(f"OUTPUT={output.resolve()}")
        return 0
    print("[err] 合并失败：系统无 ffmpeg 且 PyAV 不可用", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
