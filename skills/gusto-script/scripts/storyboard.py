#!/usr/bin/env python3
"""Turn a production's storyboard.json into storyboard images and one page to review them.

    python3 ~/.claude/skills/gusto-script/scripts/storyboard.py check <production>
    python3 ~/.claude/skills/gusto-script/scripts/storyboard.py gen <production> [--dry-run]
    python3 ~/.claude/skills/gusto-script/scripts/storyboard.py gen <production> 03 07 --force
    python3 ~/.claude/skills/gusto-script/scripts/storyboard.py html <production>
    python3 ~/.claude/skills/gusto-script/scripts/storyboard.py models

<production> is a folder name under $GUSTO_HOME/productions/, or a path.

check   validate storyboard.json: every ref and self role exists; count the images to generate.
gen     generate the `gen` frames that have no image yet (or the IDs given; --force redoes them).
        Each one puts Gustavo (from $GUSTO_HOME/self/) into the frame, wearing the outfit in the
        frame's original reference images. The originals are never changed. A redone image's
        old version moves to storyboard/old/. Spends image-API credit: run check first.
html    write storyboard.html: every frame in order with its image, line, on-screen text,
        edit note, and the originals it came from, linked to their source pages.
models  list the image models the API key can use, best first.

The API key is read from GEMINI_API_KEY or OPENAI_API_KEY, else from
$GUSTO_HOME/secrets/gemini_api_key or openai_api_key. Gemini is used when both exist.
--model or GUSTO_IMAGE_MODEL picks the model; otherwise the best one available.
"""
import argparse
import base64
import datetime
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "gusto-research" / "scripts"))
from common import HOME  # noqa: E402

SELF = HOME / "self"
KINDS = ("gen", "self", "ref", "card")
GEMINI = "https://generativelanguage.googleapis.com/v1beta"
OPENAI = "https://api.openai.com/v1"


# --- production and storyboard.json ---------------------------------------------------------

def production_dir(name):
    path = Path(name).expanduser()
    if not path.is_dir():
        path = HOME / "productions" / name
    if not (path / "storyboard.json").exists():
        sys.exit(f"no storyboard.json in {path}")
    return path


def load(prod):
    board = json.loads((prod / "storyboard.json").read_text())
    for frame in board["frames"]:
        frame["id"] = str(frame["id"])
    return board


def self_pack():
    path = SELF / "self.json"
    if not path.exists():
        sys.exit(f"no self pack at {path}: run the skill's § Self pack first")
    return json.loads(path.read_text())


def self_files(pack, roles):
    files = []
    for role in roles:
        names = pack["roles"].get(role)
        if not names:
            raise KeyError(role)
        # One image per role keeps the request small; the first is the best one.
        files.append((role, SELF / names[0]))
    return files


def problems(prod, board, pack):
    found = []
    ids = [f["id"] for f in board["frames"]]
    for dup in {i for i in ids if ids.count(i) > 1}:
        found.append(f"duplicate frame id {dup}")
    for frame in board["frames"]:
        where = f"frame {frame['id']}"
        if frame.get("kind") not in KINDS:
            found.append(f"{where}: kind must be one of {', '.join(KINDS)}")
        for ref in frame.get("refs", []):
            if not (prod / ref).exists():
                found.append(f"{where}: missing ref {ref}")
        if frame.get("kind") == "gen":
            if not frame.get("prompt"):
                found.append(f"{where}: a gen frame needs a prompt")
            if not frame.get("refs"):
                found.append(f"{where}: a gen frame starts from an original in refs/; add one")
        if frame.get("kind") in ("gen", "self"):
            try:
                for _, path in self_files(pack, frame.get("self", ["face", "body", "set"])):
                    if not path.exists():
                        found.append(f"{where}: self image missing: {path}")
            except KeyError as role:
                found.append(f"{where}: unknown self role {role}; known: {', '.join(pack['roles'])}")
        if frame.get("kind") == "ref" and not frame.get("refs"):
            found.append(f"{where}: a ref frame shows an original, so it needs refs")
    return found


def to_generate(prod, board, ids, force):
    frames = [f for f in board["frames"] if f.get("kind") == "gen"]
    if ids:
        frames = [f for f in frames if f["id"] in ids]
    return [f for f in frames if force or not image_path(prod, f).exists()]


def image_path(prod, frame):
    return prod / "storyboard" / f"{frame['id']}.png"


# --- prompt ---------------------------------------------------------------------------------

