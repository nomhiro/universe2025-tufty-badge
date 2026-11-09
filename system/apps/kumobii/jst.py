# 日本時間（JST = UTC+9）を返す。
#
# 1. 起動時に、本体の時計チップ（PCF85063A、I2C 0x51）の時刻を読む。
#    時計チップは UTC で持たせる（公式の 2026 年版 system アプリと同じ決まり）。
# 2. 時計チップが未設定（2024 年より前）なら、secrets.py の Wi-Fi につないで
#    NTP で UTC を取り、チップ内蔵の時計と時計チップの両方に書く。
#    次からは Wi-Fi なしでも正しい時刻になる。
# 3. 表示するときに 9 時間足す。
#
# シミュレーターには machine / network がないので、PC の時計（UTC）を使う。

import sys
import time

from badgeware import io

try:
    import machine
except ImportError:
    machine = None

try:
    import network
    import ntptime
    NET_AVAILABLE = True
except ImportError:
    NET_AVAILABLE = False

JST_OFFSET = 9 * 3600
CONNECT_TIMEOUT_MS = 20000
RETRY_MS = 60000

valid = machine is None   # シミュレーターでは PC の時計を信じる
status = ""               # 画面に出す短い状態
_wlan = None
_started_at = None
_failed_at = None


def _hw_rtc():
    import pcf85063a
    return pcf85063a.PCF85063A(machine.I2C(0, scl=5, sda=4))


def restore():
    """時計チップの時刻が設定済みなら、チップ内蔵の時計に写す。"""
    global valid, status
    if machine is None:
        return
    try:
        y, mo, d, hh, mm, ss, wday = _hw_rtc().datetime()
        if y >= 2024:
            machine.RTC().datetime((y, mo, d, wday, hh, mm, ss, 0))
            valid = True
    except Exception as e:
        status = "rtc err"
        print("restore:", e)


def _credentials():
    sys.path.insert(0, "/")
    try:
        from secrets import WIFI_SSID, WIFI_PASSWORD
        return WIFI_SSID, WIFI_PASSWORD
    except ImportError:
        return None, None
    finally:
        sys.path.pop(0)


def _have_ip():
    return _wlan is not None and _wlan.ifconfig()[0] != "0.0.0.0"


def _stop_wifi():
    global _wlan
    try:
        _wlan.disconnect()
        _wlan.active(False)
    except Exception:
        pass
    _wlan = None


def tick():
    """時刻が未設定のあいだ、毎フレーム呼ぶ。待たずにすぐ戻る（NTP の 1 回だけ少し待つ）。"""
    global _wlan, _started_at, _failed_at, valid, status
    if valid or not NET_AVAILABLE:
        return
    if _failed_at is not None and io.ticks - _failed_at < RETRY_MS:
        return

    if _wlan is None:
        ssid, password = _credentials()
        if not ssid:
            status = "no wifi"
            _failed_at = io.ticks
            return
        _wlan = network.WLAN(network.STA_IF)
        _wlan.active(True)
        _wlan.connect(ssid, password)
        _started_at = io.ticks
        status = "wifi..."
        return

    if not _have_ip():
        if io.ticks - _started_at > CONNECT_TIMEOUT_MS:
            status = "wifi err"
            _failed_at = io.ticks
            _stop_wifi()
        return

    status = "sync..."
    try:
        ntptime.settime()                     # チップ内蔵の時計 <- UTC
        t = time.gmtime()
        _hw_rtc().datetime((t[0], t[1], t[2], t[3], t[4], t[5], t[6]))  # 時計チップ <- UTC
        valid = True
        status = ""
    except Exception as e:
        print("ntp:", e)
        status = "sync err"
        _failed_at = io.ticks
    _stop_wifi()


def now():
    """日本時間の (年, 月, 日, 時, 分, 秒)。時刻が未設定なら None。"""
    if not valid:
        return None
    t = time.gmtime(time.time() + JST_OFFSET)
    return t[0], t[1], t[2], t[3], t[4], t[5]
