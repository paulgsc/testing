#!/usr/bin/env python3
"""The size and media guard: what this repository may hold, and how much.

This repository is small, versioned JSON that some-ui's stages read. Every
file has a byte budget by its kind, media is refused outright (by extension
and by its first bytes, so a renamed file is caught), and the whole tree has
a budget so growth is seen before it matters.

    python3 scripts/guard.py              # every tracked file (git ls-files)
    python3 scripts/guard.py --staged     # what `git commit` would record
    python3 scripts/guard.py --ref <ref>  # the tree at a commit, e.g. HEAD
    python3 scripts/guard.py --self-test  # the guard's own tests

Run it before every push. It prints every problem and exits 1 on any, 0
otherwise; warnings (the tree past WARN_AT of its budget) never fail.
Python 3.8+ and git, nothing else.
"""

import hashlib
import json
import subprocess
import sys

KB = 1024
MB = 1024 * KB

# Per-file budgets by kind. Today's largest (2026-11-11): a call week is
# 81 KB and a season, at week 9, 51 KB (about 110 KB at its end).
CAPS = {
    "json": 256 * KB,
    "text": 64 * KB,
}
TEXT_EXTENSIONS = {".md", ".txt", ".sh", ".py", ".yml", ".yaml"}
# Files without an extension that are text.
TEXT_NAMES = {".gitignore", ".gitattributes", "LICENSE"}

# The whole tree. Today about 0.2 MB without the legacy frames below.
TOTAL_BUDGET = 4 * MB
WARN_AT = 0.75

# Media and binaries, refused whatever their size.
MEDIA_EXTENSIONS = {
    # images
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".avif", ".bmp", ".tif",
    ".tiff", ".ico", ".heic", ".heif", ".svg", ".psd",
    # audio
    ".mp3", ".wav", ".ogg", ".oga", ".opus", ".flac", ".m4a", ".aac",
    ".weba", ".mid", ".midi",
    # video
    ".mp4", ".m4v", ".mov", ".webm", ".mkv", ".avi", ".wmv", ".flv",
    # archives
    ".zip", ".gz", ".tgz", ".tar", ".bz2", ".xz", ".zst", ".7z", ".rar",
    # documents and binaries
    ".pdf", ".exe", ".dll", ".so", ".dylib", ".bin", ".wasm", ".class",
    ".jar", ".o", ".a", ".woff", ".woff2", ".ttf", ".otf", ".sqlite",
    ".db",
}


def _riff(kind):
    return lambda b: b[:4] == b"RIFF" and b[8:12] == kind


MAGIC = [
    ("PNG image", lambda b: b.startswith(b"\x89PNG\r\n\x1a\n")),
    ("JPEG image", lambda b: b.startswith(b"\xff\xd8\xff")),
    ("GIF image", lambda b: b[:6] in (b"GIF87a", b"GIF89a")),
    ("WebP image", _riff(b"WEBP")),
    ("WAV audio", _riff(b"WAVE")),
    ("AVI video", _riff(b"AVI ")),
    ("BMP image", lambda b: b.startswith(b"BM") and len(b) > 14
        and b[6:10] == b"\x00\x00\x00\x00"),
    ("TIFF image", lambda b: b[:4] in (b"II*\x00", b"MM\x00*")),
    ("ICO image", lambda b: b.startswith(b"\x00\x00\x01\x00")),
    ("MP3 audio", lambda b: b.startswith(b"ID3")
        or (len(b) > 1 and b[0] == 0xFF and (b[1] & 0xE0) == 0xE0)),
    ("Ogg media", lambda b: b.startswith(b"OggS")),
    ("FLAC audio", lambda b: b.startswith(b"fLaC")),
    ("MP4/MOV/HEIC/AVIF media", lambda b: b[4:8] == b"ftyp"),
    ("Matroska/WebM video", lambda b: b.startswith(b"\x1a\x45\xdf\xa3")),
    ("PDF document", lambda b: b.startswith(b"%PDF")),
    ("zip archive", lambda b: b[:4] in (b"PK\x03\x04", b"PK\x05\x06")),
    ("gzip archive", lambda b: b.startswith(b"\x1f\x8b")),
    ("bzip2 archive", lambda b: b.startswith(b"BZh")
        and b[3:4].isdigit()),
    ("xz archive", lambda b: b.startswith(b"\xfd7zXZ\x00")),
    ("zstd archive", lambda b: b.startswith(b"\x28\xb5\x2f\xfd")),
    ("7z archive", lambda b: b.startswith(b"7z\xbc\xaf\x27\x1c")),
    ("RAR archive", lambda b: b.startswith(b"Rar!\x1a\x07")),
    ("ELF binary", lambda b: b.startswith(b"\x7fELF")),
    ("Mach-O binary", lambda b: b[:4] in (
        b"\xcf\xfa\xed\xfe", b"\xce\xfa\xed\xfe", b"\xca\xfe\xba\xbe")),
    ("Windows binary", lambda b: b.startswith(b"MZ")),
    ("WebAssembly", lambda b: b.startswith(b"\x00asm")),
    ("SQLite database", lambda b: b.startswith(b"SQLite format 3\x00")),
    ("font", lambda b: b[:4] in (b"wOFF", b"wOF2", b"OTTO",
                                  b"\x00\x01\x00\x00")),
]

