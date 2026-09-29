#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: LGPL-2.1-or-later
"""Put the Wheelly driver into a checkout of indilib/indi, and its
documentation into a checkout of indilib/drivers-docs.

    python3 to_indi.py INDI_TREE
    python3 to_indi.py --docs DRIVERS_DOCS_TREE

Why a script and not a copy by hand. Once the driver is in INDI, INDI's tree
holds a copy of it that this repository's checks cannot see. Every change
after the first pull request is the same handful of edits - seven files, a
CMake block, a drivers.xml entry, the documentation - and a handful of edits
done by hand is where a file gets forgotten, or where the version in
drivers.xml stays behind the driver's. This repository stays the source; the
copy in INDI is always produced from it, never edited there.

What it does, in INDI_TREE:
  - drivers/filter_wheel/wheelly/     the driver's sources (DRIVER_FILES);
  - drivers/filter_wheel/CMakeLists.txt  the block of CMakeLists-indi.txt,
                                      appended, or replaced if already there;
  - drivers.xml                       the entry of drivers-xml-entry.xml, at
                                      the end of the Filter Wheels group, or
                                      replaced if already there.

With --docs, in DRIVERS_DOCS_TREE (INDI's maintainers keep driver pages
there, not in INDI's tree - asked on the first pull request):
  - src/content/docs/filter-wheels/generic/wheelly/
        wheelly.md, wheelly.yaml (version filled in), the 300x300 thumbnail
        wheelly.webp, and images/X.webp for every ./images/X.webp the page
        links, converted from the panel guide's render docs/driver/img/en-X.png
        so the screenshots are not kept twice.

It can be run again on the same tree: the second run replaces, it does not
add a second copy (a script that works only on a fresh clone breaks on the
second release, which is the one that matters). The version in the CMake
block and in drivers.xml is read from this folder's CMakeLists.txt.

Python only, no dependency: it runs with the system python.
"""
import pathlib
import re
import shutil
import sys

HERE = pathlib.Path(__file__).resolve().parent
DRIVER = HERE.parent
GUIDE_IMG = DRIVER.parent.parent / "docs" / "driver" / "img"

# What goes into INDI, and nothing else: the driver is the same file here and
# there, English only as INDI's drivers are. Not CMakeLists.txt nor indi_wheelly.xml.cmake: INDI builds and lists its
# drivers its own way (the block and the entry below). Not driver_bench.py
# nor doc/: they need the simulator in firmware/, which stays here.
DRIVER_FILES = [
    "wheelly.cpp", "wheelly.h",
    "wheelly_protocol.h",
    "wheelly_config.h.cmake",
]

BANNER = "# ############### Wheelly Filter Wheel ################"
GROUP = '<devGroup group="Filter Wheels">'


def executable():
    """The executable's name, from this folder's CMakeLists.txt."""
    text = (DRIVER / "CMakeLists.txt").read_text(encoding="utf-8")
    m = re.search(r"set\(WHEELLY_EXECUTABLE\s+(\w+)\)", text)
    if not m:
        sys.exit("CMakeLists.txt: WHEELLY_EXECUTABLE not found")
    return m.group(1)


def version():
    """(major, minor) from this folder's CMakeLists.txt: the one place the
    driver's version is written."""
    text = (DRIVER / "CMakeLists.txt").read_text(encoding="utf-8")
    major = re.search(r"set\(WHEELLY_VERSION_MAJOR\s+(\d+)\)", text)
    minor = re.search(r"set\(WHEELLY_VERSION_MINOR\s+(\d+)\)", text)
    if not (major and minor):
        sys.exit("CMakeLists.txt: WHEELLY_VERSION_MAJOR/MINOR not found")
    return major.group(1), minor.group(1)


def cmake_block(major, minor):
    """The part of CMakeLists-indi.txt from the banner on, filled in. The
    comment above the banner explains the block to this repository and stays
    here."""
    text = (HERE / "CMakeLists-indi.txt").read_text(encoding="utf-8")
    start = text.index(BANNER)
    block = text[start:]
    block = block.replace("@WHEELLY_VERSION_MAJOR@", major)
    block = block.replace("@WHEELLY_VERSION_MINOR@", minor)
    block = block.replace("@WHEELLY_EXECUTABLE@", executable())
    if "@" in block:
        sys.exit("CMakeLists-indi.txt: a placeholder was left unfilled")
    return block.rstrip("\n") + "\n"


