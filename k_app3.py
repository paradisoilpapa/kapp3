import streamlit as st
import pandas as pd

# --- ページ設定 ---
st.set_page_config(page_title="ライン競輪スコア計算（完全統一版）", layout="wide")
st.title("⭐ ライン競輪スコア計算（7車ライン＋欠番対応）⭐")

# --- 定数定義 ---
wind_coefficients = {
    "左上": -0.03, "上": -0.05, "右上": -0.035,
    "左": +0.05, "右": -0.05,
    "左下": +0.035, "下": +0.05, "右下": +0.035
}
position_multipliers = {0: 0.3, 1: 0.32, 2: 0.3, 3: 0.25, 4: 0.2}
base_score = {'逃': 4.7, '両': 4.8, '追': 5.0}

# --- 状態初期化 ---
if "selected_wind" not in st.session_state:
    st.session_state.selected_wind = "無風"

# --- UI：バンクと風条件 ---
st.header("【バンク・風条件】")
cols = st.columns(3)
for i, dir in enumerate(["左上", "上", "右上", "左", "右", "左下", "下", "右下"]):
    with cols[i % 3]:
        if st.button(dir):
            st.session_state.selected_wind = dir
st.subheader(f"✅ 選択中の風向き：{st.session_state.selected_wind}")

# ▼ 競輪場選択による自動入力
keirin_data = {
    "函館": {"bank_angle": 30.6, "straight_length": 51.3, "bank_length": 400},
    "青森": {"bank_angle": 32.3, "straight_length": 58.9, "bank_length": 400},
    "いわき平": {"bank_angle": 32.9, "straight_length": 62.7, "bank_length": 400},
    "弥彦": {"bank_angle": 32.4, "straight_length": 63.1, "bank_length": 400},
    "前橋": {"bank_angle": 36.0, "straight_length": 46.7, "bank_length": 335},
    "取手": {"bank_angle": 31.5, "straight_length": 54.8, "bank_length": 400},
    "宇都宮": {"bank_angle": 25.8, "straight_length": 63.3, "bank_length": 500},
    "大宮": {"bank_angle": 26.3, "straight_length": 66.7, "bank_length": 500},
    "西武園": {"bank_angle": 29.4, "straight_length": 47.6, "bank_length": 400},
    "京王閣": {"bank_angle": 32.2, "straight_length": 51.5, "bank_length": 400},
    "立川": {"bank_angle": 31.2, "straight_length": 58.0, "bank_length": 400},
    "松戸": {"bank_angle": 29.8, "straight_length": 38.2, "bank_length": 333},
    "川崎": {"bank_angle": 32.2, "straight_length": 58.0, "bank_length": 400},
    "平塚": {"bank_angle": 31.5, "straight_length": 54.2, "bank_length": 400},
    "小田原": {"bank_angle": 35.6, "straight_length": 36.1, "bank_length": 333},
    "伊東": {"bank_angle": 34.7, "straight_length": 46.6, "bank_length": 333},
    "静岡": {"bank_angle": 30.7, "straight_length": 56.4, "bank_length": 400},
    "名古屋": {"bank_angle": 34.0, "straight_length": 58.8, "bank_length": 400},
    "岐阜": {"bank_angle": 32.3, "straight_length": 59.3, "bank_length": 400},
    "大垣": {"bank_angle": 30.6, "straight_length": 56.0, "bank_length": 400},
    "豊橋": {"bank_angle": 33.8, "straight_length": 60.3, "bank_length": 400},
    "富山": {"bank_angle": 33.7, "straight_length": 43.0, "bank_length": 333},
    "松坂": {"bank_angle": 34.4, "straight_length": 61.5, "bank_length": 400},
    "四日市": {"bank_angle": 32.3, "straight_length": 62.4, "bank_length": 400},
    "福井": {"bank_angle": 31.5, "straight_length": 52.8, "bank_length": 400},
    "奈良": {"bank_angle": 33.4, "straight_length": 38.0, "bank_length": 333},
    "向日町": {"bank_angle": 30.5, "straight_length": 47.3, "bank_length": 400},
    "和歌山": {"bank_angle": 32.3, "straight_length": 59.9, "bank_length": 400},
    "岸和田": {"bank_angle": 30.9, "straight_length": 56.7, "bank_length": 400},
    "玉野": {"bank_angle": 30.6, "straight_length": 47.9, "bank_length": 400},
    "広島": {"bank_angle": 30.8, "straight_length": 57.9, "bank_length": 400},
    "防府": {"bank_angle": 34.7, "straight_length": 42.5, "bank_length": 333},
    "高松": {"bank_angle": 33.3, "straight_length": 54.8, "bank_length": 400},
    "小松島": {"bank_angle": 29.8, "straight_length": 55.5, "bank_length": 400},
    "高知": {"bank_angle": 24.5, "straight_length": 52.0, "bank_length": 500},
    "松山": {"bank_angle": 34.0, "straight_length": 58.6, "bank_length": 400},
    "小倉": {"bank_angle": 34.0, "straight_length": 56.9, "bank_length": 400},
    "久留米": {"bank_angle": 31.5, "straight_length": 50.7, "bank_length": 400},
    "武雄": {"bank_angle": 32.0, "straight_length": 64.4, "bank_length": 400},
    "佐世保": {"bank_angle": 31.5, "straight_length": 40.2, "bank_length": 400},
    "別府": {"bank_angle": 33.7, "straight_length": 59.9, "bank_length": 400},
    "熊本": {"bank_angle": 34.3, "straight_length": 60.3, "bank_length": 400},
    "手入力": {"bank_angle": 30.0, "straight_length": 52.0, "bank_length": 400}
}


