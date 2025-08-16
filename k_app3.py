# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import numpy as np
from datetime import date
from pathlib import Path

# =========================
# 基本設定
# =========================
st.set_page_config(page_title="競輪ログ（手入力専用：二車複＋ワイド）", layout="centered")
CSV_PATH = Path("keirin_logs.csv")
COLUMNS = ["日付", "場", "R", "券種", "買い目", "投資", "払戻", "オッズ", "的中"]

# =========================
# データ読み込み（型を厳密に整形）
# =========================
def load_df() -> pd.DataFrame:
    if CSV_PATH.exists():
        df = pd.read_csv(CSV_PATH, dtype=str)  # まず文字列で読み込む
    else:
        df = pd.DataFrame(columns=COLUMNS, dtype=object)

    # 欠損列を補完
    for c in COLUMNS:
        if c not in df.columns:
            df[c] = ""

    # 数値列を安全に数値化
    df["投資"] = pd.to_numeric(df["投資"], errors="coerce").fillna(0).astype("int64")
    df["払戻"] = pd.to_numeric(df["払戻"], errors="coerce").fillna(0).astype("int64")
    df["オッズ"] = pd.to_numeric(df["オッズ"], errors="coerce")

    # 的中列：払戻>0 を1、それ以外0
    df["的中"] = pd.to_numeric(df["的中"], errors="coerce").fillna(0).astype("int64")
    df["的中"] = np.where(df["払戻"] > 0, 1, df["的中"])

    # 文字列列を整える（余計な空白など）
    for c in ["日付", "場", "R", "券種", "買い目"]:
        df[c] = df[c].astype(str).str.strip()

    # 列順を揃える
    df = df[COLUMNS].copy()
    return df

def save_df(df: pd.DataFrame) -> None:
    # 保存前にもう一度安全整形
    out = df.copy()
    out["投資"] = pd.to_numeric(out["投資"], errors="coerce").fillna(0).astype("int64")
    out["払戻"] = pd.to_numeric(out["払戻"], errors="coerce").fillna(0).astype("int64")
    out["オッズ"] = pd.to_numeric(out["オッズ"], errors="coerce")
    out["的中"] = pd.to_numeric(out["的中"], errors="coerce").fillna(0).astype("int64")
    out.to_csv(CSV_PATH, index=False)

df = load_df()

st.title("競輪ログ（手入力専用：二車複＋ワイド）")

# =========================
# 入力フォーム（手入力のみ）
# =========================
with st.form("manual_input_form", clear_on_submit=True):
    st.subheader("1) レースを追加（手入力）")
    col1, col2, col3 = st.columns(3)
    with col1:
        in_date = st.date_input("日付", value=date.today())
        in_place = st.text_input("場", value="", placeholder="例：岸和田")
        in_r = st.text_input("R（数字）", value="", placeholder="例：4")
    with col2:
        in_kind = st.selectbox("券種", ["二車複", "ワイド", "三連複"], index=0)
        in_comb = st.text_input("買い目", value="", placeholder="例：1-7 / 1-6 / 1-7-2")
        # あなたの運用既定：二車複=各100×2, ワイド=100, 例外運用あり
        default_stake = 200 if in_kind == "二車複" else (100 if in_kind == "ワイド" else 300)
        in_stake = st.number_input("投資(円)", min_value=0, max_value=1_000_000, value=default_stake, step=100)
    with col3:
        in_pay = st.number_input("払戻(円)", min_value=0, max_value=10_000_000, value=0, step=100)
        in_odds = st.text_input("オッズ（任意）", value="", placeholder="例：8.9")

    submitted = st.form_submit_button("追加")
    if submitted:
        try:
            # バリデーション
            if not in_place.strip():
                st.error("「場」を入力してください。")
            elif not in_r.strip().isdigit():
                st.error("「R」は数字で入力してください。")
            elif not in_comb.strip():
                st.error("「買い目」を入力してください。")
            else:
                # 1行生成
                row = {
                    "日付": str(in_date),
                    "場": in_place.strip(),
                    "R": in_r.strip(),
                    "券種": in_kind,
                    "買い目": in_comb.strip(),
                    "投資": int(in_stake),
                    "払戻": int(in_pay),
                    "オッズ": (float(in_odds) if in_odds.strip() != "" else np.nan),
                    "的中": 1 if int(in_pay) > 0 else 0,
                }
                # 追記
                df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
                save_df(df)
                st.success("追加しました。")
        except Exception as e:
            st.error(f"追加に失敗しました：{e}")

