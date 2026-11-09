# hello_badge: 最初の自作アプリ（ボタンテスター）
#
# - 押しているボタンが、実機と同じ位置の枠で光る
#   (右端に UP / DOWN、下端に A / B / C)
# - A / C / UP / DOWN で真ん中の丸を動かす、B で色を変える
# - 右上に電池残量を表示する

import sys
import os

sys.path.insert(0, "/system/apps/hello_badge")
os.chdir("/system/apps/hello_badge")

from badgeware import screen, PixelFont, shapes, brushes, io, run, get_battery_level, is_charging

# 画面は 160x120（実機の 320x240 を縦横2倍に拡大して表示）
W, H = 160, 120

BG = brushes.color(13, 17, 23)
TEXT = brushes.color(230, 237, 243)
DIM = brushes.color(48, 54, 61)
LIT = brushes.color(211, 250, 55)
COLORS = [(86, 211, 100), (88, 166, 255), (247, 120, 186), (255, 166, 87)]

screen.font = PixelFont.load("/system/assets/fonts/nope.ppf")

# ボタンの表示位置 (x, y, w, h, ラベル)。実機の配置に合わせている
BUTTONS = [
    (io.BUTTON_UP, 140, 30, 18, 14, "UP"),
    (io.BUTTON_DOWN, 140, 70, 18, 14, "DN"),
    (io.BUTTON_A, 30, 104, 22, 14, "A"),
    (io.BUTTON_B, 69, 104, 22, 14, "B"),
    (io.BUTTON_C, 108, 104, 22, 14, "C"),
]

x, y = 68.0, 60.0
color_index = 0
presses = 0
SPEED = 60  # 1秒あたりのピクセル数


def update():
    global x, y, color_index, presses

    # --- 入力 ---
    dt = io.ticks_delta / 1000
    if io.BUTTON_A in io.held:
        x -= SPEED * dt
    if io.BUTTON_C in io.held:
        x += SPEED * dt
    if io.BUTTON_UP in io.held:
        y -= SPEED * dt
    if io.BUTTON_DOWN in io.held:
        y += SPEED * dt
    if io.BUTTON_B in io.pressed:
        color_index = (color_index + 1) % len(COLORS)
    presses += len(io.pressed)

    # 丸が画面外に出ないようにする（右端のボタン表示と下端は避ける）
    x = max(8, min(x, 128))
    y = max(24, min(y, 92))

    # --- 描画 ---
    screen.brush = BG
    screen.clear()

    screen.brush = TEXT
    screen.text("hello badge!", 4, 3)

    battery = "chg" if is_charging() else f"{get_battery_level()}%"
    w, _ = screen.measure_text(battery)
    screen.text(battery, W - w - 4, 3)

    screen.text(f"presses: {presses}", 4, 14)

    # 動く丸
    screen.brush = brushes.color(*COLORS[color_index])
    screen.draw(shapes.circle(x, y, 8))

    # ボタンの枠（押している間だけ光る）
    for button, bx, by, bw, bh, label in BUTTONS:
        held = button in io.held
        screen.brush = LIT if held else DIM
        screen.draw(shapes.rounded_rectangle(bx, by, bw, bh, 3))
        screen.brush = BG if held else TEXT
        lw, _ = screen.measure_text(label)
        screen.text(label, bx + (bw - lw) / 2, by + 2)


if __name__ == "__main__":
    run(update)
