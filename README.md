# 宝塚記念 2026 ダッシュボード（GitHub Pages 常設版）

オッズ・枠順などの揮発情報を `update_odds.py` が取得して JSON に書き出し、
`index.html` がその JSON を読んで表示する **データ／表示 分離型**。
既存の cfd-dashboard / market-briefing agent と同じ思想です。

## 構成

```
takarazuka/
├─ index.html                  # ダッシュボード本体（分析＋画像を内蔵・単一ファイル完結）
├─ update_odds.py              # claude -p で最新オッズ・枠を取得→JSON書出し
├─ data/
│   └─ takarazuka_2026.json    # 揮発データ（スクリプトが上書き）
└─ README.md
```

※ JRAロゴと宝塚記念バナーは `index.html` に base64 で埋め込み済み（外部画像ファイル不要）。
※ 書体は iOS 標準（SF Pro / Hiragino Sans）系のシステムフォントスタックを使用。

データの流れ：
`update_odds.py` → `claude -p`（Web取得）→ JSON抽出 → `data/takarazuka_2026.json` → `index.html` が fetch

## 更新の実行

```powershell
cd path\to\takarazuka
python update_odds.py
```

- `claude` コマンドが PATH 上にあること（既存 agent が動いていればOK）。
- API キー不要（Claude Code 認証を流用）。
- 成功すると `data/takarazuka_2026.json` が更新され、`updated` 時刻が入ります。

## GitHub Pages へ反映

JSON はクライアントが `./data/...` を fetch するだけなので CORS 問題なし（同一オリジン）。
更新を即反映するには JSON をコミット＆プッシュします。

手動の場合：
```powershell
git add -A
git commit -m "update odds"
git push
```

`update_odds.py` 内の `AUTO_PUSH = True` にすると、取得後に
`git add / commit / push` まで自動実行します（リポジトリ直下で実行する前提）。

公開URL例：`https://yozarl1997.github.io/<repo>/takarazuka/`

## 定期実行（Windows タスクスケジューラ）

レース直前は変動が大きいので、木〜日に短間隔がおすすめ。

1. タスクスケジューラ →「基本タスクの作成」
2. 操作：プログラムの開始
   - プログラム：`python`（またはフルパス `C:\...\python.exe`）
   - 引数：`update_odds.py`
   - 開始：`path\to\takarazuka`
3. トリガー：毎日 or 30分間隔（詳細設定で「繰り返し間隔 30分／継続時間 1日」）

CLI から登録する例（30分おき・8時〜20時）:
```powershell
schtasks /create /tn "Takarazuka Odds" /tr "python C:\path\to\takarazuka\update_odds.py" /sc minute /mo 30 /st 08:00 /et 20:00 /f
```

## カスタマイズ

- 取得項目を変えたい：`update_odds.py` の `PROMPT` を編集。
- 別レースに流用：`PROMPT` のレース名・URL・`DATA_PATH`・`index.html` の発走時刻と分析文を差し替え。
- 取得が不安定なとき：`PROMPT` の参照URLを増やす、`TIMEOUT` を伸ばす。

## 注意

- 確定枠順は JRA が **6/11(木) 14:00** 公開。それ以前は `gate`/`num`/`odds` は null のまま。
- 競馬は確率事象であり、本ツールは公開情報の整理です。投資助言ではありません。
