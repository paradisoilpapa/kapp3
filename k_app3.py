import streamlit as st
import pandas as pd

st.set_page_config(page_title="競輪ログ（手入力・編集・削除・会場プリセット）", layout="centered")

# --- セッション状態の初期化 ---
if "races" not in st.session_state:
    st.session_state["races"] = []

# --- 会場プリセット ---
venues = [
    "いわき平", "大宮", "取手", "前橋", "宇都宮", "松戸", "千葉", "川崎", "平塚", "小田原",
    "伊東温泉", "静岡", "名古屋", "岐阜", "大垣", "豊橋", "富山", "松阪", "四日市", "奈良",
    "向日町", "和歌山", "岸和田", "玉野", "高松", "小松島", "高知", "松山", "防府", "広島",
    "周防", "山口", "久留米", "別府", "熊本", "佐世保", "長崎", "武雄", "若松", "小倉"
]

# --- 入力フォーム ---
st.header("1) レースを追加（手入力）")
with st.form("add_race"):
    date = st.date_input("日付")
    venue = st.selectbox("場（プリセット）", ["手入力に切替"] + venues)
    if venue == "手入力に切替":
        venue = st.text_input("場（手入力）")

    race_no = st.text_input("R（数字）", placeholder="例：4")
    kind = st.selectbox("券種", ["二車複", "ワイド", "三連複", "三連単", "二車単"])
    investment = st.number_input("投資(円)", min_value=100, step=100, value=100)
    payout = st.number_input("払戻(円)", min_value=0, step=100, value=0)
    odds = st.text_input("オッズ（任意）", placeholder="例：8.9")
    buy = st.text_input("買い目", placeholder="例：1-7/1-6/1-7-2")

    submitted = st.form_submit_button("追加")
    if submitted:
        st.session_state["races"].append({
            "日付": str(date),
            "場": venue,
            "R": race_no,
            "券種": kind,
            "投資": int(investment),
            "払戻": int(payout),
            "オッズ": odds,
            "買い目": buy
        })
        st.success("追加しました。")

# --- DataFrameに変換 ---
df = pd.DataFrame(st.session_state["races"])

if not df.empty:
    st.write("### 2) 登録データ一覧")
    st.dataframe(df)

    # --- 削除機能 ---
    st.write("### 3) レース削除")
    del_index = st.number_input("削除したい行番号を入力（0 から）", min_value=0, max_value=len(df)-1, step=1)
    if st.button("削除実行"):
        st.session_state["races"].pop(del_index)
        st.success(f"{del_index} 行目を削除しました。")
        st.experimental_rerun()

    # --- 集計 ---
    st.write("### 4) 集計結果")
    total_invest = df["投資"].sum()
    total_return = df["払戻"].sum()
    hit_count = (df["払戻"] > 0).sum()
    total_count = len(df)
    recovery_rate = (total_return / total_invest * 100) if total_invest > 0 else 0

    st.metric("累計 投資", f"{total_invest} 円")
    st.metric("累計 払戻", f"{total_return} 円")
    st.metric("累計 回収率", f"{recovery_rate:.2f} %")
    st.metric("的中数/レース", f"{hit_count}/{total_count}")

    # --- 会場別 & 券種別集計 ---
    st.write("### 5) 会場別 集計")
    by_venue = df.groupby("場")[["投資", "払戻"]].sum()
    by_venue["回収率%"] = (by_venue["払戻"] / by_venue["投資"] * 100).round(2)
    st.dataframe(by_venue)

    st.write("### 6) 券種別 集計")
    by_kind = df.groupby("券種")[["投資", "払戻"]].sum()
    by_kind["回収率%"] = (by_kind["払戻"] / by_kind["投資"] * 100).round(2)
    st.dataframe(by_kind)

else:
    st.info("まだデータがありません。")

