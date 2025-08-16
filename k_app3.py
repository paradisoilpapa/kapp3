# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import numpy as np
from datetime import date
from pathlib import Path

# ============ 基本設定 ============
st.set_page_config(page_title="競輪ログ（手入力・編集保存・複数削除・会場プリセット）", layout="centered")
CSV_PATH = Path("keirin_logs.csv")
COLUMNS = ["ID","日付","場","R","券種","買い目","投資","払戻","オッズ","的中"]

VENUES = sorted(set([
    "いわき平","京王閣","取手","宇都宮","前橋","西武園","大宮","弥彦","松戸","千葉",
    "川崎","平塚","小田原","伊東温泉","静岡","名古屋","岐阜","大垣","豊橋","四日市",
    "松阪","奈良","向日町（京都向日町）","岸和田","和歌山","玉野","広島","防府","高松",
    "小松島","高知","松山","佐世保","久留米","小倉","別府","熊本","武雄","青森","函館",
    "福井","富山"
]))
BET_TYPES = ["二車複","ワイド","三連複","二車単","三連単"]

# ============ ユーティリティ ============
def _safe_numeric(s, kind="int"):
    if kind == "int":
        return pd.to_numeric(s, errors="coerce").fillna(0).astype("int64")
    if kind == "float":
        return pd.to_numeric(s, errors="coerce")
    raise ValueError

def _str_strip(s):
    return s.astype(str).str.strip()

def load_df()->pd.DataFrame:
    if CSV_PATH.exists():
        df = pd.read_csv(CSV_PATH, dtype=str)
    else:
        df = pd.DataFrame(columns=COLUMNS, dtype=object)
    for c in COLUMNS:
        if c not in df.columns:
            df[c] = "" if c not in ["ID","投資","払戻","オッズ","的中"] else 0

    df["ID"]   = _safe_numeric(df["ID"], "int")
    df["投資"] = _safe_numeric(df["投資"], "int")
    df["払戻"] = _safe_numeric(df["払戻"], "int")
    df["オッズ"]= _safe_numeric(df["オッズ"],"float")
    df["的中"] = _safe_numeric(df["的中"], "int")
    df["的中"] = np.where(df["払戻"]>0, 1, df["的中"])
    for c in ["日付","場","R","券種","買い目"]:
        df[c] = _str_strip(df[c])

    # ID振り直し（0が残っていたら採番）
    if (df["ID"]==0).any():
        mx = int(df["ID"].max()) if len(df) else 0
        need = df["ID"]==0
        cnt = int(need.sum())
        df.loc[need,"ID"] = range(mx+1, mx+1+cnt)

    # ID重複があればユニーク化
    if df["ID"].duplicated().any():
        used = set()
        cur_max = int(df["ID"].max()) if len(df) else 0
        ids = []
        for v in df["ID"]:
            v = int(v)
            if v in used:
                cur_max += 1
                ids.append(cur_max)
            else:
                ids.append(v); used.add(v)
        df["ID"] = ids

    return df[COLUMNS].copy()

def save_df(df:pd.DataFrame):
    out = df.copy()
    out["ID"]=_safe_numeric(out["ID"],"int")
    out["投資"]=_safe_numeric(out["投資"],"int")
    out["払戻"]=_safe_numeric(out["払戻"],"int")
    out["オッズ"]=_safe_numeric(out["オッズ"],"float")
    out["的中"]=_safe_numeric(out["的中"],"int")
    out.to_csv(CSV_PATH, index=False)

def next_id(df:pd.DataFrame)->int:
    return int(df["ID"].max())+1 if len(df) else 1

def get_date_bounds(df:pd.DataFrame):
    if len(df)==0 or (df["日付"]=="").all():
        t=pd.to_datetime(date.today()); return t,t
    s=pd.to_datetime(df.loc[df["日付"]!="","日付"], errors="coerce").dropna()
    if len(s)==0:
        t=pd.to_datetime(date.today()); return t,t
    return s.min(), s.max()

# ============ データ ============
df = load_df()
st.title("競輪ログ（手入力・編集保存・複数削除・会場プリセット）")

# ============ 1) 手入力追加 ============
with st.form("manual_input", clear_on_submit=True):
    st.subheader("1) レースを追加（手入力）")
    c1,c2,c3 = st.columns(3)
    with c1:
        in_date = st.date_input("日付", value=date.today())
        venue_choice = st.selectbox("場（プリセット）", ["手入力に切替"]+VENUES, index=0)
        in_place = st.text_input("場（自由入力）", "") if venue_choice=="手入力に切替" else venue_choice
        in_r = st.text_input("R（数字）", "", placeholder="例：4")
    with c2:
        in_kind = st.selectbox("券種", BET_TYPES, index=0)
        in_comb = st.text_input("買い目", "", placeholder="例：1-7 / 1-6 / 1-7-2")
        default_map={"ワイド":100,"二車複":200,"二車単":200,"三連複":300,"三連単":300}
        in_stake = st.number_input("投資(円)", 0, 1_000_000, default_map.get(in_kind,100), 100)
    with c3:
        in_pay = st.number_input("払戻(円)", 0, 10_000_000, 0, 100)
        in_odds = st.text_input("オッズ（任意）", "", placeholder="例：8.9")
    if st.form_submit_button("追加"):
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
                "オッズ": (float(in_odds) if str(in_odds).strip()!="" else np.nan),
                "的中": 1 if int(in_pay)>0 else 0,
            }
            df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
            save_df(df)
            st.success("追加しました。")

