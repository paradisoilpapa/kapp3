# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import numpy as np
from datetime import date
from pathlib import Path

# =========================
# 基本設定
# =========================
st.set_page_config(page_title="競輪ログ（手入力・編集・削除・会場プリセット）", layout="centered")
CSV_PATH = Path("keirin_logs.csv")
COLUMNS = ["ID", "日付", "場", "R", "券種", "買い目", "投資", "払戻", "オッズ", "的中"]

# 会場プリセット
VENUES = sorted(set([
    "いわき平","京王閣","取手","宇都宮","前橋","西武園","大宮","弥彦","松戸","千葉",
    "川崎","平塚","小田原","伊東温泉","静岡","名古屋","岐阜","大垣","豊橋","四日市",
    "松阪","奈良","向日町（京都向日町）","岸和田","和歌山","玉野","広島","防府","高松",
    "小松島","高知","松山","佐世保","久留米","小倉","別府","熊本","武雄","青森","函館",
    "福井","富山"
]))

# 券種プリセット
BET_TYPES = ["二車複", "ワイド", "三連複", "二車単", "三連単"]

# =========================
# ユーティリティ
# =========================
def _safe_numeric(s, kind="int"):
    if kind == "int":
        return pd.to_numeric(s, errors="coerce").fillna(0).astype("int64")
    if kind == "float":
        return pd.to_numeric(s, errors="coerce")
    raise ValueError("kind must be 'int' or 'float'")

def _str_strip(s):
    return s.astype(str).str.strip()

def load_df() -> pd.DataFrame:
    if CSV_PATH.exists():
        df = pd.read_csv(CSV_PATH, dtype=str)
    else:
        df = pd.DataFrame(columns=COLUMNS, dtype=object)

    # 欠損列補完
    for c in COLUMNS:
        if c not in df.columns:
            df[c] = "" if c not in ["ID", "投資", "払戻", "オッズ", "的中"] else 0

    # 型整形
    df["ID"]   = _safe_numeric(df["ID"], "int")
    df["投資"] = _safe_numeric(df["投資"], "int")
    df["払戻"] = _safe_numeric(df["払戻"], "int")
    df["オッズ"] = _safe_numeric(df["オッズ"], "float")
    df["的中"] = _safe_numeric(df["的中"], "int")
    df["的中"] = np.where(df["払戻"] > 0, 1, df["的中"])

    for c in ["日付", "場", "R", "券種", "買い目"]:
        df[c] = _str_strip(df[c])

    # ID採番
    if (df["ID"] == 0).any():
        max_id = int(df["ID"].max()) if len(df) else 0
        need = df["ID"] == 0
        cnt = int(need.sum())
        df.loc[need, "ID"] = range(max_id + 1, max_id + 1 + cnt)

    df = df[COLUMNS].copy()
    return df

def save_df(df: pd.DataFrame) -> None:
    out = df.copy()
    out["ID"]   = _safe_numeric(out["ID"], "int")
    out["投資"] = _safe_numeric(out["投資"], "int")
    out["払戻"] = _safe_numeric(out["払戻"], "int")
    out["オッズ"] = _safe_numeric(out["オッズ"], "float")
    out["的中"] = _safe_numeric(out["的中"], "int")
    out.to_csv(CSV_PATH, index=False)

def next_id(df: pd.DataFrame) -> int:
    return int(df["ID"].max()) + 1 if len(df) else 1

def get_date_bounds(df: pd.DataFrame):
    try:
        if len(df) == 0 or (df["日付"] == "").all():
            today = pd.to_datetime(date.today())
            return today, today
        s = pd.to_datetime(df.loc[df["日付"] != "", "日付"], errors="coerce").dropna()
        if len(s) == 0:
            today = pd.to_datetime(date.today())
            return today, today
        return s.min(), s.max()
    except Exception:
        today = pd.to_datetime(date.today())
        return today, today

# =========================
# データ読み込み
# =========================
df = load_df()
st.title("競輪ログ（手入力・編集・削除・会場プリセット）")