keirin_data = {"函館": {"bank_angle": 30.6, "straight_length": 51.3, "bank_length": 400}, "手入力": {"bank_angle": 30.0, "straight_length": 52.0, "bank_length": 400}}

# --- 一括フォーム（元構成に復旧） ---
with st.form("score_form"):
    st.subheader("【バンク・風条件＋選手データ入力】")

    # ▼ 競輪場＋バンク条件
    selected_track = st.selectbox("▼ 競輪場選択（自動入力）", list(keirin_data.keys()))
    selected_info = keirin_data[selected_track]
    wind_speed = st.number_input("風速(m/s)", min_value=0.0, max_value=30.0, step=0.1, value=3.0)
    straight_length = st.number_input("みなし直線(m)", min_value=30.0, max_value=80.0, step=0.1, value=float(selected_info["straight_length"]))
    bank_angle = st.number_input("バンク角(°)", min_value=20.0, max_value=45.0, step=0.1, value=float(selected_info["bank_angle"]))
    bank_length = st.number_input("バンク周長(m)", min_value=300.0, max_value=500.0, step=0.1, value=float(selected_info["bank_length"]))
    laps = st.number_input("周回数（通常は4、高松などは5）", min_value=1, max_value=10, value=4, step=1)

    # ▼ 位置入力（逃・両・追）
    st.subheader("▼ 位置入力（逃＝先頭・両＝番手・追＝３番手以降&単騎：車番を半角数字で入力）")
    kakushitsu_keys = ['逃', '両', '追']
    kakushitsu_inputs = {}
    cols = st.columns(3)
    for i, k in enumerate(kakushitsu_keys):
        with cols[i]:
            st.markdown(f"**{k}**")
            kakushitsu_inputs[k] = st.text_input("", key=f"kaku_{k}", max_chars=14)

    car_to_kakushitsu = {}
    for k, val in kakushitsu_inputs.items():
        for c in val:
            if c.isdigit():
                n = int(c)
                if 1 <= n <= 9:
                    car_to_kakushitsu[n] = k

    st.subheader("▼ 前々走・前走の着順入力（1〜9着 または 0＝落車）")
    chaku_inputs = []
    for i in range(7):
        col1, col2 = st.columns(2)
        with col1:
            chaku1 = st.text_input(f"{i+1}番【前々走】", value="", key=f"chaku1_{i}")
        with col2:
            chaku2 = st.text_input(f"{i+1}番【前走】", value="", key=f"chaku2_{i}")
        chaku_inputs.append([chaku1, chaku2])

    st.subheader("▼ 競争得点入力")
    rating = [st.number_input(f"{i+1}番得点", value=55.0, step=0.1, key=f"rate_{i}") for i in range(7)]

    st.subheader("▼ 予想隊列入力（数字、欠の場合は空欄）")
    tairetsu = [st.text_input(f"{i+1}番隊列順位", key=f"tai_{i}") for i in range(7)]

    st.subheader("▼ S・B 入力（各選手のS・B回数を入力）")
    for i in range(7):
        st.markdown(f"**{i+1}番**")
        st.number_input("S回数", min_value=0, max_value=99, value=0, step=1, key=f"s_point_{i+1}")
        st.number_input("B回数", min_value=0, max_value=99, value=0, step=1, key=f"b_point_{i+1}")

    st.subheader("▼ ライン構成入力（A〜Dライン＋単騎）")
    a_line = st.text_input("Aライン（例：13）", key="a_line", max_chars=9)
    b_line = st.text_input("Bライン（例：25）", key="b_line", max_chars=9)
    c_line = st.text_input("Cライン（例：47）", key="c_line", max_chars=9)
    d_line = st.text_input("Dライン（例：68）", key="d_line", max_chars=9)
    solo_line = st.text_input("単騎枠（例：9）", key="solo_line", max_chars=9)

    submitted = st.form_submit_button("スコア計算実行")

