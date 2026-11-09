# Universe 2025 (Tufty) Badge で遊ぶ

GitHub Universe 2025 でもらったバッジ（Pimoroni Tufty 2350 ベース、MonaOS + MicroPython）の中身を管理するリポジトリです。`system/` は、バッジの `/system`（USB Disk Mode で見える `BADGER` ドライブ）をそのまま写したものです。

公式リポジトリ [badger/home](https://github.com/badger/home) は 2026 年版のバッジ向けに変わっています。2025 年版の資料・シミュレーター・標準アプリは、その中の `badge25/` にあります。

## バッジの中身

| パス | 中身 | 出どころ |
|---|---|---|
| `system/main.py` | 起動処理（演出 → メニュー → アプリ） | 工場出荷時のまま |
| `system/apps/menu/` | ランチャー | `__init__.py` と `default_icon.png` を badge25 のページ切り替え版に替えた |
| `system/apps/hello_badge/` | ボタンテスター（自作） | このリポジトリ |
| `system/apps/` のほかのアプリ | badge, flappy, gallery, monapet, quest, sketch, startup | 工場出荷時のまま |
| `system/assets/` | フォント、Mona のスプライト、アイコン | 工場出荷時のまま |
| `secrets.py` | Wi-Fi の SSID・パスワード、GitHub のユーザー名 | **リポジトリには入れない**。ひな形は `secrets.example.py` |

工場出荷時のファイルは Pimoroni と GitHub の MIT ライセンスのものです（[badger/home の LICENSE](https://github.com/badger/home/blob/main/LICENSE)）。`system/` 以下は `.gitattributes` で改行コードの変換を止めて、バッジとバイト単位で同じに保っています。

## アプリ

### hello_badge

押したボタンの枠が、実機と同じ位置（右端に UP / DOWN、下端に A / B / C）で光ります。

- A / C / UP / DOWN: 丸を動かす
- B: 丸の色を変える
- 右上: 電池残量

![hello_badge](docs/images/hello_badge.png)

## 準備（Windows）

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install pygame
.venv\Scripts\python tools\bootstrap.py   # シミュレーター入りの公式リポジトリを vendor/home に取得
```

## バッジと同期する

USB-C（データ通信できるケーブル）でつなぎ、背面の `RESET` をすばやく 2 回押して USB Disk Mode にします。

```powershell
.venv\Scripts\python tools\badge_sync.py status     # バッジと system/ の違いを見る
.venv\Scripts\python tools\badge_sync.py push -n    # 書き込む内容を確認する（書き込まない）
.venv\Scripts\python tools\badge_sync.py push       # system/ の変更をバッジに書く
.venv\Scripts\python tools\badge_sync.py pull       # バッジの中身を system/ に取り込む
```

- `push` は、変わったファイルだけを書き込みます。バッジ側のファイルは消しません（消すときは `--delete`）。
- `pull` は、`system/` をバッジと同じ状態にします。取り込んだあとは `git diff` で変化を確認してコミットします。
- `secrets.py` は、どちらの方向にも同期しません。
- 書き込んだあとは、ドライブを取り外してから `RESET` を 1 回押して再起動します。

## シミュレーターで動かす

```powershell
.venv\Scripts\python vendor\home\badge25\simulator\badge_simulator.py -C system system\apps\hello_badge
```

キー操作: 矢印 = UP / DOWN、Z / X / Space = A / B / C、Esc = HOME。`system\apps\menu` を指定すると、メニューから動かせます。

画面写真を自動で撮る例（20 フレーム目に B を押し、10 と 30 フレーム目を保存）:

```powershell
.venv\Scripts\python tools\sim_snapshot.py system\apps\hello_badge out\hello_badge --keys "20:b" --shots 10,30
```

シミュレーターには LED バックライトがなく、電池残量は常に 75% です。
