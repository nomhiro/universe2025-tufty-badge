# kumobii: KINTO のキャラクター「くもびぃ」が空をぷかぷか浮かぶのを眺めるアプリ
#
#   A    : ふわっと跳ねる
#   B    : 大きさを変える（小 → 中 → 大）
#   C    : 空の時間を変える（昼 → 夕方 → 夜）
#   HOME : メニューに戻る
#
# くもびぃの絵は公式画像を使わず、円を重ねて描いたファンアートです。

import sys
import os
import math
import random

sys.path.insert(0, "/system/apps/kumobii")
os.chdir("/system/apps/kumobii")

from badgeware import screen, PixelFont, shapes, brushes, io, run, Matrix

screen.font = PixelFont.load("/system/assets/fonts/ark.ppf")

W, H = 160, 120

# くもびぃの色
OUTLINE = brushes.color(18, 98, 128)
BODY = brushes.color(255, 255, 255)
SHADE = brushes.color(214, 234, 240)
PUPIL = brushes.color(18, 98, 128)

# 空の時間ごとの色: (空の上, 空の下, 遠くの雲, 文字)
# 半透明は使わず、混ぜた色を直接指定する（シミュレーターでも同じ見た目になる）
SKIES = [
    ((96, 172, 222), (186, 226, 246), (226, 242, 252), (20, 60, 90)),
    ((70, 70, 140), (250, 168, 120), (246, 196, 178), (255, 240, 230)),
    ((10, 16, 44), (34, 52, 104), (60, 78, 132), (210, 220, 255)),
]
SKY_NAMES = ["DAY", "SUNSET", "NIGHT"]
SIZES = [0.6, 1.0, 1.35]

# 本体の形: K の字に見える雲（中心からの位置と半径。大きさ 1.0 のとき）
#   左の大きなかたまり + 右上 + 右下。右側の中ほどがくびれて K に見える
BLOBS = [
    (-9, 1, 17),    # 左の胴
    (-3, -9, 13),   # 上
    (9, -11, 11),   # 右上
    (10, 11, 11),   # 右下
    (-5, 10, 13),   # 下
    (0, 1, 11),     # 真ん中を埋める
]
# 下側の影は、白い面を少し上にずらして下に水色が三日月形に残るようにする
SHADE_LIFT = 3

sky = 0
size_i = 1
scale = SIZES[size_i]

x, y = 80.0, 60.0
vx = 0.35
jump_v = 0.0
jump_y = 0.0
tilt = 0.0
blink_at = 0
look = 0.0
stars = []
far_clouds = []


