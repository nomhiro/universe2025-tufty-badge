"""kumobii アプリの日本語ラベル（PNG）を作る。

バッジのピクセルフォントには日本語の文字がないため、Windows の Yu Gothic Bold で
文字を描いて画像にし、アプリでは blit で貼る。

usage: python tools/make_kana_labels.py
出力: system/apps/kumobii/assets/title_<空>.png, sky_<空>.png（空 = 0 昼, 1 夕方, 2 夜）
"""

import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "system", "apps", "kumobii", "assets")
FONT = r"C:\Windows\Fonts\YuGothB.ttc"
SIZE = 11  # 濁点と小さい「ぃ」が潰れずに読める最小の大きさ

# アプリの SKIES の文字色と合わせる
COLORS = [(20, 60, 90), (255, 240, 230), (210, 220, 255)]
SKY_NAMES = ["ひる", "ゆうがた", "よる"]


def label(text, color, path):
    font = ImageFont.truetype(FONT, SIZE)
    mask = Image.new("L", (120, 24), 0)
    d = ImageDraw.Draw(mask)
    d.fontmode = "1"  # にじませない（画面は 2 倍に拡大されるので、くっきりさせる）
    d.text((2, 2), text, font=font, fill=255)
    mask = mask.crop(mask.getbbox())
    im = Image.new("RGBA", mask.size, color + (0,))
    im.putalpha(mask)
    im.save(path)
    print(path, im.size)


def main():
    os.makedirs(OUT, exist_ok=True)
    for i, color in enumerate(COLORS):
        label("くもびぃ", color, os.path.join(OUT, f"title_{i}.png"))
        label(SKY_NAMES[i], color, os.path.join(OUT, f"sky_{i}.png"))


if __name__ == "__main__":
    main()