# ============ 2) 総合メトリクス ============
if len(df)==0:
    st.info("まだデータがありません。上のフォームから追加してください。")
else:
    df["投資"]=_safe_numeric(df["投資"],"int")
    df["払戻"]=_safe_numeric(df["払戻"],"int")
    df["オッズ"]=_safe_numeric(df["オッズ"],"float")
    df["的中"]=_safe_numeric(df["的中"],"int")

    total_bet=int(df["投資"].sum())
    total_ret=int(df["払戻"].sum())
    hits=int(df["的中"].sum())
    trials=len(df)
    roi=(total_ret/total_bet*100.0) if total_bet>0 else 0.0

    a,b,c,d=st.columns(4)
    a.metric("累計 投資", f"{total_bet:,} 円")
    b.metric("累計 払戻", f"{total_ret:,} 円")
    c.metric("累計 回収率", f"{roi:.2f} %")
    d.metric("的中数 / レース", f"{hits}/{trials}")

    # -------- 3) 券種別集計 --------
    st.subheader("2) 券種別集計")
    by_kind=df.groupby("券種", dropna=False).agg(
        投資=("投資","sum"), 払戻=("払戻","sum"), 的中=("的中","sum"), 本数=("買い目","count")
    ).reset_index()
    by_kind["回収率%"]=np.where(by_kind["投資"]>0,(by_kind["払戻"]/by_kind["投資"]*100).round(2),0.0)
    by_kind["的中率%"]=np.where(by_kind["本数"]>0,(by_kind["的中"]/by_kind["本数"]*100).round(2),0.0)
    st.dataframe(by_kind, use_container_width=True)

    # -------- 4) 明細（期間・券種・会場でフィルタ） --------
    st.subheader("3) 明細（期間・券種・会場でフィルタ）")
    dmin,dmax=get_date_bounds(df)
    dmin=dmin.to_pydatetime().date(); dmax=dmax.to_pydatetime().date()
    with st.expander("フィルタ", expanded=True):
        x,y=st.columns(2)
        with x:
            date_from=st.date_input("日付From", value=dmin)
        with y:
            date_to=st.date_input("日付To", value=dmax)
        st.write("券種フィルタ（OFFで除外）")
        kind_checks={k: st.checkbox(k, value=True) for k in BET_TYPES}
        st.write("会場フィルタ（選択が空なら全件）")
        venue_selected=st.multiselect("会場を選択", options=VENUES, default=[])
    q=df.copy()
    q=q[(q["日付"]>=str(date_from))&(q["日付"]<=str(date_to))]
    kinds_on=[k for k,v in kind_checks.items() if v]
    if kinds_on: q=q[q["券種"].isin(kinds_on)]
    if len(venue_selected)>0: q=q[q["場"].isin(venue_selected)]
    q["行回収率%"]=np.where(
        _safe_numeric(q["投資"],"int")>0,
        (_safe_numeric(q["払戻"],"int")/np.where(_safe_numeric(q["投資"],"int")==0,1,_safe_numeric(q["投資"],"int"))*100).round(2),
        0.0
    )
    q=q.sort_values(["日付","場","R","ID"]).reset_index(drop=True)
    st.dataframe(q, use_container_width=True)

    # -------- 3.5) 会場別 × 券種 集計（フィルタ結果） --------
    st.subheader("3.5) 会場別 × 券種 集計")
    base=q.copy()
    base["場"]=base["場"].astype(str).str.strip().replace({"":"不明"})
    base["券種"]=base["券種"].astype(str).str.strip()
    base["投資"]=_safe_numeric(base["投資"],"int")
    base["払戻"]=_safe_numeric(base["払戻"],"int")
    base["的中"]=_safe_numeric(base["的中"],"int")

    if len(base)==0:
        st.info("フィルタ結果が空です。")
    else:
        by_place_kind=base.groupby(["場","券種"], dropna=False).agg(
            投資=("投資","sum"), 払戻=("払戻","sum"), 的中=("的中","sum"), 本数=("買い目","count")
        ).reset_index()
        by_place_kind["回収率%"]=np.where(by_place_kind["投資"]>0,(by_place_kind["払戻"]/by_place_kind["投資"]*100).round(2),0.0)
        by_place_kind["的中率%"]=np.where(by_place_kind["本数"]>0,(by_place_kind["的中"]/by_place_kind["本数"]*100).round(2),0.0)
        st.markdown("**会場×券種（ロングテーブル）**")
        st.dataframe(by_place_kind.sort_values(["回収率%","本数"], ascending=[False,False]), use_container_width=True)

        st.markdown("**会場ごとの券種別指標（横持ち）**")
        pv=by_place_kind.pivot_table(
            index="場", columns="券種",
            values=["投資","払戻","回収率%","的中率%"],
            aggfunc="first", observed=False
        ).fillna(0)

        # ←← ここから安全化（KeyError対策） →→
        # インデックス名がNoneでも '場' 列として復元
        if pv.index.name is None:
            pv.index.name = "場"
        pv = pv.rename_axis(index="場").reset_index()

        # MultiIndex列をフラット化
        def _flat(cols):
            out=[]
            for c in cols:
                if isinstance(c, tuple): out.append(f"{c[0]}_{c[1]}")
                else: out.append(str(c))
            return out
        pv.columns=_flat(pv.columns)

        # まれに '場' 列名が 'index' や 'level_0' になる環境がある → 強制リネーム
        if "場" not in pv.columns:
            for cand in ["index","level_0"]:
                if cand in pv.columns:
                    pv.rename(columns={cand:"場"}, inplace=True)
                    break

        pv["場"]=pv["場"].astype(str)

        # トータルは map で安全に付与（merge 不使用）
        tot=base.groupby("場", dropna=False).agg(総投資=("投資","sum"), 総払戻=("払戻","sum")).reset_index()
        tot["総回収率%"]=np.where(tot["総投資"]>0,(tot["総払戻"]/tot["総投資"]*100).round(2),0.0)
        idx=tot.set_index("場")
        pv["総投資"]=pv["場"].map(idx["総投資"]).fillna(0)
        pv["総払戻"]=pv["場"].map(idx["総払戻"]).fillna(0)
        pv["総回収率%"]=pv["場"].map(idx["総回収率%"]).fillna(0)
        pv=pv.sort_values("総回収率%", ascending=False)
        # ←← ここまで安全化 →→

        st.dataframe(pv, use_container_width=True)

    # -------- 5) 既存データの編集（表で直接 → 保存） --------
    st.subheader("4) 既存データの編集（直接書き換え → 保存）")
    edit_view=df.copy().sort_values(["日付","場","R","ID"]).reset_index(drop=True)
    try:
        col_config={
            "ID": st.column_config.NumberColumn("ID", help="永続ID（基本は編集しない）"),
            "投資": st.column_config.NumberColumn("投資", step=100),
            "払戻": st.column_config.NumberColumn("払戻", step=100),
            "オッズ": st.column_config.NumberColumn("オッズ", step=0.1),
            "的中": st.column_config.NumberColumn("的中", help="0/1。払戻>0なら保存時に1へ更新"),
            "券種": st.column_config.SelectboxColumn("券種", options=BET_TYPES),
        }
    except Exception:
        col_config={
            "ID": st.column_config.NumberColumn("ID", help="永続ID（基本は編集しない）"),
            "投資": st.column_config.NumberColumn("投資", step=100),
            "払戻": st.column_config.NumberColumn("払戻", step=100),
            "オッズ": st.column_config.NumberColumn("オッズ", step=0.1),
            "的中": st.column_config.NumberColumn("的中", help="0/1。払戻>0なら保存時に1へ更新"),
        }
    edited=st.data_editor(
        edit_view, use_container_width=True, num_rows="fixed",
        column_config=col_config, key="editor_full",
    )
    if st.button("編集内容を保存"):
        edited["ID"]=_safe_numeric(edited["ID"],"int")
        edited["投資"]=_safe_numeric(edited["投資"],"int")
        edited["払戻"]=_safe_numeric(edited["払戻"],"int")
        edited["オッズ"]=_safe_numeric(edited["オッズ"],"float")
        edited["的中"]=_safe_numeric(edited["的中"],"int")
        edited["的中"]=np.where(edited["払戻"]>0,1,edited["的中"])
        for c in ["日付","場","R","券種","買い目"]:
            edited[c]=_str_strip(edited[c])
        save_df(edited)
        st.success("保存しました。画面を更新してください。")

    # -------- 6) 複数行削除（チェック → 削除） --------
    st.subheader("5) 複数行の削除（チェックして削除）")
    show=df.copy().sort_values(["日付","場","R","ID"]).reset_index(drop=True)
    show["削除"]=False
    del_table=st.data_editor(
        show[["削除","ID","日付","場","R","券種","買い目","投資","払戻","オッズ","的中"]],
        use_container_width=True, num_rows="fixed",
        column_config={
            "削除": st.column_config.CheckboxColumn("削除", help="削除したい行にチェック"),
            "ID": st.column_config.NumberColumn("ID", help="永続ID", disabled=True),
        },
        key="editor_delete",
    )

    if st.button("チェックした行を削除"):
        # ← 型違いで消えない問題を根絶（int64に強制）
        del_ids = pd.to_numeric(
            del_table.loc[del_table["削除"]==True, "ID"], errors="coerce"
        ).dropna().astype("int64").tolist()

        if len(del_ids)==0:
            st.warning("削除対象が選ばれていません。")
        else:
            df["ID"] = _safe_numeric(df["ID"], "int")  # 念のため
            df = df[~df["ID"].isin(del_ids)].copy()
            save_df(df)
            st.success(f"{len(del_ids)} 行を削除しました。")
            st.rerun()