def init():
    global stars, far_clouds, blink_at
    random.seed(7)
    stars = [(random.randint(0, W - 1), random.randint(0, H // 2), random.randint(0, 1000))
             for _ in range(24)]
    far_clouds = [[random.uniform(0, W), random.uniform(8, H - 30), random.uniform(0.08, 0.25),
                   random.uniform(0.6, 1.2)] for _ in range(5)]
    blink_at = io.ticks + 2000


def lerp(a, b, t):
    return int(a + (b - a) * t)


def mix(c1, c2, t):
    return (lerp(c1[0], c2[0], t), lerp(c1[1], c2[1], t), lerp(c1[2], c2[2], t))


def sky_at(py):
    top, bottom = SKIES[sky][0], SKIES[sky][1]
    return mix(top, bottom, max(0.0, min(1.0, py / H)))


def draw_sky():
    band = 4
    for i in range(0, H, band):
        screen.brush = brushes.color(*sky_at(i + band / 2))
        screen.draw(shapes.rectangle(0, i, W, band))

    if sky == 2:
        for sx, sy, phase in stars:
            t = 0.5 + 0.45 * math.sin((io.ticks + phase * 7) / 500)
            screen.brush = brushes.color(*mix(sky_at(sy), (255, 255, 230), t))
            screen.draw(shapes.rectangle(sx, sy, 1, 1))
        # 三日月: 月の円を描いてから、少しずらした空の色の円で欠けさせる
        screen.brush = brushes.color(255, 250, 210)
        screen.draw(shapes.circle(128, 22, 8))
        screen.brush = brushes.color(*sky_at(19))
        screen.draw(shapes.circle(132, 19, 7))


def draw_far_clouds():
    screen.brush = brushes.color(*SKIES[sky][2])
    for c in far_clouds:
        c[0] += c[2]
        if c[0] - 20 * c[3] > W:
            c[0] = -20 * c[3]
            c[1] = random.uniform(8, H - 30)
        cx, cy, s = c[0], c[1], c[3]
        screen.draw(shapes.circle(cx, cy, 7 * s))
        screen.draw(shapes.circle(cx + 8 * s, cy - 3 * s, 8 * s))
        screen.draw(shapes.circle(cx + 16 * s, cy, 6 * s))
        screen.draw(shapes.rounded_rectangle(cx - 2 * s, cy, 20 * s, 6 * s, 3 * s))


def rotate(dx, dy, c, s):
    return dx * c - dy * s, dx * s + dy * c


def draw_kumobii(cx, cy, k, angle, blinking, look_dx):
    c, s = math.cos(angle), math.sin(angle)

    def blobs(extra, lift=0):
        for bx, by, r in BLOBS:
            dx, dy = rotate(bx * k, (by - lift) * k, c, s)
            screen.draw(shapes.circle(cx + dx, cy + dy, r * k + extra))

    line = max(1.5, 2.2 * k)
    screen.brush = OUTLINE
    blobs(line)
    screen.brush = SHADE
    blobs(0)
    screen.brush = BODY
    for bx, by, r in BLOBS:
        # 上半分だけ持ち上げた白で塗り、下に影を残す
        lift = SHADE_LIFT if by > 0 else 0
        dx, dy = rotate(bx * k, (by - lift) * k, c, s)
        screen.draw(shapes.circle(cx + dx, cy + dy, (r - (1 if by > 0 else 0)) * k))

    # 目（白目の縁取り + 黒目）。左寄りの位置に 2 つ
    for ex in (-7, 2):
        dx, dy = rotate(ex * k, -3 * k, c, s)
        px, py = cx + dx, cy + dy
        if blinking:
            screen.brush = PUPIL
            screen.draw(shapes.rounded_rectangle(px - 2.5 * k, py - 0.6 * k, 5 * k, 1.6 * k, 0.8 * k))
            continue
        eye = shapes.circle(0, 0, 1)
        screen.brush = OUTLINE
        eye.transform = _ellipse(px, py, 3.2 * k, 4.2 * k, angle)
        screen.draw(eye)
        screen.brush = BODY
        eye.transform = _ellipse(px, py, 2.4 * k, 3.4 * k, angle)
        screen.draw(eye)
        screen.brush = PUPIL
        eye.transform = _ellipse(px + look_dx * k, py + 0.4 * k, 1.9 * k, 2.8 * k, angle)
        screen.draw(eye)


def _ellipse(px, py, rx, ry, angle):
    return Matrix().translate(px, py).rotate_radians(angle).scale(rx, ry)


def update():
    global sky, size_i, scale, x, y, vx, jump_v, jump_y, tilt, blink_at, look

    if io.BUTTON_A in io.pressed and jump_y > -1:
        jump_v = -2.6
    if io.BUTTON_B in io.pressed:
        size_i = (size_i + 1) % len(SIZES)
    if io.BUTTON_C in io.pressed:
        sky = (sky + 1) % len(SKIES)

    # 大きさはゆっくり変わる（わたあめっぽく）
    scale += (SIZES[size_i] - scale) * 0.12

    t = io.ticks / 1000
    half_w = 29 * scale
    x += vx
    if x < half_w or x > W - half_w:
        vx = -vx
        x = max(half_w, min(W - half_w, x))

    # ぷかぷか: ゆっくり上下 + 少しゆらゆら
    base_y = 58 + math.sin(t * 1.3) * 6 + math.sin(t * 0.47) * 4
    jump_v += 0.12
    jump_y = min(0.0, jump_y + jump_v)
    if jump_y == 0.0:
        jump_v = 0.0
    y = base_y + jump_y

    target_tilt = vx * 0.25 + math.sin(t * 0.9) * 0.06
    tilt += (target_tilt - tilt) * 0.08
    look += ((1.0 if vx > 0 else -1.0) - look) * 0.05

    blinking = False
    if io.ticks >= blink_at:
        blinking = True
        if io.ticks >= blink_at + 140:
            blink_at = io.ticks + random.randint(2000, 5000)

    draw_sky()
    draw_far_clouds()

    # 影（地面はないので、下のほうにうっすら）
    screen.brush = brushes.color(*mix(sky_at(112), (0, 0, 0), 0.18))
    sh = shapes.circle(0, 0, 1)
    sh.transform = Matrix().translate(x, 112).scale(18 * scale * (1 - (y - 40) / -200), 2.5)
    screen.draw(sh)

    draw_kumobii(x, y, scale, tilt, blinking, look)

    screen.brush = brushes.color(*SKIES[sky][3])
    screen.text("KUMOBII", 3, 2)
    label = SKY_NAMES[sky]
    screen.text(label, W - 3 - screen.measure_text(label)[0], 2)


if __name__ == "__main__":
    run(update)
