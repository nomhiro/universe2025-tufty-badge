"""開発環境の準備: 公式リポジトリの取得と、シミュレーター用 system/ の組み立て。

usage: python tools/bootstrap.py

- vendor/home に badger/home を clone する（既にあれば何もしない）
- vendor/home/badge25 の assets と標準アプリを system/ にコピーする
  （system/apps にある自作アプリは上書きしない）
"""
import os
import shutil
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
VENDOR = os.path.join(ROOT, "vendor", "home")
BADGE25 = os.path.join(VENDOR, "badge25")
SYSTEM = os.path.join(ROOT, "system")

# バッジに標準で入っているアプリ（menu はページ切り替え式の badge25 版）
STOCK_APPS = ["badge", "flappy", "gallery", "menu", "monapet", "quest", "sketch", "startup"]


def main():
    if not os.path.isdir(VENDOR):
        subprocess.run(
            ["git", "clone", "--depth", "1", "https://github.com/badger/home.git", VENDOR],
            check=True,
        )

    dst_assets = os.path.join(SYSTEM, "assets")
    if not os.path.isdir(dst_assets):
        shutil.copytree(os.path.join(BADGE25, "assets"), dst_assets)
        print("copied assets")

    for app in STOCK_APPS:
        dst = os.path.join(SYSTEM, "apps", app)
        if os.path.isdir(dst):
            continue
        shutil.copytree(os.path.join(BADGE25, "apps", app), dst)
        print(f"copied apps/{app}")

    print("ready. try:")
    print(f"  {sys.executable} vendor/home/badge25/simulator/badge_simulator.py -C system system/apps/hello_badge")


if __name__ == "__main__":
    main()