# --- ライン構成入力に必要な補助関数 ---
def extract_car_list(input_str):
    return [int(c) for c in input_str if c.isdigit()]

def build_line_position_map():
    result = {}
    for line, name in zip([a_line, b_line, c_line, d_line, solo_line], ['A', 'B', 'C', 'D', 'S']):
        cars = extract_car_list(line)
        for i, car in enumerate(cars):
            if name == 'S':
                result[car] = 0
            else:
                result[car] = i + 1
    return result

# --- スコア補正関数 ---
def score_from_tenscore_list(tens):
    df = pd.DataFrame({"得点": tens})
    df["順位"] = df["得点"].rank(ascending=False, method="min").astype(int)
    baseline = df[df["順位"].between(2, 6)]["得点"].mean()
    df["補正"] = df.apply(lambda r: round(abs(baseline - r["得点"]) * 0.03, 3) if r["順位"] in [2, 3, 4] else 0.0, axis=1)
    return df["補正"].tolist()

# --- 実行処理 ---
if submitted:
    line_position_map = build_line_position_map()
    st.write("ライン構成マップ:", line_position_map)
    scores = score_from_tenscore_list(rating)
    st.write("補正スコア:", scores)




# --- スコア計算トリガー ---
with st.form(key="score_form"):
    st.subheader("▼ ライン構成入力（最大7ライン）")
    a_line = st.text_input("Aライン（例：13）", key="a_line", max_chars=9)
    b_line = st.text_input("Bライン（例：25）", key="b_line", max_chars=9)
    c_line = st.text_input("Cライン（例：47）", key="c_line", max_chars=9)
    d_line = st.text_input("Dライン（例：68）", key="d_line", max_chars=9)
    e_line = st.text_input("Eライン（例：9）", key="e_line", max_chars=9)
    f_line = st.text_input("Fライン（例：24）", key="f_line", max_chars=9)
    g_line = st.text_input("Gライン（例：57）", key="g_line", max_chars=9)

    tenscore_list = [st.number_input(f"{i+1}番の得点", value=55.0, step=0.1, key=f"score_{i}") for i in range(9)]
    submitted = st.form_submit_button("スコア計算実行")

