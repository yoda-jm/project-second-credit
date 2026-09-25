#!/usr/bin/env python3
"""Assembles a game's construction movie from captures/movie/<game>/<NNN-commit>/ into
captures/<game>-construction.mp4.

Each step gets a caption card (step number, date, commit subject), then its clip (clip.avi from
tools/movie_clip.sh, with the game's audio) or, for older steps, its still frames with a slow zoom (silent).
Needs ffmpeg. Usage: python3 tools/make_movie.py <game> [--seconds-per-frame 1.2]
"""
import argparse, glob, os, subprocess, tempfile, textwrap

ap = argparse.ArgumentParser()
ap.add_argument("game")
ap.add_argument("--seconds-per-frame", type=float, default=1.2)
a = ap.parse_args()
root = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
steps = sorted(glob.glob(os.path.join(root, "captures/movie", a.game, "*/")))
font = subprocess.run(["fc-match", "-f", "%{file}", "sans:bold"], capture_output=True, text=True).stdout.strip()
W, H, FPS = 1280, 720, 30
ENC = ["-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-r", str(FPS), "-c:a", "aac", "-ar", "48000", "-ac", "2"]
SILENCE = ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo"]


def esc(s):
    return s.replace("\\", "\\\\").replace(":", "\\:").replace("'", "’").replace("%", "\\%")


def ff(*args):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args], check=True)


with tempfile.TemporaryDirectory() as tmp:
    segs = []
    title = os.path.join(tmp, "000-title.mp4")
    ff("-f", "lavfi", "-i", f"color=c=0x07060b:s={W}x{H}:d=3:r={FPS}", *SILENCE, "-t", "3",
       "-vf", f"drawtext=fontfile={font}:text='{esc(a.game.upper())}':fontcolor=0xffd35a:fontsize=72:x=(w-tw)/2:y=h/2-70,"
              f"drawtext=fontfile={font}:text='how it was built, step by step':fontcolor=white:fontsize=34:x=(w-tw)/2:y=h/2+30,"
              "fade=in:0:10,fade=out:st=2.6:d=0.4", *ENC, title)
    segs.append(title)
    for n, step in enumerate(steps, 1):
        info_path = os.path.join(step, "commit.txt")
        info = open(info_path).read().splitlines() if os.path.exists(info_path) else ["", os.path.basename(step.rstrip("/"))]
        date = info[0].split(" ")[1] if info[0] else ""
        subject = info[1] if len(info) > 1 else info[0]
        card = os.path.join(tmp, f"{n:03d}-card.mp4")
        draw = [f"drawtext=fontfile={font}:text='STEP {n}':fontcolor=0xffd35a:fontsize=40:x=(w-tw)/2:y=h/2-140",
                f"drawtext=fontfile={font}:text='{esc(date)}':fontcolor=0x9aa3b5:fontsize=26:x=(w-tw)/2:y=h/2-80"]
        for i, line in enumerate(textwrap.wrap(subject, 44)[:3]):
            draw.append(f"drawtext=fontfile={font}:text='{esc(line)}':fontcolor=white:fontsize=38:x=(w-tw)/2:y=h/2-10+{i * 52}")
        ff("-f", "lavfi", "-i", f"color=c=0x07060b:s={W}x{H}:d=2.4:r={FPS}", *SILENCE, "-t", "2.4",
           "-vf", ",".join(draw) + ",fade=in:0:8,fade=out:st=2.1:d=0.3", *ENC, card)
        segs.append(card)
        clip = os.path.join(step, "clip.avi")
        if os.path.exists(clip):
            seg = os.path.join(tmp, f"{n:03d}-clip.mp4")
            ff("-i", clip, "-vf", f"scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2,"
                                  "fade=in:0:8", "-af", "afade=in:0:d=0.3", *ENC, seg)
            segs.append(seg)
            continue
        for i, f in enumerate(sorted(glob.glob(os.path.join(step, "*.png")))):
            seg = os.path.join(tmp, f"{n:03d}-{i:03d}.mp4")
            d = a.seconds_per_frame
            nfr = int(d * FPS)
            vf = (f"scale={W * 2}:{H * 2}:force_original_aspect_ratio=decrease,pad={W * 2}:{H * 2}:(ow-iw)/2:(oh-ih)/2,"
                  f"zoompan=z='1+0.04*on/{nfr}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={nfr}:s={W}x{H}:fps={FPS},"
                  f"fade=in:0:5,fade=out:{nfr - 5}:5")
            ff("-loop", "1", "-i", f, *SILENCE, "-t", str(d), "-vf", vf, *ENC, seg)
            segs.append(seg)
    lst = os.path.join(tmp, "list.txt")
    with open(lst, "w") as fh:
        fh.writelines(f"file '{s}'\n" for s in segs)
    out = os.path.join(root, "captures", f"{a.game}-construction.mp4")
    ff("-f", "concat", "-safe", "0", "-i", lst, *ENC, "-movflags", "+faststart", out)
    print(f"wrote {out}: {len(steps)} steps")
