import streamlit as st
import pandas as pd
from datetime import date
from pathlib import Path

st.set_page_config(page_title="競輪ログ（二車複＋ワイド）", layout="centered")
CSV_PATH = Path("keirin_logs.csv")

DEFAULT_COLUMNS = ["日付","場","R","券種","買い目","投資","払戻","オッズ","的中"]
if CSV_PATH.exists():
    df = pd.read_csv(CSV_PATH, dtype=str)
    # 型整形
    for c in ["投資","払戻"]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int)
    for c in ["オッズ"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    if "的中" not in df.columns:
        df["的中"] = (df["払戻"] > 0).astype(int)
else:
    df = pd.DataFrame(columns=DEFAULT_COLUMNS)

st.title("競輪ログ（事前購入 × 二車複＋ワイド）")

with st.sidebar:
    st.markdown("### 入力ヘルパー")
    base_stake = st.number_input("固定投資(円/R) ※目安", 100, 10000, 300, 100)
    st.caption("あなたは基本300円固定（二車複100×2＋ワイド100）。")

st.markdown("#### 1) CSV貼り付け or 手入力で追加")

with st.expander("CSV貼り付け（推奨）", expanded=True):
    st.caption("形式：日付,場,R,券種,買い目,投資,払戻,オッズ 例) 2025-08-16,岸和田,4,二車複,1-7,200,0,8.9")
    csv_line = st.text_input("1行CSVを貼り付け", value="")
    if st.button("CSVを追加"):
        try:
            parts = [x.strip() for x in csv_line.split(",")]
            assert len(parts) >= 6, "項目数が足りません。"
            row = {
                "日付": parts[0],
                "場": parts[1],
                "R": parts[2],
                "券種": parts[3],
                "買い目": parts[4],
                "投資": int(parts[5]),
                "払戻": int(parts[6]) if len(parts) > 6 and parts[6] else 0,
                "オッズ": float(parts[7]) if len(parts) > 7 and parts[7] else None,
            }
            row["的中"] = 1 if row["払戻"] > 0 else 0
            df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
            df.to_csv(CSV_PATH, index=False)
            st.success("追加しました。")
        except Exception as e:
            st.error(f"追加失敗：{e}")

with st.expander("手入力で追加", expanded=False):
    col1, col2 = st.columns(2)
    with col1:
        d = st.date_input("日付", value=date.today())
        place = st.text_input("場", value="")
        rno = st.text_input("R（数字のみ）", value="")
    with col2:
        kind = st.selectbox("券種", ["二車複","ワイド","三連複"])
        comb = st.text_input("買い目（例 1-7 / 1-7-2）", value="")
        stake = st.number_input("投資(円)", 0, 10000, 300 if kind=="三連複" else (200 if kind=="二車複" else 100), 100)
    col3, col4 = st.columns(2)
    with col3:
        payoff = st.number_input("払戻(円)", 0, 1000000, 0, 100)
    with col4:
        odds = st.text_input("オッズ（任意）", value="")
    if st.button("手入力を追加"):
        try:
            row = {
                "日付": str(d),
                "場": place.strip(),
                "R": rno.strip(),
                "券種": kind,
                "買い目": comb.strip(),
                "投資": int(stake),
                "払戻": int(payoff),
                "オッズ": float(odds) if odds else None,
            }
            row["的中"] = 1 if row["払戻"] > 0 else 0
            df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
            df.to_csv(CSV_PATH, index=False)
            st.success("追加しました。")
        except Exception as e:
            st.error(f"追加失敗：{e}")

st.markdown("#### 2) 集計")

if len(df)==0:
    st.info("まだデータがありません。上でレースを追加してください。")
else:
    # 総計
    total_bet = int(df["投資"].sum())
    total_ret = int(df["払戻"].sum())
    roi = (total_ret/total_bet)*100 if total_bet>0 else 0.0
    hits = int(df["的中"].sum())
    trials = len(df)

    colA, colB, colC, colD = st.columns(4)
    colA.metric("累計 投資", f"{total_bet:,} 円")
    colB.metric("累計 払戻", f"{total_ret:,} 円")
    colC.metric("累計 回収率", f"{roi:.2f} %")
    colD.metric("的中数 / レース", f"{hits}/{trials}")

    # 券種別
    by_kind = df.groupby("券種").agg(投資=("投資","sum"), 払戻=("払戻","sum"), 的中=("的中","sum"), 本数=("買い目","count")).reset_index()
    by_kind["回収率%"] = (by_kind["払戻"]/by_kind["投資"]*100).round(2)
    st.subheader("券種別集計")
    st.dataframe(by_kind, use_container_width=True)

    # 当日/期間フィルタ
    with st.expander("期間・フィルタ"):
        colx, coly, colz = st.columns(3)
        with colx:
            date_from = st.text_input("日付From（YYYY-MM-DD）", "")
        with coly:
            date_to = st.text_input("日付To（YYYY-MM-DD）", "")
        with colz:
            kind_sel = st.multiselect("券種フィルタ", ["二車複","ワイド","三連複"], default=["二車複","ワイド"])
        q = df.copy()
        if date_from:
            q = q[q["日付"] >= date_from]
        if date_to:
            q = q[q["日付"] <= date_to]
        if kind_sel:
            q = q[q["券種"].isin(kind_sel)]
        q["行回収率%"] = (q["払戻"]/q["投資"]*100).round(2)
        st.dataframe(q.sort_values(["日付","場","R"]), use_container_width=True)

    st.caption("※ CSVはアプリと同じフォルダの keirin_logs.csv に保存されます。バックアップ推奨。")
