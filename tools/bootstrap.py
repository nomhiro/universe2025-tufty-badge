"""開発環境の準備: シミュレーターが入っている公式リポジトリを vendor/home に取得する。

usage: python tools/bootstrap.py
"""
import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
VENDOR = os.path.join(ROOT, "vendor", "home")


def main():
    if not os.path.isdir(VENDOR):
        subprocess.run(
            ["git", "clone", "--depth", "1", "https://github.com/badger/home.git", VENDOR],
            check=True,
        )
    print("ready. try:")
    print(f"  {sys.executable} vendor/home/badge25/simulator/badge_simulator.py -C system system/apps/flappy")


if __name__ == "__main__":
    main()
