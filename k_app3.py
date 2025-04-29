import streamlit as st
import pandas as pd

st.title("ライン競輪スコア計算（7車ライン＋政春補正＋風向風速隊列完全対応版）")

# --- 入力UI ---
kakushitsu_options = ['逃', '両', '追']
symbol_input_options = ['◎', '〇', '▲', '△', '×', '無']

st.header("【脚質入力】")
kakushitsu = [st.selectbox(f"{i+1}番脚質", kakushitsu_options, key=f"kaku_{i}") for i in range(7)]

st.header("【前走着順入力（1〜7着）】")
chaku = [st.number_input(f"{i+1}番着順", min_value=1, max_value=7, value=4, step=1, key=f"chaku_{i}") for i in range(7)]

st.header("【競争得点入力】")
rating = [st.number_input(f"{i+1}番得点", value=55.0, step=0.1, key=f"rate_{i}") for i in range(7)]

st.header("【隊列予想（数字、欠の場合は空欄）】")
tairetsu = [st.text_input(f"{i+1}番隊列順位", key=f"tai_{i}") for i in range(7)]

st.header("【ラインポジション入力（0単騎 1先頭 2番手 3三番手）】")
line_order = [st.selectbox(f"{i+1}番ラインポジション", [0, 1, 2, 3], key=f"line_{i}") for i in range(7)]

st.header("【政春印入力】")
symbol = [st.selectbox(f"{i+1}番印", symbol_input_options, key=f"sym_{i}") for i in range(7)]

st.header("【バンク・風条件】")
st.markdown("### ホーム（上）- バック（下） 配置")
wind_cols_top = st.columns(3)
wind_cols_middle = st.columns(3)
wind_cols_bottom = st.columns(3)

if "selected_wind" not in st.session_state:
    st.session_state.selected_wind = None

with wind_cols_top[0]:
    if st.button("左上"):
        st.session_state.selected_wind = "左上"
with wind_cols_top[1]:
    if st.button("上"):
        st.session_state.selected_wind = "上"
with wind_cols_top[2]:
    if st.button("右上"):
        st.session_state.selected_wind = "右上"

with wind_cols_middle[0]:
    if st.button("左"):
        st.session_state.selected_wind = "左"
with wind_cols_middle[1]:
    st.markdown("中央")
with wind_cols_middle[2]:
    if st.button("右"):
        st.session_state.selected_wind = "右"

with wind_cols_bottom[0]:
    if st.button("左下"):
        st.session_state.selected_wind = "左下"
with wind_cols_bottom[1]:
    if st.button("下"):
        st.session_state.selected_wind = "下"
with wind_cols_bottom[2]:
    if st.button("右下"):
        st.session_state.selected_wind = "右下"

wind_speed = st.number_input("風速(m/s)", min_value=0.0, max_value=10.0, step=0.1)
straight_length = st.number_input("みなし直線(m)", min_value=30, max_value=80, value=52, step=1)
bank_angle = st.number_input("バンク角(°)", min_value=20.0, max_value=45.0, value=30.0, step=0.1)
rain = st.checkbox("雨（滑走・慎重傾向あり）")

# --- 補正設定（横風は中立0.0に修正！） ---
wind_coefficients = {
    "左上": 0.7,
    "上": 1.0,
    "右上": 0.7,
    "左": 0.0,  # 横風は中立！
    "右": 0.0,  # 横風は中立！
    "左下": -0.7,
    "下": -1.0,
    "右下": -0.7
}

position_multipliers = {
    0: 1.2,  # 単騎
    1: 1.0,  # 先頭
    2: 0.3,  # 2番手
    3: 0.1   # 3番手
}

symbol_bonus = {'◎': 2.0, '〇': 1.5, '▲': 1.0, '△': 0.5, '×': 0.2, '無': 0.0}
base_score = {'逃': 8, '両': 6, '追': 5}

# --- 補正関数 ---
def score_from_chakujun(pos):
    if pos == 1:
        return -3.0
    elif pos == 2:
        return -2.0
    elif pos == 3:
        return -1.0
    elif pos == 4:
        return 0.0
    elif pos == 5:
        return 3.0
    elif pos == 6:
        return 2.0
    elif pos == 7:
        return 1.0
    else:
        return 0.0

def score_from_rating(rank):
    if rank == 1:
        return -3.0
    elif rank == 2:
        return -2.0
    elif rank == 3:
        return -1.0
    elif rank == 4:
        return 0.0
    elif rank == 5:
        return 3.0
    elif rank == 6:
        return 2.0
    elif rank == 7:
        return 1.0
    else:
        return 0.0

def line_member_bonus(pos):
    return {0: -1.0, 1: 2.0, 2: 1.5, 3: 1.0}.get(pos, 0.0)

def bank_character_bonus(kaku, angle, straight):
    if straight <= 50 and angle >= 32:
        return {'逃': 1.0, '両': 0, '追': -1.0}[kaku]
    elif straight >= 58 and angle <= 31:
        return {'逃': -1.0, '両': 0, '追': 1.0}[kaku]
    return 0.0

# --- スコア計算 ---
if st.button("スコア計算実行"):

    tairetsu_list = [i+1 for i, v in enumerate(tairetsu) if v.isdigit()]
    sorted_ratings = sorted([(i, rating[i]) for i in range(7)], key=lambda x: x[1], reverse=True)
    rating_rank = {num: rank+1 for rank, (num, _) in enumerate(sorted_ratings)}

    score_parts = []

    for i in range(7):
        if not tairetsu[i].isdigit():
            continue
        num = i + 1

        base = base_score[kakushitsu[i]]

        # 風補正
        if st.session_state.selected_wind:
            wind_base = wind_coefficients.get(st.session_state.selected_wind, 0.0)
            wind = wind_base * wind_speed * position_multipliers.get(line_order[i], 0.0)
        else:
            wind = 0.0

        # 隊列補正
        pos_in_tairetsu = tairetsu_list.index(num)
        tai = max(0, round(3.0 - 0.5 * pos_in_tairetsu, 1))
        if kakushitsu[i] == '追' and 2 <= pos_in_tairetsu <= 4:
            tai += 1.5

        # 着順補正（4着基準）
        chakujun_corr = score_from_chakujun(chaku[i])

        # 得点補正（得点順位基準）
        rating_corr = score_from_rating(rating_rank[i])

        # 雨補正
        rain_corr = {'逃': 2.5, '両': 0.5, '追': -2.5}[kakushitsu[i]] if rain else 0

        # 政春印補正
        symb = symbol_bonus[symbol[i]]

        # ラインポジション補正
        line_bonus = line_member_bonus(line_order[i])

        # バンク特性補正
        bank_bonus = bank_character_bonus(kakushitsu[i], bank_angle, straight_length)

        # 総合スコア
        total = base + wind + tai + chakujun_corr + rating_corr + rain_corr + symb + line_bonus + bank_bonus

        score_parts.append((num, kakushitsu[i], base, wind, tai, chakujun_corr, rating_corr, rain_corr, symb, line_bonus, bank_bonus, total))

    df = pd.DataFrame(score_parts, columns=['車番', '脚質', '基本', '風補正', '隊列補正', '着順補正', '得点補正', '雨補正', '政春印補正', 'ライン補正', 'バンク補正', '合計スコア'])
    df_sorted = df.sort_values(by='合計スコア', ascending=False).reset_index(drop=True)

    st.dataframe(df_sorted)