def inputs_for(prod, frame, pack):
    """(label, path) for every image sent with the frame: Gustavo first, then the originals."""
    labelled = []
    for role, path in self_files(pack, frame.get("self", ["face", "body", "set"])):
        label = {
            "face": "Gustavo's face. Identity reference: keep this exact face.",
            "body": "Gustavo's build and posture. Identity reference only; ignore the clothes.",
        }.get(role, f"The set ('{role}'). Put him in this exact room, same camera angle, lens and light; ignore the clothes of anyone in it.")
        labelled.append((label, path))
    for ref in frame.get("refs", []):
        labelled.append(("Original reference from the research: copy the garments exactly "
                         "(colour, fabric, fit, details). Ignore the person, face and background in it.", prod / ref))
    return labelled


def instruction(board, frame, pack, count):
    return "\n".join([
        f"Storyboard frame {frame['id']} for the YouTube video \"{board.get('title', '')}\" "
        "by Gustavo Ortiz (channel Gusto Clásico).",
        f"Host: {pack.get('description', '')}",
        f"The {count} images above are references, labelled in order.",
        "Show: " + frame["prompt"],
        f"Shot: {frame.get('shot', 'medium shot')}.",
        "Keep Gustavo's face, hair, skin tone, age and build exactly as in the references; "
        "do not beautify, slim or rejuvenate him. Photorealistic, natural warm interior light, "
        "like a frame from his own videos. No text, captions, logos or watermarks.",
    ])


def shrink(path, tmp):
    """A JPEG copy at most 1600 px wide, via macOS sips; the original if sips is missing."""
    if not shutil.which("sips"):
        return path
    out = Path(tmp) / f"{uuid.uuid4().hex}.jpg"
    proc = subprocess.run(["sips", "-s", "format", "jpeg", "-Z", "1600", str(path), "--out", str(out)],
                          capture_output=True)
    return out if proc.returncode == 0 and out.exists() else path


def mime(path):
    return {".png": "image/png", ".webp": "image/webp", ".gif": "image/gif"}.get(path.suffix.lower(), "image/jpeg")


# --- providers ------------------------------------------------------------------------------

def api_key(provider):
    env = {"gemini": "GEMINI_API_KEY", "openai": "OPENAI_API_KEY"}[provider]
    if os.environ.get(env):
        return os.environ[env]
    path = HOME / "secrets" / f"{provider}_api_key"
    return path.read_text().strip() if path.exists() else None


def provider_and_key(choice):
    for provider in ([choice] if choice else ["gemini", "openai"]):
        key = api_key(provider)
        if key:
            return provider, key
    sys.exit("no image API key: save one to $GUSTO_HOME/secrets/gemini_api_key (or openai_api_key), "
             "mode 600. See the skill's § Image API.")


def call(url, headers, body=None, data=None):
    req = urllib.request.Request(url, headers=headers, data=data if data is not None else
                                 (json.dumps(body).encode() if body is not None else None))
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as err:
        detail = err.read().decode("utf-8", "replace")[:800]
        raise RuntimeError(f"HTTP {err.code}: {detail}") from None


def version(name):
    return tuple(int(n) for n in re.findall(r"\d+", name)[:3])


def image_models(provider, key):
    if provider == "gemini":
        data = call(f"{GEMINI}/models?pageSize=1000", {"x-goog-api-key": key})
        names = [m["name"].split("/", 1)[1] for m in data.get("models", [])
                 if "image" in m["name"] and "imagen" not in m["name"]
                 and "generateContent" in m.get("supportedGenerationMethods", [])]
        return sorted(names, key=lambda n: ("pro" in n, version(n), "preview" not in n), reverse=True)
    data = call(f"{OPENAI}/models", {"Authorization": f"Bearer {key}"})
    names = [m["id"] for m in data.get("data", []) if m["id"].startswith("gpt-image")]
    return sorted(names, key=lambda n: ("mini" not in n, version(n)), reverse=True)


def gemini_image(key, model, labelled, text, aspect):
    parts = []
    for n, (label, path) in enumerate(labelled, 1):
        parts.append({"text": f"Image {n}: {label}"})
        parts.append({"inline_data": {"mime_type": mime(path), "data": base64.b64encode(path.read_bytes()).decode()}})
    parts.append({"text": text})
    body = {"contents": [{"role": "user", "parts": parts}],
            "generationConfig": {"responseModalities": ["IMAGE"], "imageConfig": {"aspectRatio": aspect}}}
    data = call(f"{GEMINI}/models/{model}:generateContent",
                {"x-goog-api-key": key, "Content-Type": "application/json"}, body)
    for candidate in data.get("candidates", []):
        for part in candidate.get("content", {}).get("parts", []):
            blob = part.get("inlineData") or part.get("inline_data")
            if blob:
                return base64.b64decode(blob["data"])
    reason = (data.get("candidates") or [{}])[0].get("finishReason") or data.get("promptFeedback")
    raise RuntimeError(f"no image returned ({reason})")