# =========================
# 1) 手入力で追加
# =========================
with st.form("manual_input_form", clear_on_submit=True):
    st.subheader("1) レースを追加（手入力）")
    col1, col2, col3 = st.columns(3)
    with col1:
        in_date = st.date_input("日付", value=date.today())

        venue_choice = st.selectbox("場（プリセット）", ["手入力に切替"] + VENUES, index=0)
        if venue_choice == "手入力に切替":
            in_place = st.text_input("場（自由入力）", value="", placeholder="例：岸和田")
        else:
            in_place = venue_choice

        in_r = st.text_input("R（数字）", value="", placeholder="例：4")

    with col2:
        in_kind = st.selectbox("券種", BET_TYPES, index=0)
        in_comb = st.text_input("買い目", value="", placeholder="例：1-7 / 1-6 / 1-7-2")
        default_map = {"ワイド":100, "二車複":200, "二車単":200, "三連複":300, "三連単":300}
        default_stake = default_map.get(in_kind, 100)
        in_stake = st.number_input("投資(円)", min_value=0, max_value=1_000_000, value=default_stake, step=100)

    with col3:
        in_pay = st.number_input("払戻(円)", min_value=0, max_value=10_000_000, value=0, step=100)
        in_odds = st.text_input("オッズ（任意）", value="", placeholder="例：8.9")

    submitted = st.form_submit_button("追加")
    if submitted:
        try:
            if not str(in_place).strip():
                st.error("「場」を入力してください。")
            elif not str(in_r).strip().isdigit():
                st.error("「R」は数字で入力してください。")
            elif not str(in_comb).strip():
                st.error("「買い目」を入力してください。")
            else:
                row = {
                    "ID": next_id(df),
                    "日付": str(in_date),
                    "場": str(in_place).strip(),
                    "R": str(in_r).strip(),
                    "券種": in_kind,
                    "買い目": str(in_comb).strip(),
                    "投資": int(in_stake),
                    "払戻": int(in_pay),
                    "オッズ": (float(in_odds) if str(in_odds).strip() != "" else np.nan),
                    "的中": 1 if int(in_pay) > 0 else 0,
                }
                df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
                save_df(df)
                st.success("追加しました。")
        except Exception as e:
            st.error(f"追加に失敗しました：{e}")

# =========================
# 2) 集計メトリクス
# =========================
if len(df) == 0:
    st.info("まだデータがありません。上のフォームから追加してください。")