if submitted:
    line_position_map, line_def = build_line_position_map()
    st.write("ライン構成マップ:", line_position_map)
    st.write("ライン定義:", line_def)
    corrected_scores = score_from_tenscore_list(tenscore_list)
    st.write("補正後スコア：", corrected_scores)


    def wind_straight_combo_adjust(kaku, direction, speed, straight, pos):
        if direction == "無風" or speed < 0.5:
            return 0
    
        base = wind_coefficients.get(direction, 0.0)  # e.g. 上=+0.005
        pos_mult = position_multipliers.get(pos, 0.0)  # e.g. 先頭=0.5, 番手=0.3
    
        # 強化された脚質補正係数（±1.0スケールに）
        kaku_coeff = {
            '逃': +0.3,
            '両':  +0.15,
            '追': -0.3
        }.get(kaku, 0.0)
    
        total = base * speed * pos_mult * kaku_coeff  # 例: +0.1×10×1×1 = +1.0
        return round(total, 2)


    def convert_chaku_to_score(values):
        scores = []
        for i, v in enumerate(values):  # i=0: 前走, i=1: 前々走
            v = v.strip()
            try:
                chaku = int(v)
                if 1 <= chaku <= 9:
                    score = (10 - chaku) / 9
                    if i == 1:  # 前々走のみ補正
                        score *= 0.35
                    scores.append(score)
            except ValueError:
                continue
        if not scores:
            return None
        return round(sum(scores) / len(scores), 2)


    def lap_adjust(kaku, laps):
        delta = max(laps - 2, 0)
        return {
            '逃': round(-0.1 * delta, 1),
            '追': round(+0.05 * delta, 1),
            '両': 0.0
        }.get(kaku, 0.0)

    def line_member_bonus(pos):
        return {
            0: 0.25,  # 単騎
            1: 0.25,  # 先頭（ライン1番手）
            2: 0.3,  # 2番手（番手）
            3: 0.3,  # 3番手（最後尾）
            4: 0.15   # 4番手（9車用：評価不要レベル）
        }.get(pos, 0.0)


    def bank_character_bonus(kaku, angle, straight):
        """
        カント角と直線長による脚質補正（スケール緩和済み）
        """
        straight_factor = (straight - 40.0) / 10.0
        angle_factor = (angle - 25.0) / 5.0
        total_factor = -0.1 * straight_factor + 0.1 * angle_factor
        return round({'逃': +total_factor, '追': -total_factor, '両': +0.25 * total_factor}.get(kaku, 0.0), 2)
        
    def bank_length_adjust(kaku, length):
        """
        バンク周長による補正（400基準を完全維持しつつ、±0.15に制限）
        """
        delta = (length - 411) / 100
        delta = max(min(delta, 0.075), -0.075)
        return round({'逃': 1.0 * delta, '両': 2.0 * delta, '追': 3.0 * delta}.get(kaku, 0.0), 2)

    def compute_group_bonus(score_parts, line_def):
        group_scores = {k: 0.0 for k in ['A', 'B', 'C', 'D']}
        group_counts = {k: 0 for k in ['A', 'B', 'C', 'D']}

            # 各ラインの合計スコアと人数を集計
        for entry in score_parts:
            car_no, score = entry[0], entry[-1]
            for group in ['A', 'B', 'C', 'D']:
                if car_no in line_def[group]:
                    group_scores[group] += score
                    group_counts[group] += 1
                    break
        # 合計スコアで順位を決定（平均ではない）
        sorted_lines = sorted(group_scores.items(), key=lambda x: x[1], reverse=True)
    
        # 上位グループから順に 0.25 → 0.2 → 0.15→0.1 のボーナスを付与
        bonus_map = {group: [0.25, 0.2, 0.15, 0.1][idx] for idx, (group, _) in enumerate(sorted_lines)}
    
        return bonus_map


