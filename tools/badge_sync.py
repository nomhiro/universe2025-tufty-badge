"""バッジ（BADGER ドライブ）と system/ を同期する。

usage:
  python tools/badge_sync.py status          # 違いを表示するだけ
  python tools/badge_sync.py pull [-n]       # バッジ → system/（system/ をバッジと同じ状態にする）
  python tools/badge_sync.py push [-n] [--delete]
                                             # system/ → バッジ（変わったファイルだけ書く）

-n / --dry-run  何をするか表示するだけで、書き込まない
--delete        push で、system/ に無いファイルをバッジから消す（既定では消さない）

バッジは背面の RESET を 2 回押して USB Disk Mode にしておく。
secrets.py（Wi-Fi のパスワードなど）は、どちらの方向にも同期しない。
"""
import argparse
import hashlib
import os
import shutil
import string
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SYSTEM = os.path.join(ROOT, "system")
LABEL = "BADGER"
SKIP_NAMES = {"secrets.py", "System Volume Information", "__pycache__", ".badge_state", ".DS_Store"}


def find_drive():
    if sys.platform == "win32":
        import ctypes

        buf = ctypes.create_unicode_buffer(261)
        for letter in string.ascii_uppercase:
            root = f"{letter}:\\"
            if ctypes.windll.kernel32.GetVolumeInformationW(root, buf, 261, None, None, None, None, 0):
                if buf.value == LABEL:
                    return root
        return None
    for base in ("/Volumes", f"/media/{os.environ.get('USER', '')}", f"/run/media/{os.environ.get('USER', '')}"):
        path = os.path.join(base, LABEL)
        if os.path.isdir(path):
            return path
    return None


def list_files(root):
    files = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_NAMES and not d.startswith(".")]
        for name in filenames:
            if name in SKIP_NAMES or name.startswith("."):
                continue
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, root).replace(os.sep, "/")
            files[rel] = full
    return files


def digest(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def compare(src_root, dst_root):
    src, dst = list_files(src_root), list_files(dst_root)
    added = sorted(set(src) - set(dst))
    removed = sorted(set(dst) - set(src))
    changed = sorted(p for p in set(src) & set(dst) if digest(src[p]) != digest(dst[p]))
    return src, added, changed, removed


def remove_empty_dirs(root):
    for dirpath, _, _ in sorted(os.walk(root), key=lambda t: -len(t[0])):
        if dirpath != root and not os.listdir(dirpath):
            os.rmdir(dirpath)


def sync(src_root, dst_root, dry_run, delete):
    src, added, changed, removed = compare(src_root, dst_root)
    for p in added:
        print(f"  + {p}")
    for p in changed:
        print(f"  M {p}")
    for p in removed:
        print(f"  {'-' if delete else '?'} {p}{'' if delete else '  (残す)'}")
    if not (added or changed or (removed and delete)):
        print("  差分なし")
        return
    if dry_run:
        print("  (dry-run のため書き込んでいません)")
        return
    for p in added + changed:
        out = os.path.join(dst_root, p)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        shutil.copyfile(src[p], out)
    if delete:
        for p in removed:
            os.remove(os.path.join(dst_root, p))
        remove_empty_dirs(dst_root)
    if hasattr(os, "sync"):
        os.sync()
    # 書いた結果を読み直して確かめる
    _, a2, c2, r2 = compare(src_root, dst_root)
    if a2 or c2 or (delete and r2):
        sys.exit(f"検証に失敗: 追加 {a2} 変更 {c2} 削除残り {r2 if delete else []}")
    print(f"  完了: 追加 {len(added)} / 変更 {len(changed)} / 削除 {len(removed) if delete else 0}")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap =argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["status", "pull", "push"])
    ap.add_argument("-n", "--dry-run", action="store_true")
    ap.add_argument("--delete", action="store_true", help="push 時にバッジ側の余分なファイルを消す")
    args = ap.parse_args()

    drive = find_drive()
    if not drive:
        sys.exit("BADGER ドライブが見つかりません。RESET を 2 回押して USB Disk Mode にしてください。")
    print(f"BADGER: {drive}")

    if args.command == "status":
        print("バッジ → system/ で見た差分:")
        sync(drive, SYSTEM, dry_run=True, delete=True)
    elif args.command == "pull":
        sync(drive, SYSTEM, args.dry_run, delete=True)
    else:
        sync(SYSTEM, drive, args.dry_run, args.delete)


if __name__ == "__main__":
    main()
