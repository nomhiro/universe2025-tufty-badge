# バッジのハードウェア調査結果

`system/apps/probe` を実機で動かして確かめた結果です（2026-11-09）。probe は結果を `/probe.txt` に保存しますが、アプリからは `/system`（BADGER ドライブ）に書き込めないため、画面の写真から読み取りました。

## ファームウェア

| 項目 | 値 |
|---|---|
| MicroPython | 1.26.0（起動時の表記は `v1.14-5485.gddae88e91.dirty on 2025-10-20`） |
| `sys.implementation._machine` | `GitHub Badger with RP2350` |
| ビルド名 | `github-badger-2350` |
| 起動直後の空きメモリ | 約 153KB（`gc.mem_free()` = 153312） |
| チップ | RP2350B（80 ピン版）。内蔵温度センサーが ADC チャンネル 8 にあることから判断 |

## センサーと周辺部品

| 部品 | 結果 | 確かめた内容 | 使い方 |
|---|---|---|---|
| 加速度センサー | **なし** | ピン名にも I2C の接続先にも該当なし。2026 年版で追加された部品 | Qw/ST に MSA301 Breakout を足す |
| 照度センサー | **あり・動作** | `LIGHT_SENSE` ピンあり。手で覆うと値が変化（観測範囲 144〜768） | `machine.ADC(machine.Pin.board.LIGHT_SENSE).read_u16()`、または `badgeware.get_light()` |
| 時計チップ（RTC） | **あり・動作** | I2C の `0x51` に PCF85063A。時刻は進んでいるが未設定（2000-01-02 から数えている） | `pcf85063a.PCF85063A(i2c).datetime()`。Wi-Fi 経由の時刻合わせは `badgeware.time_from_ntp()` と `localtime_to_rtc()` |
| チップ内蔵の温度センサー | **あり・動作** | 26〜28℃（室温ではなくチップの温度） | `machine.ADC(machine.ADC.CORE_TEMP)`（= チャンネル 8） |
| ケースの LED（4 か所） | **あり・動作** | `CL0`〜`CL3` を PWM で 1 つずつ点灯できた | `machine.PWM(machine.Pin.board.CL0)` など。`badgeware` に専用の関数はない |
| IR 送受信 | ピンあり | `IR_RX`、`IR_TX` | `aye_arr.nec`（NEC 方式） |
| 電池・USB | ピンあり | `VBAT_SENSE`、`CHARGE_STAT`、`VBUS_DETECT` | `get_battery_level()`、`is_charging()`、`get_usb_connected()` |

### LED の位置（正面から見て）

| ピン | 位置 |
|---|---|
| CL0 | 右上 |
| CL1 | 左上 |
| CL2 | 左下 |
| CL3 | 右下 |

### I2C（Qw/ST 端子）

- `I2C(0, scl=5, sda=4, freq=100000)`。`machine.I2C()` の既定も同じバスです。
- 何もつないでいない状態で見える接続先は `0x51`（時計チップ）だけです。Qw/ST 端子と時計チップは同じバスにつながっているので、**`0x51` を使うセンサーはつなげません**。

## Qw/ST 用ドライバー

資料に載っていた次の 30 個は、すべて実機で読み込めました。

`pcf85063a` `powman` `aye_arr` `aye_arr.nec` `pimoroni_i2c` `qwstpad` `breakout_msa301` `breakout_bme280` `breakout_bme68x` `breakout_bme69x` `breakout_bmp280` `breakout_icp10125` `breakout_scd41` `breakout_sgp30` `breakout_mics6814` `breakout_ltr559` `breakout_bh1745` `breakout_as7262` `breakout_as7343` `breakout_vl53l5cx` `breakout_pmw3901` `breakout_paa5100` `breakout_trackball` `breakout_encoder` `breakout_potentiometer` `breakout_rtc` `ulab` `qrcode` `network` `bluetooth`

## 基板のピン名（`machine.Pin.board`）

`BUTTON_A` `BUTTON_B` `BUTTON_C` `BUTTON_DOWN` `BUTTON_HOME` `BUTTON_INT` `BUTTON_RESET` `BUTTON_UP` `CHARGE_STAT` `CL0` `CL1` `CL2` `CL3` `I2C_SCL` `I2C_SDA` `IR_RX` `IR_TX` `LCD_BACKLIGHT` `LCD_CS` `LCD_DB0`〜`LCD_DB7` `LCD_RD` `LCD_RS` `LCD_WR` `LIGHT_SENSE` `POWER_EN` `RTC_ALARM` `SENSE_1V1` `VBAT_SENSE` `VBUS_DETECT` `WL_CLK` `WL_CS` `WL_D` `WL_ON`

## badgeware モジュールにある主な名前

公式ドキュメントに載っていないものを含みます。動作は未確認です。

- 照度と画面の明るさ: `get_light` `LIGHT_SENSOR` `update_backlight` `BACKLIGHT_SMOOTHING` `MAX_BACKLIGHT_SAMPLES`
- 時刻: `rtc` `time_from_ntp` `localtime_to_rtc` `rtc_to_localtime`
- 電源と省電力: `get_battery_level` `is_charging` `get_usb_connected` `sleep` `woken_by_button` `woken_by_reset` `pressed_to_wake`
- 動作速度: `SYSTEM_VERY_SLOW` `SYSTEM_SLOW` `SYSTEM_NORMAL` `SYSTEM_FAST` `SYSTEM_TURBO`
- その他: `get_disk_usage` `AnimatedSprite` `ParticleGenerator` `BitmapFont` `wrap_and_measure`

## アプリから書き込める場所

- `/system`（BADGER ドライブ）には書き込めません。
- 保存は `/` 直下（LittleFS）に書きます。この領域は PC からは見えません。