# --- ライン構成入力（最大7ライン対応：A〜G） ---
st.subheader("▼ ライン構成入力（最大7ライン）")
a_line = st.text_input("Aライン（例：13）", key="a_line_main", max_chars=9)
b_line = st.text_input("Bライン（例：25）", key="b_line_main", max_chars=9)
c_line = st.text_input("Cライン（例：47）", key="c_line_main", max_chars=9)
d_line = st.text_input("Dライン（例：68）", key="d_line_main", max_chars=9)
e_line = st.text_input("Eライン（例：9）", key="e_line_main", max_chars=9)
f_line = st.text_input("Fライン（例：24）", key="f_line_main", max_chars=9)
g_line = st.text_input("Gライン（例：57）", key="g_line_main", max_chars=9)

# --- ライン構成入力に必要な補助関数 ---
def extract_car_list(input_str):
    return [int(c) for c in input_str if c.isdigit()]

def build_line_position_map():
    line_position_map = {}
    line_def = {
        'A': extract_car_list(a_line),
        'B': extract_car_list(b_line),
        'C': extract_car_list(c_line),
        'D': extract_car_list(d_line),
        'E': extract_car_list(e_line),
        'F': extract_car_list(f_line),
        'G': extract_car_list(g_line),
    }
    for label, members in line_def.items():
        for i, car in enumerate(members):
            line_position_map[car] = (label, i + 1)  # ライン名と番手を記録
    return line_position_map, line_def

# --- グループ補正取得関数 ---
def get_group_bonus(car_no, line_def, group_bonus_map):
    for group in line_def:
        if car_no in line_def[group]:
            base_bonus = group_bonus_map.get(group, 0.0)
            s_bonus = 0.15 if group == 'A' else 0.0  # Aラインには+0.15
            return base_bonus + s_bonus
    return 0.0

# --- ライン構成取得と番手取得マップ作成 ---
line_position_map, line_def = build_line_position_map()
line_order = [line_position_map.get(i + 1, (None, 0))[1] for i in range(9)]

# --- 競争得点リストからスコアを生成する補正関数 ---
def score_from_tenscore_list(tenscore_list):
    sorted_unique = sorted(set(tenscore_list), reverse=True)
    score_to_rank = {score: rank + 1 for rank, score in enumerate(sorted_unique)}
    result = []
    for score in tenscore_list:
        rank = score_to_rank[score]
        correction = {
            -3: 0.0, -2: 0.0, -1: 0.0, 0: 0.0,
             1: 0.10, 2: 0.20, 3: 0.30,
             4: 0.40, 5: 0.50
        }
        result.append(correction.get(rank, 0.0))
    return result




# --- グループ補正取得関数 ---
def get_group_bonus(car_no, line_def, group_bonus_map):
    for group in line_def:
        if car_no in line_def[group]:
            base_bonus = group_bonus_map.get(group, 0.0)
            s_bonus = 0.15 if group == 'A' else 0.0  # Aラインには+0.15
            return base_bonus + s_bonus
    return 0.0

# --- ライン構成取得と番手取得マップ作成 ---
line_position_map, line_def = build_line_position_map()
line_order = [line_position_map.get(i + 1, (None, 0))[1] for i in range(9)]



# スコア計算
tenscore_score = score_from_tenscore_list(rating)
score_parts = []

