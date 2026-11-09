# probe: バッジに載っている部品を調べて、画面と probe.txt に書き出す
#
#   UP / DOWN : 前 / 次のページ（写真で残しやすいよう 1 画面ずつめくる）
#   A         : いまの結果を probe.txt に保存（照度の最小・最大も入る）
#   B         : LED テスト（CL0 → CL1 → CL2 → CL3 の順に 1 秒ずつ光らせる）
#   HOME      : メニューに戻る
#
# 起動時にも 1 回保存する。保存先は /system/probe.txt（BADGER ドライブの直下）、
# 書けなければ /probe.txt。

import sys
import os
import gc

sys.path.insert(0, "/system/apps/probe")
os.chdir("/system/apps/probe")

from badgeware import screen, PixelFont, shapes, brushes, io, run

try:
    import machine
except ImportError:  # シミュレーター
    machine = None

screen.font = PixelFont.load("/system/assets/fonts/ark.ppf")

BG = brushes.color(13, 17, 23)
TEXT = brushes.color(230, 237, 243)
HEAD = brushes.color(211, 250, 55)
LINE_H = 9

report = []          # probe.txt に書く行
light_adc = None
temp_adc = None
rtc = None
case_lights = []
light_min = None
light_max = None
saved_to = "-"
led_test_at = None


def add(line):
    report.append(line)
    print(line)


def safe(label, func):
    try:
        return func()
    except Exception as e:
        add(f"{label}: ERROR {type(e).__name__} {e}")
        return None


def probe_system():
    add("== system")
    add(f"implementation: {sys.implementation}")
    safe("uname", lambda: add(f"uname: {os.uname()}"))
    gc.collect()
    safe("mem_free", lambda: add(f"mem_free: {gc.mem_free()}"))


def probe_pins():
    add("== machine.Pin.board")
    if machine is None:
        add("machine: not available")
        return []
    names = sorted(n for n in dir(machine.Pin.board) if not n.startswith("_"))
    add(f"pins: {' '.join(names)}")
    return names


def probe_light(pins):
    global light_adc
    add("== light sensor")
    if "LIGHT_SENSE" not in pins:
        add("LIGHT_SENSE: no such pin")
        return
    light_adc = safe("LIGHT_SENSE adc", lambda: machine.ADC(machine.Pin.board.LIGHT_SENSE))
    if light_adc:
        add(f"LIGHT_SENSE read_u16: {light_adc.read_u16()}")


def cpu_temp_c():
    v = temp_adc.read_u16() * 3.3 / 65535
    return 27 - (v - 0.706) / 0.001721


def probe_cpu_temp():
    global temp_adc
    add("== cpu temperature")
    if machine is None:
        return
    ch = getattr(machine.ADC, "CORE_TEMP", None)
    add(f"ADC.CORE_TEMP: {ch}")
    temp_adc = safe("core temp adc", lambda: machine.ADC(ch if ch is not None else 4))
    if temp_adc:
        add(f"cpu_temp_c: {cpu_temp_c():.1f}")


def probe_i2c(pins):
    global rtc
    add("== i2c")
    if machine is None:
        return
    buses = []
    if "I2C_SDA" in pins and "I2C_SCL" in pins:
        bus = safe("i2c board pins", lambda: machine.I2C(
            0, sda=machine.Pin.board.I2C_SDA, scl=machine.Pin.board.I2C_SCL, freq=100000))
        if bus:
            buses.append(("I2C0 board I2C_SDA/SCL", bus))
    bus = safe("i2c default", lambda: machine.I2C())
    if bus:
        buses.append(("machine.I2C() default", bus))
    for name, bus in buses:
        add(f"{name}: {bus}")
        found = safe("scan", lambda: bus.scan())
        if found is not None:
            add(f"scan: {' '.join(hex(a) for a in found) or '(none)'}")
            if 0x51 in found:
                add("0x51 present -> PCF85063A RTC address")
    try:
        import pcf85063a
        rtc = pcf85063a.PCF85063A(buses[0][1] if buses else machine.I2C())
        add(f"pcf85063a datetime: {rtc.datetime()}")
    except Exception as e:
        rtc = None
        add(f"pcf85063a: ERROR {type(e).__name__} {e}")


def probe_case_lights(pins):
    add("== case lights (LED)")
    names = [n for n in ("CL0", "CL1", "CL2", "CL3") if n in pins]
    add(f"pins: {' '.join(names) or '(none)'}")
    for n in names:
        pwm = safe(f"{n} pwm", lambda: machine.PWM(getattr(machine.Pin.board, n)))
        if pwm:
            pwm.freq(500)
            pwm.duty_u16(0)
            case_lights.append(pwm)