def xml_entry(major, minor):
    """The <device> of drivers-xml-entry.xml, filled in, without the file's
    own comments."""
    text = (HERE / "drivers-xml-entry.xml").read_text(encoding="utf-8")
    m = re.search(r"^([ \t]*<device .*?</device>)", text, re.S | re.M)
    if m is None:
        sys.exit("drivers-xml-entry.xml: no <device> entry found")
    entry = m.group(1).replace("@WHEELLY_VERSION@", f"{major}.{minor}")
    entry = entry.replace("@WHEELLY_EXECUTABLE@", executable())
    if "@" in entry:
        sys.exit("drivers-xml-entry.xml: a placeholder was left unfilled")
    return entry


def put_cmake(path, block):
    text = path.read_text(encoding="utf-8")
    if BANNER in text:
        # ours runs from the banner to the next banner, or to the end
        start = text.index(BANNER)
        nxt = text.find("\n# ###############", start + len(BANNER))
        end = len(text) if nxt < 0 else nxt + 1
        text = text[:start] + block + ("\n" if nxt >= 0 else "") + text[end:]
        how = "replaced"
    else:
        text = text.rstrip("\n") + "\n\n" + block
        how = "appended"
    path.write_text(text, encoding="utf-8")
    return how


def put_xml(path, entry):
    text = path.read_text(encoding="utf-8")
    ours = re.compile(r'[ \t]*<device label="Wheelly".*?</device>\n', re.S)
    if ours.search(text):
        text = ours.sub(lambda _: entry + "\n", text, count=1)
        how = "replaced"
    else:
        start = text.index(GROUP)
        close = text.index("</devGroup>", start)
        line_start = text.rfind("\n", 0, close) + 1
        text = text[:line_start] + entry + "\n" + text[line_start:]
        how = "added"
    path.write_text(text, encoding="utf-8")
    return how


def put_docs(tree, major, minor):
    """The driver's page in drivers-docs. Pillow converts the screenshots to
    WebP, the only thing here that is not the standard library: imported
    here, so the INDI half runs without it."""
    from PIL import Image

    dest = tree / "src" / "content" / "docs" / "filter-wheels" / "generic" / "wheelly"
    if dest.exists():
        shutil.rmtree(dest)
    (dest / "images").mkdir(parents=True)
    source = HERE / "doc"
    page = (source / "wheelly.md").read_text(encoding="utf-8")
    (dest / "wheelly.md").write_text(page, encoding="utf-8")
    meta = (source / "wheelly.yaml").read_text(encoding="utf-8")
    meta = meta.replace("@WHEELLY_VERSION@", f"{major}.{minor}")
    meta = meta.replace("@WHEELLY_EXECUTABLE@", executable())
    if "@" in meta:
        sys.exit("wheelly.yaml: a placeholder was left unfilled")
    (dest / "wheelly.yaml").write_text(meta, encoding="utf-8")
    shutil.copy2(source / "wheelly.webp", dest / "wheelly.webp")
    names = re.findall(r"\]\(\./images/([^)\s]+)\.webp\)", page)
    for name in names:
        png = GUIDE_IMG / f"en-{name}.png"
        if not png.is_file():
            sys.exit(f"wheelly.md uses images/{name}.webp, {png} not found")
        with Image.open(png) as im:
            if im.width > 1200:     # drivers-docs: no wider than 1200 px
                im = im.resize((1200, round(im.height * 1200 / im.width)))
            im.save(dest / "images" / f"{name}.webp", quality=90)
    return dest, names


def main():
    args = sys.argv[1:]
    docs = args[:1] == ["--docs"]
    if docs:
        args = args[1:]
    if len(args) != 1:
        sys.exit(__doc__)
    tree = pathlib.Path(args[0]).expanduser().resolve()
    major, minor = version()

    if docs:
        if not (tree / "src" / "content" / "docs" / "filter-wheels").is_dir():
            sys.exit(f"{tree} does not look like a checkout of indilib/drivers-docs")
        dest, names = put_docs(tree, major, minor)
        print(f"{dest.relative_to(tree)}/: wheelly.md, wheelly.yaml "
              f"(version {major}.{minor}), thumbnail and {len(names)} pictures")
        return

    wheels = tree / "drivers" / "filter_wheel"
    if not (wheels / "CMakeLists.txt").is_file() or not (tree / "drivers.xml").is_file():
        sys.exit(f"{tree} does not look like a checkout of indilib/indi")

    target = wheels / "wheelly"
    if target.exists():
        shutil.rmtree(target)
    target.mkdir()
    for name in DRIVER_FILES:
        shutil.copy2(DRIVER / name, target / name)
    print(f"drivers/filter_wheel/wheelly/: {len(DRIVER_FILES)} files")

    how = put_cmake(wheels / "CMakeLists.txt", cmake_block(major, minor))
    print(f"drivers/filter_wheel/CMakeLists.txt: block {how}")
    how = put_xml(tree / "drivers.xml", xml_entry(major, minor))
    print(f"drivers.xml: entry {how}, version {major}.{minor}")


if __name__ == "__main__":
    main()