for i in range(7):
    if not tairetsu[i].isdigit():
        continue

    num = i + 1
    kaku = car_to_kakushitsu.get(num, "追")
    base = base_score[kaku]

    wind = wind_straight_combo_adjust(
        kaku,
        st.session_state.selected_wind,
        wind_speed,
        straight_length,
        line_order[i]
    )

    chaku_values = chaku_inputs[i]
    kasai = convert_chaku_to_score(chaku_inputs[i]) or 0.0
    rating_score = tenscore_score[i]
    rain_corr = lap_adjust(kaku, laps)
    s_bonus = -0.01 * st.session_state.get(f"s_point_{num}", 0)
    b_bonus = 0.05 * st.session_state.get(f"b_point_{num}", 0)
    symbol_score = s_bonus + b_bonus
    line_bonus = line_member_bonus(line_order[i])
    bank_bonus = bank_character_bonus(kaku, bank_angle, straight_length)
    length_bonus = bank_length_adjust(kaku, bank_length)

    total = base + wind + kasai + rating_score + rain_corr + symbol_score + line_bonus + bank_bonus + length_bonus

    score_parts.append([
        num, kaku, base, wind, kasai, rating_score, rain_corr,
        symbol_score, line_bonus, bank_bonus, length_bonus, total
    ])


    # グループ補正
    group_bonus_map = compute_group_bonus(score_parts, line_def)
    final_score_parts = []
    for row in score_parts:
        group_corr = get_group_bonus(row[0], line_def, group_bonus_map)
        new_total = row[-1] + group_corr
        final_score_parts.append(row[:-1] + [group_corr, new_total])


    # 表示
    df = pd.DataFrame(final_score_parts, columns=[
        '車番', '脚質', '基本', '風補正', '着順補正', '得点補正',
        '周回補正', 'SB印補正', 'ライン補正', 'バンク補正', '周長補正',
        'グループ補正', '合計スコア'
    ])
    st.dataframe(df.sort_values(by='合計スコア', ascending=False).reset_index(drop=True))
    
try:
    if not final_score_parts:
        st.warning("スコアが計算されていません。入力や処理を確認してください。")
        st.stop()
except NameError:
    st.warning("スコアデータが定義されていません。入力に問題がある可能性があります。")
    st.stop()
    

import pandas as pd
import streamlit as st

from itertools import combinations
import pandas as pd
import streamlit as st

# --- B回数列の統一 ---
df.rename(columns={"バック": "B回数"}, inplace=True)
b_list = [st.session_state.get(f"b_point_{i+1}", 0) for i in range(len(df))]
if len(b_list) != len(df):
    st.error("⚠ B回数の数が選手数と一致していません")
    st.stop()
df["B回数"] = b_list

# --- 競争得点の取得 ---
rating = [st.session_state.get(f"rate_{i}", 55.0) for i in range(7)]
df["得点"] = rating

# --- ライン構成取得 ---
a_line = extract_car_list(a_line)
b_line = extract_car_list(b_line)
c_line = extract_car_list(c_line)
d_line = extract_car_list(d_line)
solo_line = extract_car_list(solo_line)

line_def_raw = {
    'A': a_line,
    'B': b_line,
    'C': c_line,
    'D': d_line,
    '単騎': solo_line
}

# 単騎を個別ライン化
line_def = {k: v for k, v in line_def_raw.items() if k != '単騎'}
solo_members = line_def_raw.get('単騎', [])
for i, solo_car in enumerate(solo_members):
    line_def[f'単騎{i+1}'] = [solo_car]

# --- ◎決定（得点2〜4位からスコア最上位） ---
df_sorted_by_score = df.sort_values(by="合計スコア", ascending=False).reset_index(drop=True)
df_sorted_by_rating = df.sort_values(by="得点", ascending=False).reset_index(drop=True)
df_rating_top2_4 = df_sorted_by_rating.iloc[1:4]
df_candidate = df[df["車番"].isin(df_rating_top2_4["車番"])]
anchor_row = df_candidate.sort_values(by="合計スコア", ascending=False).iloc[0]
anchor = int(anchor_row["車番"])

# --- 本命ラインの再設定（anchorが含まれるライン） ---
main_line_found = False
for label, members in line_def.items():
    if anchor in members:
        a_line = members
        main_line_found = True
        break
if not main_line_found:
    a_line = [anchor]  # 単騎扱い

# --- 単騎◎判定 ---
is_anchor_solo = len(a_line) == 1 and a_line[0] == anchor

# --- ライングループ抽出（2車以上） ---
line_groups = []
for label, members in line_def.items():
    if len(members) >= 2:
        line_groups.append(members)

# --- 三連複構成抽出 ---
kumi_awase = {"構成①": [], "構成②": [], "構成③": [], "漁夫構成": []}
selection_reason = {"構成①": [], "構成②": [], "構成③": [], "漁夫構成": []}

