"""Build the static site from the Russian source page.

    python tools/build.py path/to/source-ru.html

Writes ru/index.html and index.html (Russian), en/index.html (English, via tools/en.txt) and a copy of
the source to src/ru.html. Fails if a translation pair no longer matches the source or
if any Cyrillic text is left untranslated in the English page.
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CYR = re.compile(r"[А-Яа-яЁё]")


def read(path):
    with io.open(path, encoding="utf-8") as f:
        return f.read()


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with io.open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def wrap(body, lang):
    head = ('<!doctype html>\n<html lang="%s">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n') % lang
    return head + body + "\n</html>\n"


def load_pairs(path):
    pairs, ru = [], None
    for n, line in enumerate(read(path).splitlines(), 1):
        if line.startswith(">>> "):
            ru = line[4:]
        elif line.startswith("<<< "):
            if ru is None:
                sys.exit("en.txt:%d: English line without a Russian line" % n)
            pairs.append((ru, line[4:], n))
            ru = None
    return pairs


def translate(src, pairs):
    missing = [(n, ru) for ru, _, n in pairs if ru not in src]
    if missing:
        for n, ru in missing:
            print("en.txt:%d no longer matches the source: %s" % (n, ru[:80]))
        sys.exit(1)
    out = src
    for ru, en, _ in sorted(pairs, key=lambda p: -len(p[0])):
        out = out.replace(ru, en)
    # the language switch and hint banner are meant to stay in Russian on the English page
    left = [l for l in out.splitlines() if CYR.search(l) and 'lang="ru"' not in l]
    if left:
        print("Untranslated lines in the English page:")
        for l in left:
            print("  " + l.strip()[:120])
        sys.exit(1)
    return out


def main():
    src_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "src", "ru.html")
    src = read(src_path)
    pairs = load_pairs(os.path.join(ROOT, "tools", "en.txt"))
    # /ru/ is the canonical Russian URL; the site root serves the same page for old links
    write(os.path.join(ROOT, "ru", "index.html"), wrap(src, "ru"))
    write(os.path.join(ROOT, "index.html"), wrap(src, "ru"))
    write(os.path.join(ROOT, "en", "index.html"), wrap(translate(src, pairs), "en"))
    if os.path.abspath(src_path) != os.path.join(ROOT, "src", "ru.html"):
        write(os.path.join(ROOT, "src", "ru.html"), src)
    print("built ru/, index.html and en/ from %d translation pairs" % len(pairs))


if __name__ == "__main__":
    main()