def openai_image(key, model, labelled, text, aspect):
    legend = "\n".join(f"Image {n}: {label}" for n, (label, _) in enumerate(labelled, 1))
    size = {"16:9": "1536x1024", "9:16": "1024x1536"}.get(aspect, "1024x1024")
    boundary = uuid.uuid4().hex
    chunks = []
    for name, value in (("model", model), ("prompt", legend + "\n\n" + text), ("size", size), ("n", "1")):
        chunks.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode())
    for path in (p for _, p in labelled):
        chunks.append((f'--{boundary}\r\nContent-Disposition: form-data; name="image[]"; filename="{path.name}"\r\n'
                       f"Content-Type: {mime(path)}\r\n\r\n").encode() + path.read_bytes() + b"\r\n")
    chunks.append(f"--{boundary}--\r\n".encode())
    data = call(f"{OPENAI}/images/edits",
                {"Authorization": f"Bearer {key}", "Content-Type": f"multipart/form-data; boundary={boundary}"},
                data=b"".join(chunks))
    return base64.b64decode(data["data"][0]["b64_json"])


# --- commands -------------------------------------------------------------------------------

def check(args):
    prod = production_dir(args.production)
    board, pack = load(prod), self_pack()
    found = problems(prod, board, pack)
    for problem in found:
        print("problem:", problem)
    kinds = {k: sum(f.get("kind") == k for f in board["frames"]) for k in KINDS}
    pending = to_generate(prod, board, [], False)
    print(f"{len(board['frames'])} frames: " + ", ".join(f"{n} {k}" for k, n in kinds.items()) + ". "
          f"{len(pending)} image(s) to generate: {' '.join(f['id'] for f in pending) or 'none'}.")
    if found:
        sys.exit(1)


def gen(args):
    prod = production_dir(args.production)
    board, pack = load(prod), self_pack()
    found = problems(prod, board, pack)
    if found:
        sys.exit("fix storyboard.json first:\n  " + "\n  ".join(found))
    frames = to_generate(prod, board, args.ids, args.force)
    if not frames:
        print("nothing to generate")
        return
    if args.dry_run:
        for frame in frames:
            labelled = inputs_for(prod, frame, pack)
            print(f"== {frame['id']} ({len(labelled)} images)")
            for n, (label, path) in enumerate(labelled, 1):
                print(f"  {n}. {path}  [{label[:50]}]")
            print(instruction(board, frame, pack, len(labelled)))
        print(f"\n{len(frames)} image(s) would be generated.")
        return
    provider, key = provider_and_key(args.provider)
    model = args.model or os.environ.get("GUSTO_IMAGE_MODEL") or (image_models(provider, key) or [None])[0]
    if not model:
        sys.exit(f"the {provider} key has no image model; run `models`")
    print(f"{provider} / {model}: {len(frames)} image(s)")
    out_dir = prod / "storyboard"
    (out_dir / "old").mkdir(parents=True, exist_ok=True)
    failed = 0
    with tempfile.TemporaryDirectory() as tmp:
        for frame in frames:
            labelled = [(label, shrink(path, tmp)) for label, path in inputs_for(prod, frame, pack)]
            text = instruction(board, frame, pack, len(labelled))
            aspect = frame.get("aspect") or board.get("aspect", "16:9")
            try:
                make = gemini_image if provider == "gemini" else openai_image
                image = make(key, model, labelled, text, aspect)
            except Exception as err:  # one bad frame must not stop the rest
                failed += 1
                print(f"{frame['id']}: failed: {err}", file=sys.stderr)
                continue
            path = image_path(prod, frame)
            if path.exists():
                stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
                path.rename(out_dir / "old" / f"{frame['id']}-{stamp}.png")
            path.write_bytes(image)
            log = {"frame": frame["id"], "provider": provider, "model": model,
                   "made": datetime.datetime.now().isoformat(timespec="seconds"),
                   "inputs": [str(p) for _, p in inputs_for(prod, frame, pack)], "prompt": text}
            (out_dir / f"{frame['id']}.json").write_text(json.dumps(log, ensure_ascii=False, indent=2) + "\n")
            print(path)
    render(prod, board)
    if failed:
        sys.exit(f"{failed} frame(s) failed; rerun gen to retry only those")