# The only media this repository holds, and only until the owner says
# where it goes: the clips' frames as they were on 2026-11-11, before the
# guard. Each is held to its exact bytes. No file joins this list; one
# leaves it when its frame has a new home (TESTING-GUARD, Nov 11).
LEGACY_MEDIA = {
    "clips/rust-essay-recorded/after/01-intro.png":
        "ef959543984d9fb4aa0390919c74a5b399e5703b5ee041c8aeaa74dad31a7847",
    "clips/rust-essay-recorded/after/02-answer.png":
        "d4a2b3d3b64d810fceb39f60dc0e35b9e3db5c89f6a6e40e9a95064fb3c6a55d",
    "clips/rust-essay-recorded/after/03-beside.png":
        "b71799b50440344e8e42133c1bb03481b77b12cae0a9284c0f9e69e71b19f730",
    "clips/studio-release-promo/after/01-templates.png":
        "bae1cfbaff2dcbfdc641e0cbc3ba69a95f3c9a265098c1e1c5e8fc1bb7d2475c",
    "clips/studio-release-promo/after/02-release-promo.png":
        "8c5b1ec2a8cd537beb3a97294aa66966ae97c31ed5478f69df66b7bfb5552692",
    "clips/studio-release-promo/before/01-templates.png":
        "4b09b718b7140852cb85a2ea35b3207a10293b6a2a769528b874704f87808701",
}


def extension(path):
    name = path.rsplit("/", 1)[-1]
    if "." not in name.lstrip("."):
        return ""
    return "." + name.rsplit(".", 1)[-1].lower()


def sniff(data):
    """The media kind its first bytes say, or None."""
    head = data[:64]
    for kind, test in MAGIC:
        if test(head):
            return kind
    return None


def kind_of(path):
    """json, text, media, or unknown, by the name alone."""
    ext = extension(path)
    if ext == ".json":
        return "json"
    if ext in TEXT_EXTENSIONS or path.rsplit("/", 1)[-1] in TEXT_NAMES:
        return "text"
    if ext in MEDIA_EXTENSIONS:
        return "media"
    return "unknown"


def check_file(path, data, legacy=None):
    """Every reason one file can't be kept here."""
    legacy = LEGACY_MEDIA if legacy is None else legacy
    size = len(data)
    kind = kind_of(path)
    magic = sniff(data)
    if path in legacy:
        digest = hashlib.sha256(data).hexdigest()
        if digest != legacy[path]:
            return ["%s: legacy media changed (sha256 %s, held to %s); "
                    "no media may be added or edited" %
                    (path, digest, legacy[path])]
        return []
    if kind == "media" or magic:
        what = magic or "media by its extension %s" % extension(path)
        return ["%s: %s (%s bytes); media isn't kept here, see the README's "
                "rule" % (path, what, size)]
    if kind == "unknown":
        return ["%s: unknown kind %r; this repository keeps JSON and text "
                "(%s), and a new kind is a change to scripts/guard.py" %
                (path, extension(path) or "(no extension)",
                 " ".join(sorted(TEXT_EXTENSIONS | {".json"})))]
    problems = []
    if size > CAPS[kind]:
        problems.append("%s: %d bytes, over the %s cap of %d" %
                        (path, size, kind, CAPS[kind]))
    if b"\x00" in data:
        problems.append("%s: has NUL bytes, so it is binary, not %s" %
                        (path, kind))
        return problems
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        problems.append("%s: isn't UTF-8 text" % path)
        return problems
    if kind == "json":
        try:
            json.loads(text)
        except ValueError as e:
            problems.append("%s: isn't JSON (%s)" % (path, e))
    return problems


