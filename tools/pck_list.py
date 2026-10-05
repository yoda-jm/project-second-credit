#!/usr/bin/env python3
"""Lists the files inside a Godot 4 .pck (formats 2 and 3), with sizes. Usage: tools/pck_list.py file.pck [--sum]
--sum prints only the total per top folder (games/<id>, core, .godot/...)."""
import struct
import sys


def entries(path):
    with open(path, "rb") as f:
        data = f.read()
    if data.startswith(b"GDPC"):
        start = 0
    elif data[-4:] == b"GDPC":  # embedded in an executable: the pack, its size, then the magic again at the very end
        start = len(data) - 12 - struct.unpack_from("<Q", data, len(data) - 12)[0]
    else:
        sys.exit(f"{path}: no Godot pack found")
    o = start + 4
    ver, major, minor, patch = struct.unpack_from("<4I", data, o)
    o += 16
    flags, base = struct.unpack_from("<IQ", data, o)
    o += 12
    if ver >= 3:
        dir_off = struct.unpack_from("<Q", data, o)[0]
        o = start + dir_off
    else:
        o += 16 * 4
    count = struct.unpack_from("<I", data, o)[0]
    o += 4
    out = []
    for _ in range(count):
        n = struct.unpack_from("<I", data, o)[0]
        o += 4
        name = data[o:o + n].rstrip(b"\0").decode()
        o += n
        off, size = struct.unpack_from("<QQ", data, o)
        o += 16 + 16 + 4  # md5, flags
        out.append((name, size))
    return (major, minor, patch), out


def main():
    ver, files = entries(sys.argv[1])
    if "--sum" in sys.argv:
        tot = {}
        for name, size in files:
            parts = name.replace("res://", "").split("/")
            key = "/".join(parts[:2]) if parts[0] in ("games", ".godot") else parts[0]
            tot[key] = tot.get(key, 0) + size
        for k, v in sorted(tot.items(), key=lambda kv: -kv[1]):
            print(f"{v / 1e6:9.2f} MB  {k}")
    else:
        for name, size in files:
            print(f"{size:10d}  {name}")
    print(f"Godot {ver[0]}.{ver[1]}.{ver[2]}, {len(files)} files, {sum(s for _, s in files) / 1e6:.1f} MB", file=sys.stderr)


if __name__ == "__main__":
    main()