def models(args):
    provider, key = provider_and_key(args.provider)
    for name in image_models(provider, key):
        print(f"{provider}  {name}")


def html_cmd(args):
    prod = production_dir(args.production)
    print(render(prod, load(prod)))


def render(prod, board):
    pack = self_pack()
    sources = {}
    sources_file = prod / "refs" / "sources.json"
    if sources_file.exists():
        sources = {s["file"]: s for s in json.loads(sources_file.read_text())}
    esc = html.escape
    cards = []
    for frame in board["frames"]:
        kind = frame.get("kind")
        refs = frame.get("refs", [])
        image = image_path(prod, frame)
        if kind == "gen" and image.exists():
            main = f'<img src="storyboard/{esc(image.name)}">'
        elif kind == "gen":
            main = '<div class="pending">pendiente de generar</div>'
        elif kind == "self":
            shown = self_files(pack, frame.get("self", ["set"])[:1])[0][1]
            main = f'<img src="{esc(os.path.relpath(shown, prod))}">'
        elif kind == "ref" and refs:
            main = f'<img src="{esc(refs[0])}">'
        else:
            main = f'<div class="card">{esc(frame.get("on_screen", ""))}</div>'
        originals = []
        for ref in refs:
            src = sources.get(Path(ref).name, {})
            link = src.get("page") or src.get("image_url") or ref
            originals.append(f'<a href="{esc(link)}" title="{esc(src.get("note", ""))}"><img src="{esc(ref)}"></a>')
        meta = " · ".join(x for x in (f"Escena {frame.get('scene', '')}", frame.get("time", ""), frame.get("shot", "")) if x)
        rows = [f'<div class="id">{esc(frame["id"])} <span>{esc(meta)}</span></div>', main]
        if frame.get("line"):
            rows.append(f'<p class="line">“{esc(frame["line"])}”</p>')
        if frame.get("on_screen") and kind != "card":
            rows.append(f'<p class="screen">En pantalla: {esc(frame["on_screen"])}</p>')
        if frame.get("edit"):
            rows.append(f'<p class="edit">Edición: {esc(frame["edit"])}</p>')
        if originals:
            rows.append(f'<div class="refs">{"".join(originals)}</div>')
        cards.append(f'<section class="{esc(kind or "")}">{"".join(rows)}</section>')
    page = f"""<!doctype html><html lang="es"><meta charset="utf-8">
<title>{esc(board.get('title', 'Storyboard'))}</title>
<style>
body{{background:#111;color:#eee;font:15px/1.4 -apple-system,Helvetica,sans-serif;margin:24px}}
h1{{font-weight:500}} .grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(360px,1fr));gap:20px}}
section{{background:#1c1c1c;border-radius:8px;padding:12px}} section>img,.pending,.card{{width:100%;aspect-ratio:16/9;object-fit:cover;border-radius:4px;display:flex;align-items:center;justify-content:center}}
.pending{{background:#2a2a2a;color:#888}} .card{{background:#0b1a33;color:#fff;font-size:22px;text-align:center;padding:12px;box-sizing:border-box}}
.id{{font-weight:600;margin-bottom:8px}} .id span{{font-weight:400;color:#aaa}} .line{{font-style:italic}}
.screen{{color:#f4c46b}} .edit{{color:#9cc3ff}} .refs img{{height:64px;margin:4px 4px 0 0;border-radius:3px}}
</style>
<h1>{esc(board.get('title', 'Storyboard'))}</h1>
<p>Originales: referencia privada de la investigación, no para publicar. Las imágenes generadas muestran a Gustavo con el outfit.</p>
<div class="grid">{''.join(cards)}</div></html>
"""
    out = prod / "storyboard.html"
    out.write_text(page)
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    for name, run in (("check", check), ("gen", gen), ("html", html_cmd), ("models", models)):
        p = sub.add_parser(name)
        if name != "models":
            p.add_argument("production")
        if name in ("gen", "models"):
            p.add_argument("--provider", choices=["gemini", "openai"])
        if name == "gen":
            p.add_argument("ids", nargs="*", help="only these frame IDs")
            p.add_argument("--force", action="store_true", help="redo frames that already have an image")
            p.add_argument("--dry-run", action="store_true", help="print what would be sent; spend nothing")
            p.add_argument("--model")
        p.set_defaults(run=run)
    args = parser.parse_args()
    args.run(args)


if __name__ == "__main__":
    main()
