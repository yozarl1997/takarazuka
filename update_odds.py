#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
宝塚記念2026 オッズ・枠順 自動更新スクリプト
------------------------------------------------
既存agent群と同じ subprocess.run(["claude", "-p", prompt]) 方式。
Claude Code にnetkeiba/JRAの最新オッズ・枠順を取得させ、
data/takarazuka_2026.json を書き換える。GitHub Pages の index.html がこれを読む。

  実行     : python update_odds.py
  定期実行 : Windowsタスクスケジューラ（例：木〜日 30分おき など）
  自動push : 下の AUTO_PUSH を True にすると git add/commit/push まで実行
"""

import json
import re
import sys
import shutil
import datetime
import pathlib
import subprocess

# ── 設定 ─────────────────────────────────────────────
BASE       = pathlib.Path(__file__).resolve().parent
DATA_PATH  = BASE / "data" / "takarazuka_2026.json"
AUTO_PUSH  = False          # True で git push まで自動化（GitHub Pages即反映）
TIMEOUT    = 300            # claude 応答の最大待機秒数

# ── Claude Code への指示（厳格JSONのみ返させる）──────────
PROMPT = r"""
2026年6月14日(日) 阪神11R「宝塚記念(GI・芝2200m)」の最新情報をWeb検索して取得してください。
枠順は6/11に確定済みです。netkeiba・JRA・競馬ブック等を参照。

参照候補URL:
- https://race.netkeiba.com/special/index.html?id=0068
- https://www.jra.go.jp/keiba/g1/takara/syutsuba.html
- https://s.keibabook.co.jp/cyuou/syutuba/202603010411

各出走馬(全18頭)について:
- num(馬番 1-18) / waku(枠番 1-8) / gate("枠-馬番")
- name(馬名) / jockey(確定騎手) / weight(斤量)
- odds(最新の単勝オッズ・数値文字列) / pop(人気順位・整数) ※未確定なら null
- aptScore(宝塚適性を1-5で。芝2000m以上のGI実績・グランプリ実績・阪神/中山内回りのタフコース実績・先行力を加味)
- apt(適性の要点を60字以内で)
- form(宝塚と同条件＝芝2000m以上のGI、特にグランプリや内回りタフコースでの好走を中心に最大4件。各 {"d":"YY.MM","race":"レース名(格)","c":"コース例 中山芝2500","fin":"1着"} )
全体:
- track(馬場/天気の短評) / weather({"high":,"low":,"rain":})

【厳守】回答は次の構造のJSON1個のみ。前置き・解説・コードブロック記号(```)は一切付けないこと。
{"race":"宝塚記念 2026","updated":"YYYY-MM-DD HH:MM","track":"良/晴 等","post_confirmed":true,"weather":{"high":28,"low":19,"rain":40},"horses":[{"num":1,"waku":1,"gate":"1-1","name":"ダノンデサイル","jockey":"戸崎圭太","weight":"58.0","odds":"6.2","pop":4,"aptScore":4,"apt":"急坂良馬場巧者でGI実績十分","form":[{"d":"26.04","race":"大阪杯(GI)","c":"阪神芝2000","fin":"3着"}]}]}
""".strip()


def run_claude(prompt: str) -> str:
    """既存agentと同じ claude -p 方式で実行し、stdoutを返す。"""
    exe = shutil.which("claude") or "claude"   # Windowsで claude.cmd の場合も which が解決
    proc = subprocess.run(
        [exe, "-p", prompt],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=TIMEOUT,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"claude returncode={proc.returncode}\n{proc.stderr[:600]}")
    return proc.stdout


def extract_json(text: str) -> dict:
    """claude出力からJSON本体だけを取り出してパース。"""
    t = text.replace("```json", "").replace("```", "").strip()
    m = re.search(r"\{[\s\S]*\}", t)
    if not m:
        raise ValueError(f"JSONが見つかりません。先頭200字: {t[:200]!r}")
    return json.loads(m.group(0))


def validate(data: dict) -> dict:
    """最低限の整形・検証。"""
    if "horses" not in data or not isinstance(data["horses"], list):
        raise ValueError("horses 配列がありません")
    data.setdefault("race", "宝塚記念 2026")
    data["updated"] = data.get("updated") or datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    # 文字列化の揺れを吸収
    for h in data["horses"]:
        if h.get("odds") is not None:
            h["odds"] = str(h["odds"])
        if h.get("pop") is not None:
            try:
                h["pop"] = int(h["pop"])
            except (ValueError, TypeError):
                h["pop"] = None
    return data


def git_push() -> None:
    msg = "update odds " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    for args in (["git", "add", "-A"],
                 ["git", "commit", "-m", msg],
                 ["git", "push"]):
        r = subprocess.run(args, cwd=BASE, capture_output=True,
                           text=True, encoding="utf-8", errors="replace")
        print(f"  $ {' '.join(args)} -> rc={r.returncode}")
        if r.returncode != 0 and "nothing to commit" not in (r.stdout + r.stderr):
            print("   ", (r.stderr or r.stdout).strip()[:200])


def main() -> None:
    print("[1/3] Claude Code で最新オッズ・枠順を取得中…")
    raw = run_claude(PROMPT)

    print("[2/3] JSON抽出・検証中…")
    data = validate(extract_json(raw))

    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    DATA_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    n = len(data["horses"])
    odds_n = sum(1 for h in data["horses"] if h.get("odds"))
    print(f"      書き出し完了: {DATA_PATH}")
    print(f"      {n}頭中 {odds_n}頭にオッズ反映 / 更新時刻 {data['updated']}")

    if AUTO_PUSH:
        print("[3/3] git push…")
        git_push()
    else:
        print("[3/3] 完了（AUTO_PUSH=False のため push なし）")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
