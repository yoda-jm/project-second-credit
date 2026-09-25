#!/usr/bin/env python3
"""Assembles the construction movie from captures/movie/<NNN-commit>/ into captures/construction.mp4.

Each step gets a caption card (step number, date, commit subject), then its frames, each held briefly with a
slow zoom. Needs ffmpeg. Usage: python3 tools/make_movie.py [--seconds-per-frame 1.2] [--out file.mp4]
The frames come from tools/movie_shot.sh; to rebuild them at full quality, replay the milestones on the GPU.
"""
import argparse, glob, os, subprocess, tempfile, textwrap

ap = argparse.ArgumentParser()
ap.add_argument("--seconds-per-frame", type=float, default=1.2)
ap.add_argument("--out", default="captures/construction.mp4")
a = ap.parse_args()
root = os.path.join(os.path.dirname(__file__), "..")
steps = sorted(d for d in glob.glob(os.path.join(root, "captures/movie/*/")))
font = subprocess.run(["fc-match", "-f", "%{file}", "sans:bold"], capture_output=True, text=True).stdout.strip()
W, H, FPS = 1280, 720, 30


def esc(s):
    return s.replace("\\", "\\\\").replace(":", "\\:").replace("'", "’").replace("%", "\\%")


with tempfile.TemporaryDirectory() as tmp:
    segs = []
    for n, step in enumerate(steps, 1):
        frames = sorted(glob.glob(os.path.join(step, "*.png")))
        if not frames:
            continue
        info = open(os.path.join(step, "commit.txt")).read().splitlines() if os.path.exists(
            os.path.join(step, "commit.txt")) else ["", os.path.basename(step.rstrip("/"))]
        date = info[0].split(" ")[1] if info[0] else ""
        subject = info[1] if len(info) > 1 else info[0]
        lines = textwrap.wrap(subject, 44)[:3]
        card = os.path.join(tmp, f"{n:03d}-card.mp4")
        draw = [f"drawtext=fontfile={font}:text='STEP {n}':fontcolor=0xffd35a:fontsize=40:x=(w-tw)/2:y=h/2-140",
                f"drawtext=fontfile={font}:text='{esc(date)}':fontcolor=0x9aa3b5:fontsize=26:x=(w-tw)/2:y=h/2-80"]
        for i, l in enumerate(lines):
            draw.append(f"drawtext=fontfile={font}:text='{esc(l)}':fontcolor=white:fontsize=38:x=(w-tw)/2:y=h/2-10+{i * 52}")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"color=c=0x07060b:s={W}x{H}:d=2.2:r={FPS}",
                        "-vf", ",".join(draw) + ",fade=in:0:8,fade=out:st=1.9:d=0.3", "-pix_fmt", "yuv420p", card],
                       check=True)
        segs.append(card)
        for i, f in enumerate(frames):
            seg = os.path.join(tmp, f"{n:03d}-{i:03d}.mp4")
            d = a.seconds_per_frame
            nfr = int(d * FPS)
            vf = (f"scale={W * 2}:{H * 2}:force_original_aspect_ratio=decrease,pad={W * 2}:{H * 2}:(ow-iw)/2:(oh-ih)/2,"
                  f"zoompan=z='1+0.04*on/{nfr}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={nfr}:s={W}x{H}:fps={FPS},"
                  f"fade=in:0:5,fade=out:{nfr - 5}:5")
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-i", f, "-t", str(d), "-vf", vf,
                            "-pix_fmt", "yuv420p", seg], check=True)
            segs.append(seg)
    lst = os.path.join(tmp, "list.txt")
    with open(lst, "w") as fh:
        fh.writelines(f"file '{s}'\n" for s in segs)
    out = os.path.join(root, a.out)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c:v", "libx264", "-crf", "20",
                    "-pix_fmt", "yuv420p", "-movflags", "+faststart", out], check=True)
    print(f"wrote {os.path.normpath(out)}: {len(steps)} steps, {len(segs)} segments")
