# kumobii: KINTO のキャラクター「くもびぃ」が空をぷかぷか浮かぶのを眺めるアプリ
#
#   A    : ふわっと跳ねる
#   B    : 大きさを変える（小 → 中 → 大）
#   C    : 空を変える（じどう → 昼 → 夕方 → 夜 → じどう）
#   HOME : メニューに戻る
#
# 「じどう」のときは、日本時間で空が変わる（6〜16 時 昼、16〜18 時 夕方、18〜6 時 夜）。
# 時刻は本体の時計チップから読み、未設定なら Wi-Fi で合わせる（jst.py）。
#
# くもびぃの絵は公式画像を使わず、円を重ねて描いたファンアートです。

import sys
import os
import math
import random

sys.path.insert(0, "/system/apps/kumobii")
os.chdir("/system/apps/kumobii")

from badgeware import screen, Image, PixelFont, shapes, brushes, io, run, Matrix
import jst

screen.font = PixelFont.load("/system/assets/fonts/ark.ppf")

W, H = 160, 120

# くもびぃの色
OUTLINE = brushes.color(18, 98, 128)
BODY = brushes.color(255, 255, 255)
SHADE = brushes.color(214, 234, 240)
PUPIL = brushes.color(18, 98, 128)
EYE_RIM = brushes.color(170, 196, 206)

# 空の時間ごとの色: (空の上, 空の下, 遠くの雲, 文字)
# 半透明は使わず、混ぜた色を直接指定する（シミュレーターでも同じ見た目になる）
SKIES = [
    ((96, 172, 222), (186, 226, 246), (226, 242, 252), (20, 60, 90)),
    ((70, 70, 140), (250, 168, 120), (246, 196, 178), (255, 240, 230)),
    ((10, 16, 44), (34, 52, 104), (60, 78, 132), (210, 220, 255)),
]
# 日本語の文字は画像で貼る（tools/make_kana_labels.py で作る）
TITLES = [Image.load(f"assets/title_{i}.png") for i in range(3)]
SKY_LABELS = [Image.load(f"assets/sky_{i}.png") for i in range(3)]
AUTO_LABELS = [Image.load(f"assets/auto_{i}.png") for i in range(3)]
SIZES = [0.6, 1.0, 1.35]

# 本体の形: K の字に見える雲（中心からの位置と半径。大きさ 1.0 のとき）
#   左上・左下・右上・右下の 4 つのかたまりと、すき間を埋める円。
#   左側はなだらかにふくらみ、右側の中ほどだけが浅くくびれて K に見える。
#   公式の立体イラストの輪郭に円を重ねて合わせた値
BLOBS = [
    (-8.7, -11.0, 13.0),  # 左上
    (12.0, -13.2, 9.6),   # 右上
    (12.0, 9.8, 11.1),    # 右下
    (-7.9, 10.4, 13.3),   # 左下
    (-10.1, 0.1, 13.0),   # 左の中ほど
    (2.0, -0.5, 13.4),    # 真ん中
    (1.3, -11.0, 9.3),    # 上のくぼみを浅くする
    (1.3, 10.5, 8.1),     # 下のくぼみを浅くする
]
EYES_X = (-10.0, -0.5)
EYE_Y = -2.5
# 下側の影は、白い面を少し上にずらして下に水色が三日月形に残るようにする
SHADE_LIFT = 3

sky = 0
sky_mode = None   # None = じどう（日本時間で決める）、0〜2 = 手動
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
    jst.restore()


def sky_for_hour(hour):
    if 6 <= hour < 16:
        return 0
    if 16 <= hour < 18:
        return 1
    return 2


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
        screen.draw(shapes.circle(118, 34, 8))
        screen.brush = brushes.color(*sky_at(31))
        screen.draw(shapes.circle(122, 31, 7))


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
        lift = SHADE_LIFT if by > 1 else 0
        dx, dy = rotate(bx * k, (by - lift) * k, c, s)
        screen.draw(shapes.circle(cx + dx, cy + dy, (r - (1 if by > 1 else 0)) * k))

    # 目（白目の縁取り + 黒目）。左寄りの位置に 2 つ
    for ex in EYES_X:
        dx, dy = rotate(ex * k, EYE_Y * k, c, s)
        px, py = cx + dx, cy + dy
        if blinking:
            screen.brush = PUPIL
            screen.draw(shapes.rounded_rectangle(px - 2.5 * k, py - 0.6 * k, 5 * k, 1.6 * k, 0.8 * k))
            continue
        eye = shapes.circle(0, 0, 1)
        if k < 0.8:
            # 小さいときは白目を描くとつぶれるので、黒目だけにする
            screen.brush = PUPIL
            eye.transform = _ellipse(px, py, max(1.0, 1.8 * k), max(1.4, 2.6 * k), angle)
            screen.draw(eye)
            continue
        # 白目の縁は淡い色（公式イラストの、くぼんだ白目の影に合わせる）
        screen.brush = EYE_RIM
        eye.transform = _ellipse(px, py, 2.9 * k, 3.6 * k, angle)
        screen.draw(eye)
        screen.brush = BODY
        eye.transform = _ellipse(px - 0.3 * k, py - 0.3 * k, 2.3 * k, 3.0 * k, angle)
        screen.draw(eye)
        screen.brush = PUPIL
        eye.transform = _ellipse(px + (0.4 + look_dx * 0.5) * k, py + 0.5 * k, 1.8 * k, 2.5 * k, angle)
        screen.draw(eye)


def _ellipse(px, py, rx, ry, angle):
    return Matrix().translate(px, py).rotate_radians(angle).scale(rx, ry)


def update():
    global sky, sky_mode, size_i, scale, x, y, vx, jump_v, jump_y, tilt, blink_at, look

    if io.BUTTON_A in io.pressed and jump_y > -1:
        jump_v = -2.6
    if io.BUTTON_B in io.pressed:
        size_i = (size_i + 1) % len(SIZES)
    if io.BUTTON_C in io.pressed:
        sky_mode = 0 if sky_mode is None else (None if sky_mode == len(SKIES) - 1 else sky_mode + 1)

    jst.tick()
    now = jst.now()
    if sky_mode is not None:
        sky = sky_mode
    elif now:
        sky = sky_for_hour(now[3])

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

    screen.blit(TITLES[sky], 3, 2)
    screen.blit(SKY_LABELS[sky], W - 3 - SKY_LABELS[sky].width, 2)
    if sky_mode is None:
        screen.blit(AUTO_LABELS[sky], W - 3 - AUTO_LABELS[sky].width, 15)

    # 日本時間の時計（上の真ん中）。未設定なら --:-- と状態
    screen.brush = brushes.color(*SKIES[sky][3])
    clock = f"{now[3]:02d}:{now[4]:02d}" if now else "--:--"
    screen.text(clock, (W - screen.measure_text(clock)[0]) // 2, 2)
    if jst.status:
        screen.text(jst.status, (W - screen.measure_text(jst.status)[0]) // 2, 12)


if __name__ == "__main__":
    run(update)