# =========================
# 集計（安全に数値化してから計算）
# =========================
if len(df) == 0:
    st.info("まだデータがありません。上のフォームから追加してください。")
else:
    # 再度保険として数値化（環境差での型崩れ対策）
    df["投資"] = pd.to_numeric(df["投資"], errors="coerce").fillna(0).astype("int64")
    df["払戻"] = pd.to_numeric(df["払戻"], errors="coerce").fillna(0).astype("int64")
    df["オッズ"] = pd.to_numeric(df["オッズ"], errors="coerce")
    df["的中"] = pd.to_numeric(df["的中"], errors="coerce").fillna(0).astype("int64")

    # --- メトリクス ---
    total_bet = int(df["投資"].sum())
    total_ret = int(df["払戻"].sum())
    hits = int(df["的中"].sum())
    trials = int(len(df))
    roi = (total_ret / total_bet * 100.0) if total_bet > 0 else 0.0

    colA, colB, colC, colD = st.columns(4)
    colA.metric("累計 投資", f"{total_bet:,} 円")
    colB.metric("累計 払戻", f"{total_ret:,} 円")
    colC.metric("累計 回収率", f"{roi:.2f} %")
    colD.metric("的中数 / レース", f"{hits}/{trials}")

    # --- 券種別集計 ---
    st.subheader("2) 券種別集計")
    by_kind = df.groupby("券種", dropna=False).agg(
        投資=("投資", "sum"),
        払戻=("払戻", "sum"),
        的中=("的中", "sum"),
        本数=("買い目", "count"),
    ).reset_index()

    by_kind["投資"] = pd.to_numeric(by_kind["投資"], errors="coerce").fillna(0)
    by_kind["払戻"] = pd.to_numeric(by_kind["払戻"], errors="coerce").fillna(0)

    by_kind["回収率%"] = np.where(
        by_kind["投資"] > 0,
        (by_kind["払戻"] / by_kind["投資"] * 100).round(2),
        0.0,
    )
    st.dataframe(by_kind, use_container_width=True)

    # --- フィルタ＆明細 ---
    st.subheader("3) 明細（期間・券種でフィルタ）")
    with st.expander("フィルタ"):
        colx, coly, colz = st.columns(3)
        with colx:
            date_from = st.text_input("日付From（YYYY-MM-DD）", "")
        with coly:
            date_to = st.text_input("日付To（YYYY-MM-DD）", "")
        with colz:
            kinds = st.multiselect("券種フィルタ", ["二車複", "ワイド", "三連複"], default=["二車複", "ワイド"])

    q = df.copy()
    if date_from.strip():
        q = q[q["日付"] >= date_from.strip()]
    if date_to.strip():
        q = q[q["日付"] <= date_to.strip()]
    if kinds:
        q = q[q["券種"].isin(kinds)]

    # 行ごとの回収率（0除算回避）
    q["行回収率%"] = np.where(
        pd.to_numeric(q["投資"], errors="coerce").fillna(0) > 0,
        (pd.to_numeric(q["払戻"], errors="coerce").fillna(0) / pd.to_numeric(q["投資"], errors="coerce").fillna(1) * 100).round(2),
        0.0
    )

    q = q.sort_values(["日付", "場", "R"], ascending=[True, True, True]).reset_index(drop=True)
    st.dataframe(q, use_container_width=True)

    # --- ダウンロード（バックアップ用） ---
    st.download_button(
        label="CSVをダウンロード（バックアップ）",
        data=q.to_csv(index=False).encode("utf-8"),
        file_name="keirin_logs_export.csv",
        mime="text/csv",
    )

st.caption("※ 手入力専用版。CSV貼付や自動取得の機能は入れていません。数値型は常に安全変換し、0除算や型エラーで落ちないように実装しています。")