# --- Cグループ定義（for 通常構成） ---
c_group = c_line + d_line + solo_members

df_car_scores = df.set_index("車番")

if is_anchor_solo:
    # --- 漁夫の利構成（ライン単位で2組） ---
    rival_lines = [line for line in line_groups if anchor not in line]
    if len(rival_lines) >= 2:
        line_scores = []
        for line in rival_lines:
            score_sum = sum([df_car_scores.loc[x, "合計スコア"] for x in line])
            line_scores.append((line, score_sum))
        top2_lines = sorted(line_scores, key=lambda x: x[1], reverse=True)[:2]
        top2_cars = []
        for line, _ in top2_lines:
            best = max(line, key=lambda x: df_car_scores.loc[x, "合計スコア"])
            top2_cars.append(best)
        kumi = tuple(sorted([anchor] + top2_cars))
        kumi_awase["漁夫構成"].append(kumi)
        selection_reason["漁夫構成"].append(f"◎({anchor})–漁夫の利ライン({top2_cars[0]},{top2_cars[1]})")
else:
    # --- 構成①：◎–A–C（A残り＋C） ---
    a_line_filtered = [a for a in a_line if a != anchor]
    if len(a_line_filtered) >= 1 and len(c_group) >= 1:
        a_sorted = sorted(a_line_filtered, key=lambda x: df_car_scores.loc[x, "合計スコア"], reverse=True)
        c_sorted = sorted(c_group, key=lambda x: df_car_scores.loc[x, "合計スコア"], reverse=True)
        for a in a_sorted:
            for c in c_sorted:
                kumi = tuple(sorted([anchor, a, c]))
                kumi_awase["構成①"].append(kumi)
                selection_reason["構成①"].append(f"◎({anchor})–A({a})–C({c})")

    # --- 構成②：Bスコア上位2–◎ ---
    if len(b_line) >= 2:
        b_sorted = sorted(b_line, key=lambda x: df_car_scores.loc[x, "合計スコア"], reverse=True)[:3]
        for b1, b2 in combinations(b_sorted, 2):
            kumi = tuple(sorted([anchor, b1, b2]))
            kumi_awase["構成②"].append(kumi)
            selection_reason["構成②"].append(f"B({b1},{b2})–◎({anchor})")

    # --- 構成③：◎–A上位2–A残り ---
    if len(a_line_filtered) >= 3:
        a_sorted = sorted(a_line_filtered, key=lambda x: df_car_scores.loc[x, "合計スコア"], reverse=True)
        top2 = a_sorted[:2]
        remaining = [a for a in a_sorted if a not in top2]
        for a1 in top2:
            for rem in remaining:
                kumi = tuple(sorted([anchor, a1, rem]))
                kumi_awase["構成③"].append(kumi)
                selection_reason["構成③"].append(f"◎({anchor})–A上位({a1})–A残り({rem})")

# --- 出力部 ---
final_candidates = (
    kumi_awase["構成①"] +
    kumi_awase["構成②"] +
    kumi_awase["構成③"] +
    kumi_awase["漁夫構成"]
)
selection_reason_flat = (
    selection_reason["構成①"] +
    selection_reason["構成②"] +
    selection_reason["構成③"] +
    selection_reason["漁夫構成"]
)

st.markdown("### 🔹 ライン定義")
st.markdown(f"- 本命ライン（A）：{sorted(a_line)}")
st.markdown(f"- 対抗ライン（B）：{sorted(b_line)}")
st.markdown(f"- Cグループ（C以下の統合）：{sorted(c_group)}")

st.markdown("### 🌟 フォーメーション構成")
for reason in selection_reason_flat:
    st.markdown(f"- {reason}")
for i, kumi in enumerate(final_candidates, 1):
    st.markdown(f"{i}. **{kumi[0]} - {kumi[1]} - {kumi[2]}**")