else:
    # 再整形（環境差対策）
    df["投資"] = _safe_numeric(df["投資"], "int")
    df["払戻"] = _safe_numeric(df["払戻"], "int")
    df["オッズ"] = _safe_numeric(df["オッズ"], "float")
    df["的中"] = _safe_numeric(df["的中"], "int")

    total_bet = int(df["投資"].sum())
    total_ret = int(df["払戻"].sum())
    hits      = int(df["的中"].sum())
    trials    = int(len(df))
    roi = (total_ret / total_bet * 100.0) if total_bet > 0 else 0.0

    colA, colB, colC, colD = st.columns(4)
    colA.metric("累計 投資", f"{total_bet:,} 円")
    colB.metric("累計 払戻", f"{total_ret:,} 円")
    colC.metric("累計 回収率", f"{roi:.2f} %")
    colD.metric("的中数 / レース", f"{hits}/{trials}")

    # =========================
    # 3) 券種別集計
    # =========================
    st.subheader("2) 券種別集計")
    try:
        by_kind = df.groupby("券種", dropna=False).agg(
            投資=("投資", "sum"),
            払戻=("払戻", "sum"),
            的中=("的中", "sum"),
            本数=("買い目", "count"),
        ).reset_index()
        by_kind["投資"] = _safe_numeric(by_kind["投資"], "int")
        by_kind["払戻"] = _safe_numeric(by_kind["払戻"], "int")
        by_kind["回収率%"] = np.where(
            by_kind["投資"] > 0,
            (by_kind["払戻"] / by_kind["投資"] * 100).round(2),
            0.0,
        )
        by_kind["的中率%"] = np.where(
            by_kind["本数"] > 0,
            (by_kind["的中"] / by_kind["本数"] * 100).round(2),
            0.0
        )
        st.dataframe(by_kind, use_container_width=True)
    except Exception as e:
        st.warning(f"券種別集計で問題: {e}")

    # =========================
    # 4) 明細（期間・券種・会場でフィルタ）
    # =========================
    st.subheader("3) 明細（期間・券種・会場でフィルタ）")
    # 日付境界の取得を安全化
    try:
        dmin, dmax = get_date_bounds(df)
        dmin = dmin.to_pydatetime().date()
        dmax = dmax.to_pydatetime().date()
    except Exception as e:
        st.warning(f"日付境界の取得に失敗: {e}。本日で代替します。")
        dmin = dmax = date.today()

    with st.expander("フィルタ", expanded=True):
        colx, coly = st.columns(2)
        with colx:
            try:
                date_from = st.date_input("日付From", value=dmin)
            except Exception:
                date_from = dmin
                st.warning("日付Fromの初期化に問題がありました。")
        with coly:
            try:
                date_to = st.date_input("日付To", value=dmax)
            except Exception:
                date_to = dmax
                st.warning("日付Toの初期化に問題がありました。")

        st.write("券種フィルタ（OFFで除外）")
        kind_checks = {k: st.checkbox(k, value=True) for k in BET_TYPES}

        st.write("会場フィルタ（選択が空なら全件）")
        venue_selected = st.multiselect("会場を選択", options=VENUES, default=[])

    q = df.copy()
    try:
        q = q[(q["日付"] >= str(date_from)) & (q["日付"] <= str(date_to))]
    except Exception as e:
        st.warning(f"日付フィルタで問題: {e}（全期間で表示）")

    kinds_on = [k for k, v in kind_checks.items() if v]
    if kinds_on:
        q = q[q["券種"].isin(kinds_on)]
    if len(venue_selected) > 0:
        q = q[q["場"].isin(venue_selected)]

    try:
        q["行回収率%"] = np.where(
            pd.to_numeric(q["投資"], errors="coerce").fillna(0) > 0,
            (pd.to_numeric(q["払戻"], errors="coerce").fillna(0) /
             np.where(pd.to_numeric(q["投資"], errors="coerce").fillna(0)==0, 1,
                      pd.to_numeric(q["投資"], errors="coerce").fillna(0)) * 100).round(2),
            0.0
        )
    except Exception as e:
        st.warning(f"行回収率の計算で問題: {e}（列を0で表示）")
        q["行回収率%"] = 0.0

    q = q.sort_values(["日付", "場", "R", "ID"]).reset_index(drop=True)
    st.dataframe(q, use_container_width=True)

    # =========================
    # 3.5) 会場別 × 券種 集計（フィルタ結果に連動）
    # =========================
    st.subheader("3.5) 会場別 × 券種 集計")
    try:
        base = q.copy()
        base["投資"] = pd.to_numeric(base["投資"], errors="coerce").fillna(0).astype(int)
        base["払戻"] = pd.to_numeric(base["払戻"], errors="coerce").fillna(0).astype(int)
        base["的中"] = pd.to_numeric(base["的中"], errors="coerce").fillna(0).astype(int)

        if len(base) == 0:
            st.info("フィルタ結果が空です。データを追加するかフィルタを緩めてください。")
        else:
            by_place_kind = base.groupby(["場","券種"], dropna=False).agg(
                投資=("投資","sum"), 払戻=("払戻","sum"), 的中=("的中","sum"), 本数=("買い目","count")
            ).reset_index()
            by_place_kind["回収率%"] = np.where(
                by_place_kind["投資"]>0,
                (by_place_kind["払戻"]/by_place_kind["投資"]*100).round(2),
                0.0
            )
            by_place_kind["的中率%"] = np.where(
                by_place_kind["本数"]>0,
                (by_place_kind["的中"]/by_place_kind["本数"]*100).round(2),
                0.0
            )
            st.markdown("**会場×券種（ロングテーブル）**")
            st.dataframe(
                by_place_kind.sort_values(["回収率%","本数"], ascending=[False,False]),
                use_container_width=True,
            )

            # 横持ち
            try:
                pv = by_place_kind.pivot_table(
                    index="場",
                    columns="券種",
                    values=["投資","払戻","回収率%","的中率%"],
                    aggfunc="first"
                ).fillna(0)

                tot_place = base.groupby("場", dropna=False).agg(
                    総投資=("投資","sum"), 総払戻=("払戻","sum")
                ).reset_index()
                tot_place["総回収率%"] = np.where(
                    tot_place["総投資"]>0,
                    (tot_place["総払戻"]/tot_place["総投資"]*100).round(2),
                    0.0
                )
                pv = pv.merge(tot_place[["場","総投資","総払戻","総回収率%"]], on="場", how="left")
                pv = pv.sort_values("総回収率%", ascending=False)
                st.markdown("**会場ごとの券種別指標（横持ち）**")
                st.dataframe(pv, use_container_width=True)
            except Exception as e:
                st.warning(f"横持ちビューの生成で問題: {e}（ロングのみ表示）")
    except Exception as e:
        st.error(f"会場×券種の集計処理でエラー: {e}")

    # =========================
    # 5) 既存データの編集（直接書き換え → 保存）
    # =========================
    st.subheader("4) 既存データの編集（直接書き換え → 保存）")
    try:
        edit_view = df.copy().sort_values(["日付","場","R","ID"]).reset_index(drop=True)
        # 一部のStreamlitバージョンでSelectboxColumnが不調なことがあるためtryで囲む
        try:
            col_config = {
                "ID": st.column_config.NumberColumn("ID", help="永続ID（できるだけ編集しない）"),
                "投資": st.column_config.NumberColumn("投資", step=100),
                "払戻": st.column_config.NumberColumn("払戻", step=100),
                "オッズ": st.column_config.NumberColumn("オッズ", step=0.1),
                "的中": st.column_config.NumberColumn("的中", help="0/1。払戻>0なら保存時に1へ更新"),
                "券種": st.column_config.SelectboxColumn("券種", options=BET_TYPES),
            }
        except Exception:
            col_config = {
                "ID": st.column_config.NumberColumn("ID", help="永続ID（できるだけ編集しない）"),
                "投資": st.column_config.NumberColumn("投資", step=100),
                "払戻": st.column_config.NumberColumn("払戻", step=100),
                "オッズ": st.column_config.NumberColumn("オッズ", step=0.1),
                "的中": st.column_config.NumberColumn("的中", help="0/1。払戻>0なら保存時に1へ更新"),
            }

        edited = st.data_editor(
            edit_view,
            use_container_width=True,
            num_rows="fixed",
            column_config=col_config,
            key="editor_full",
        )

        if st.button("編集内容を保存"):
            edited["ID"]   = _safe_numeric(edited["ID"], "int")
            edited["投資"] = _safe_numeric(edited["投資"], "int")
            edited["払戻"] = _safe_numeric(edited["払戻"], "int")
            edited["オッズ"] = _safe_numeric(edited["オッズ"], "float")
            edited["的中"] = _safe_numeric(edited["的中"], "int")
            edited["的中"] = np.where(edited["払戻"] > 0, 1, edited["的中"])
            for c in ["日付","場","R","券種","買い目"]:
                edited[c] = _str_strip(edited[c])
            save_df(edited)
            st.success("保存しました。画面を更新してください。")
    except Exception as e:
        st.warning(f"編集テーブルで問題: {e}（編集機能を一時停止）")

    # =========================
    # 6) 複数行の削除（チェック → 削除）
    # =========================
    st.subheader("5) 複数行の削除（チェックして削除）")
    try:
        show = df.copy().sort_values(["日付","場","R","ID"]).reset_index(drop=True)
        show["削除"] = False
        del_table = st._