MODULES = [
    "pcf85063a", "powman", "aye_arr", "aye_arr.nec", "pimoroni_i2c", "qwstpad",
    "breakout_msa301", "breakout_bme280", "breakout_bme68x", "breakout_bme69x",
    "breakout_bmp280", "breakout_icp10125", "breakout_scd41", "breakout_sgp30",
    "breakout_mics6814", "breakout_ltr559", "breakout_bh1745", "breakout_as7262",
    "breakout_as7343", "breakout_vl53l5cx", "breakout_pmw3901", "breakout_paa5100",
    "breakout_trackball", "breakout_encoder", "breakout_potentiometer", "breakout_rtc",
    "ulab", "qrcode", "network", "bluetooth",
]


def probe_modules():
    add("== modules")
    ok, ng = [], []
    for name in MODULES:
        try:
            __import__(name)
            ok.append(name)
        except Exception:
            ng.append(name)
        gc.collect()
    add(f"import ok: {' '.join(ok) or '(none)'}")
    add(f"import ng: {' '.join(ng) or '(none)'}")


def probe_runtime_api():
    add("== runtime api")
    import badgeware
    add(f"badgeware: {' '.join(n for n in dir(badgeware) if not n.startswith('_'))}")
    add(f"io: {' '.join(n for n in dir(io) if not n.startswith('_'))}")


def save():
    global saved_to
    lines = list(report)
    lines.append("== live")
    if light_min is not None:
        lines.append(f"light_min: {light_min}")
        lines.append(f"light_max: {light_max}")
    for path in ("/system/probe.txt", "/probe.txt"):
        try:
            with open(path, "w") as f:
                f.write("\n".join(lines) + "\n")
            saved_to = path
            return
        except Exception as e:
            print(f"save {path} failed: {e}")
    saved_to = "FAILED"


def init():
    safe("system", probe_system)
    pins = safe("pins", probe_pins) or []
    safe("light", lambda: probe_light(pins))
    safe("cpu temp", probe_cpu_temp)
    safe("i2c", lambda: probe_i2c(pins))
    safe("case lights", lambda: probe_case_lights(pins))
    safe("modules", probe_modules)
    safe("runtime api", probe_runtime_api)
    save()


def set_case_lights(index):
    for i, pwm in enumerate(case_lights):
        pwm.duty_u16(65535 if i == index else 0)


WIDTH = 156
wrapped = None
page = 0


def wrap(line):
    # 画面幅に収まるように折り返す（空白で区切り、長すぎる語は文字単位で切る）
    out, cur = [], ""
    for word in line.split(" "):
        cand = word if not cur else cur + " " + word
        if screen.measure_text(cand)[0] <= WIDTH:
            cur = cand
            continue
        if cur:
            out.append(cur)
        cur = ""
        for ch in word:
            if screen.measure_text(cur + ch)[0] > WIDTH:
                out.append(cur)
                cur = ""
            cur += ch
    out.append(cur)
    return out


def update():
    global page, light_min, light_max, led_test_at, wrapped

    if wrapped is None:
        wrapped = []
        for line in report:
            wrapped.extend(wrap(line))

    if io.BUTTON_A in io.pressed:
        save()
    if io.BUTTON_B in io.pressed and case_lights:
        led_test_at = io.ticks

    # LED テスト: 1 秒ずつ CL0..CL3、最後に全部消す
    led_label = ""
    if led_test_at is not None:
        step = (io.ticks - led_test_at) // 1000
        if step < len(case_lights):
            set_case_lights(step)
            led_label = f"LED CL{step}"
        else:
            set_case_lights(-1)
            led_test_at = None

    head = []
    if light_adc:
        v = light_adc.read_u16()
        light_min = v if light_min is None else min(light_min, v)
        light_max = v if light_max is None else max(light_max, v)
        head.append(f"light {v} ({light_min}-{light_max})")
    else:
        head.append("light: n/a")
    second = f"cpu {cpu_temp_c():.1f}C" if temp_adc else "cpu: n/a"
    if rtc:
        try:
            d = rtc.datetime()
            second += f"  rtc {d[3]:02d}:{d[4]:02d}:{d[5]:02d}"
        except Exception:
            second += "  rtc: error"
    head.append(second)

    top = 1 + 3 * LINE_H + 2
    per_page = (120 - top) // LINE_H
    pages = max(1, (len(wrapped) + per_page - 1) // per_page)
    if io.BUTTON_DOWN in io.pressed:
        page = (page + 1) % pages
    if io.BUTTON_UP in io.pressed:
        page = (page - 1) % pages
    head.append(led_label or f"page {page + 1}/{pages}  saved {saved_to}")

    screen.brush = BG
    screen.clear()
    screen.brush = HEAD
    for i, line in enumerate(head):
        screen.text(line, 2, 1 + i * LINE_H)

    screen.brush = TEXT
    start = page * per_page
    for i, line in enumerate(wrapped[start:start + per_page]):
        screen.text(line, 2, top + i * LINE_H)


if __name__ == "__main__":
    run(update)