def check_tree(files, legacy=None, budget=TOTAL_BUDGET):
    """(problems, warnings, total) for {path: bytes}."""
    problems, warnings = [], []
    total = 0
    for path in sorted(files):
        data = files[path]
        total += len(data)
        problems.extend(check_file(path, data, legacy))
    if total > budget:
        problems.append("the tree is %d bytes, over its budget of %d" %
                        (total, budget))
    elif total > budget * WARN_AT:
        warnings.append("the tree is %d bytes, %d%% of its budget of %d" %
                        (total, 100 * total // budget, budget))
    return problems, warnings, total


def git(*args):
    return subprocess.run(("git",) + args, check=True,
                          stdout=subprocess.PIPE).stdout


def entries(spec):
    """{path: object id} for regular files: of the index, or of a tree."""
    out = {}
    if spec is None:
        raw = git("ls-files", "-s", "-z")
        for rec in raw.split(b"\x00"):
            if not rec:
                continue
            meta, path = rec.split(b"\t", 1)
            mode, oid, _stage = meta.split(b" ")
            out[path.decode()] = (mode.decode(), oid.decode())
    else:
        raw = git("ls-tree", "-r", "-z", spec)
        for rec in raw.split(b"\x00"):
            if not rec:
                continue
            meta, path = rec.split(b"\t", 1)
            mode, _type, oid = meta.split(b" ")
            out[path.decode()] = (mode.decode(), oid.decode())
    return out


def blobs(oids):
    """The bytes of each blob, in one `git cat-file --batch`."""
    if not oids:
        return {}
    unique = sorted(set(oids))
    raw = subprocess.run(["git", "cat-file", "--batch"], check=True,
                         input=("\n".join(unique) + "\n").encode(),
                         stdout=subprocess.PIPE).stdout
    out, at = {}, 0
    for oid in unique:
        nl = raw.index(b"\n", at)
        size = int(raw[at:nl].split(b" ")[2])
        out[oid] = raw[nl + 1:nl + 1 + size]
        at = nl + 1 + size + 1
    return out


def read_tree(spec, worktree):
    """{path: bytes}, and problems with entries that aren't plain files."""
    listed = entries(spec)
    problems = []
    files = {}
    for path, (mode, _oid) in sorted(listed.items()):
        if mode == "160000":
            problems.append("%s: a submodule isn't kept here" % path)
        elif mode == "120000":
            problems.append("%s: a symlink isn't kept here" % path)
    plain = {p: oid for p, (m, oid) in listed.items()
             if m not in ("160000", "120000")}
    if worktree:
        for path in plain:
            with open(path, "rb") as f:
                files[path] = f.read()
    else:
        data = blobs(list(plain.values()))
        for path, oid in plain.items():
            files[path] = data[oid]
    return files, problems


def report(files, extra):
    problems, warnings, total = check_tree(files)
    problems = extra + problems
    by_dir = {}
    for path, data in files.items():
        top = path.split("/", 1)[0] if "/" in path else "(root)"
        by_dir[top] = by_dir.get(top, 0) + len(data)
    print("guard: %d files, %d bytes of %d (%d%%)" %
          (len(files), total, TOTAL_BUDGET, 100 * total // TOTAL_BUDGET))
    for top, size in sorted(by_dir.items(), key=lambda kv: -kv[1]):
        print("  %-16s %9d" % (top, size))
    for w in warnings:
        print("warning: " + w)
    for p in problems:
        print("problem: " + p)
    print("guard: %s" % ("ready" if not problems else
                         "%d problem(s), not ready" % len(problems)))
    return 1 if problems else 0


# -- self-test -------------------------------------------------------------

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 40


def self_test():
    cases = []

    def case(name, got, want):
        cases.append((name, got == want, got, want))

    ok = lambda path, data, legacy={}: check_file(path, data, legacy)
    bad = lambda path, data, legacy={}: bool(check_file(path, data, legacy))

    case("a small JSON file passes", ok("a/b.json", b'{"x": 1}'), [])
    case("JSON that doesn't parse fails", bad("a.json", b"{x"), True)
    case("JSON at its cap passes",
         ok("a.json", b'"' + b"x" * (CAPS["json"] - 2) + b'"'), [])
    case("JSON over its cap fails",
         bad("a.json", b'"' + b"x" * (CAPS["json"] - 1) + b'"'), True)
    case("markdown passes", ok("README.md", b"# hi\n"), [])
    case("text over its cap fails",
         bad("notes.md", b"x" * (CAPS["text"] + 1)), True)
    case("a PNG fails by extension", bad("c/a.png", b"not really"), True)
    case("a PNG named .json fails by its bytes", bad("c/a.json", PNG), True)
    case("a JPEG named .md fails", bad("x.md", b"\xff\xd8\xff\xe0abc"), True)
    case("an MP4 named .json fails",
         bad("x.json", b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 8), True)
    case("a WAV fails", bad("x.txt", b"RIFF\x00\x00\x00\x00WAVEfmt "), True)
    case("an MP3 fails", bad("x.txt", b"ID3\x03\x00"), True)
    case("a zip fails", bad("x.yml", b"PK\x03\x04rest"), True)
    case("a gzip fails", bad("x.json", b"\x1f\x8b\x08\x00"), True)
    case("an ELF fails", bad("tool", b"\x7fELF\x02\x01"), True)
    case("a PDF fails", bad("x.md", b"%PDF-1.7\n"), True)
    case("a WebM fails", bad("x.webm", b"\x1a\x45\xdf\xa3\x01"), True)
    case("an SVG fails by extension", bad("x.svg", b"<svg/>"), True)
    case("an unknown kind fails", bad("x.csv", b"a,b\n"), True)
    case("a file with no extension fails", bad("Makefile", b"all:\n"), True)
    case("NUL bytes in text fail", bad("x.txt", b"a\x00b"), True)
    case("bytes that aren't UTF-8 fail", bad("x.md", b"\xc3\x28"), True)
    digest = hashlib.sha256(PNG).hexdigest()
    case("legacy media held to its bytes passes",
         ok("c/a.png", PNG, {"c/a.png": digest}), [])
    case("legacy media changed fails",
         bad("c/a.png", PNG + b"x", {"c/a.png": digest}), True)
    case("media at another path than its legacy entry fails",
         bad("c/b.png", PNG, {"c/a.png": digest}), True)
    p, w, _ = check_tree({"a.json": b"1" * 80}, {}, budget=100)
    case("a tree past WARN_AT warns, not fails", (p, len(w)), ([], 1))
    p, w, _ = check_tree({"a.json": b"1" * 101}, {}, budget=100)
    case("a tree over its budget fails", len(p), 1)
    case("every legacy entry is media",
         all(kind_of(k) == "media" for k in LEGACY_MEDIA), True)
    case("every legacy digest is a SHA-256",
         all(len(v) == 64 and int(v, 16) >= 0 for v in LEGACY_MEDIA.values()),
         True)

    failed = [c for c in cases if not c[1]]
    for name, passed, got, want in cases:
        print("%s %s" % ("ok  " if passed else "FAIL", name))
        if not passed:
            print("     got %r, want %r" % (got, want))
    print("self-test: %d of %d passed" % (len(cases) - len(failed),
                                         len(cases)))
    return 1 if failed else 0


def main(argv):
    if argv == ["--self-test"]:
        return self_test()
    if argv == []:
        files, extra = read_tree(None, worktree=True)
    elif argv == ["--staged"]:
        files, extra = read_tree(None, worktree=False)
    elif len(argv) == 2 and argv[0] == "--ref":
        files, extra = read_tree(argv[1], worktree=False)
    else:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    return report(files, extra)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
