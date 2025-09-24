# -*- coding: utf-8 -*-
"""
原価管理MVP｜商品主軸・宮田金物 初期登録版（全面貼り換え）
- CSV不要。初期データをコード同梱。
- 商品主軸で採用単価（◎）/ 最新（〇）/ 平均（▲）を計算。
- 一覧にチェック → 下で数量入力 → 小計/税/合計を即表示（簡易見積）。
- 履歴は任意で表示（仕入先・伝票の監査用途）。

起動：
$ streamlit run k_app3_full.py
"""
import math
from datetime import date, datetime
import pandas as pd
import numpy as np
import streamlit as st

# -------------------------------------
# ページ設定
# -------------------------------------
st.set_page_config(page_title="原価管理MVP（商品主軸・宮田金物 初期登録）", layout="wide")
st.title("原価管理MVP｜商品主軸・宮田金物 初期登録版")

# -------------------------------------
# 初期データ（同梱）
# -------------------------------------
ITEMS = pd.DataFrame([
    ["rebar_D10_NA","鉄筋","異径鋼","D10 無規格","m",None],
    ["rebar_D10_SD295A","鉄筋","異径鋼","SD295A D10","m",None],
    ["rebar_D13_SD295A","鉄筋","異径鋼","SD295A D13","m",None],
    ["rebar_D16_SD345","鉄筋","異径鋼","SD345 D16","m",None],
    ["cdmesh_6_150","鉄筋副材","CDメッシュ","6mm×150目","枚",None],
    ["tie_wire_band5_350","副資材","結束線","バンディ#5 350mm","kg",None],
    ["tie_wire_black5_300","副資材","結束線","ブラックバンディ#5 300mm","kg",None],
    ["mokkons_B200","型枠","丸セパ(5/16)","モッコンB200","本",None],
    ["anchor_btn_1_2x240","金物","アンカーBTN","1/2×240","本",None],
    ["conc_sykoro_4x5x6","基礎副材","コンクリートサイコロ","4×5×6","個",None],
    ["conpa_screw_35","金物","コンパネビス","35mm","本",1000],  # 1箱=1000本
    ["nut_chrome_M12","金物","ナット（クロメート）","M12","個",None],
    ["nut_zinc_1_2","金物","ナット（メッキ）","1/2","個",None],
    ["washer_zinc_1_2","金物","座金（メッキ）","1/2","個",None],
    ["washer_zinc_16mm","金物","座金（メッキ）","16mm","個",None],
    ["boardnail_16x32","消耗品","ボード釘","#16×32","本",None],
    ["paint_tough_red","塗装材","タフペイント","赤","本",None],
    ["paint_tough_white","塗装材","タフペイント","白","本",None],
    ["paint_tough_yellow","塗装材","タフペイント","黄","本",None],
    ["course_thread_65","金物","コーススレッド（皿）","65mm","本",50],   # 1束=50本
    ["course_thread_75","金物","コーススレッド（皿）","75mm","本",50],
    ["plast_hollow_menboku_15","型枠","プラスチック中空面木","15mm","本",None],
    ["plast_hollow_menboku_20","型枠","プラスチック中空面木","20mm","本",None],
    ["plast_hollow_menboku_30","型枠","プラスチック中空面木","30mm","本",None],
], columns=["item_id","category","name","spec","base_unit","units_per_box"]).set_index("item_id")

# ==== 中村ブロック（常時） ====
ITEMS = pd.concat([
    ITEMS,
    pd.DataFrame([
        # item_id,                 category,  name,        spec,          base_unit, units_per_box
        ["block_C12_basic",        "ブロック材","C種12cm",   "基本",        "個", None],
        ["block_C12_corner",       "ブロック材","C種12cm",   "隅",          "個", None],
        ["block_C12_yokokin",      "ブロック材","C種12cm",   "横筋",        "個", None],
        ["block_C12_half",         "ブロック材","C種12cm",   "1/2",        "個", None],

        ["block_C15_basic",        "ブロック材","C種15cm",   "基本",        "個", None],
        ["block_C15_yokokin",      "ブロック材","C種15cm",   "横筋",        "個", None],

        ["block_C19_basic",        "ブロック材","C種19cm",   "基本",        "個", None],
        ["block_C19_yokokin",      "ブロック材","C種19cm",   "横筋",        "個", None],

        ["block_B10_basic",        "ブロック材","B種10cm",   "基本",        "個", None],
        ["block_B10_corner",       "ブロック材","B種10cm",   "隅",          "個", None],

        ["bag_cement",             "資材",      "袋セメント", "25kg",       "袋", None],
        ["bag_sand",               "資材",      "袋砂",       "",           "袋", None],
        ["bag_gravel",             "資材",      "袋砂利",     "",           "袋", None],

        # 参考：棒鋼10mm×4m（“本”売り） ※既存のm換算鉄筋とは別ID
        ["rebar_bar10_4m",         "鉄筋",      "鉄筋",       "φ10 4m棒",   "本", None],
    ], columns=["item_id","category","name","spec","base_unit","units_per_box"]).set_index("item_id")
])

# === 生コン（品番ごと）＋ 割増類 ＋ 砕石 ===
_items_add = pd.DataFrame([
    # 生コン（品番）
    ["rmx_21_15_20N", "生コン",   "レディーミクストコンクリート", "21-15-20 N", "m3", None],
    ["rmx_24_18_20N", "生コン",   "レディーミクストコンクリート", "24-18-20 N", "m3", None],
    ["rmx_18_18_20N", "生コン",   "レディーミクストコンクリート", "18-18-20 N", "m3", None],
    ["rmx_18_12_20BB","生コン",   "レディーミクストコンクリート", "18-12-20 BB","m3", None],

    # 生コン：割増・手数料
    ["rmx_surcharge_smalltruck", "生コン割増", "小型車割増", "", "m3", None],   # 票ではm3計上が多いので m3 に統一
    ["rmx_surcharge_empty",      "生コン割増", "空積料",     "", "台", None],
    ["rmx_surcharge_remote",     "生コン割増", "遠隔地割増", "", "m3", None],
    ["rmx_factory_truck_2t3t",   "生コン割増", "2t·3t車使用料(工場)", "", "台", None],

    # 砕石（クラッシャーラン等）
    ["agg_crusher_run_recycle",  "砕石", "再生クラッシャーラン", "", "m3", None],
    ["agg_katama_sp",            "砕石", "カタマSP",             "", "m3", None],
    ["agg_slag_rc30",            "砕石", "スラグ砕石RC-30",      "", "m3", None],
    ["agg_nj_slag",              "砕石", "NJスラグ",             "", "m3", None],
], columns=["item_id","category","name","spec","base_unit","units_per_box"]).set_index("item_id")

# 追記（重複IDがあれば上書き）
ITEMS = pd.concat([ITEMS, _items_add[~_items_add.index.isin(ITEMS.index)]], axis=0)
ITEMS_D = ITEMS.to_dict(orient="index")



ITEMS_D = ITEMS.to_dict(orient="index")  # 追記後に再生成



# 径→kg/m（JIS実務値）
REBAR_KG_PER_M = {
    "D6":0.222,"D10":0.617,"D13":0.995,"D16":1.560,"D19":2.250,
    "D22":2.980,"D25":3.980,"D29":5.040,"D32":6.350,"D35":7.990,
    "D38":9.860,"D41":11.90,
}

# 価格履歴（宮田金物）—※ ここは一度だけ定義（重複定義しない）
PRICES_INIT = pd.DataFrame([
    ["2025-03-21","宮田金物","rebar_D10_SD295A","SD295A","D10","kg",141,None,"伝票279300"],
    ["2025-03-21","宮田金物","rebar_D13_SD295A","SD295A","D13","kg",139,None,"伝票279300"],
    ["2025-03-21","宮田金物","rebar_D10_NA","無規格","D10","kg",139,None,"伝票272xxx"],
    ["2025-02-28","宮田金物","rebar_D10_NA","無規格","D10","kg",138,None,"伝票272896"],
    ["2024-11-30","宮田金物","rebar_D16_SD345","SD345","D16","kg",139,None,"伝票279458"],
    ["2024-10-31","宮田金物","rebar_D16_SD345","SD345","D16","kg",134,None,"伝票273079"],

    ["2024-11-30","宮田金物","cdmesh_6_150","","","枚",1300,None,"伝票279192"],

    ["2025-02-28","宮田金物","tie_wire_band5_350","","","kg",290,None,"伝票279150"],
    ["2024-09-30","宮田金物","tie_wire_band5_350","","","kg",260,None,"伝票272896"],
    ["2025-03-31","宮田金物","tie_wire_black5_300","","","kg",290,None,"伝票279458"],

    ["2024-12-18","宮田金物","mokkons_B200","","","本",23,None,"伝票275954"],
    ["2025-03-21","宮田金物","mokkons_B200","","","本",25,None,"伝票279300"],

    ["2024-11-18","宮田金物","anchor_btn_1_2x240","","","本",150,None,"伝票275036"],

    ["2025-02-14","宮田金物","conc_sykoro_4x5x6","","","個",25,None,"伝票277903"],

    ["2025-03-26","宮田金物","conpa_screw_35","","","箱",2500,1000,"伝票279290"],
    ["2025-02-10","宮田金物","conpa_screw_35","","","箱",2200,1000,"伝票277660"],

    ["2024-11-18","宮田金物","nut_chrome_M12","","","個",14,None,"伝票275036"],
    ["2025-03-27","宮田金物","nut_zinc_1_2","","","個",13,None,"伝票279394"],
    ["2025-03-27","宮田金物","washer_zinc_1_2","","","個",17,None,"伝票279394"],
    ["2024-11-18","宮田金物","washer_zinc_16mm","","","個",15,None,"伝票275036"],

    ["2025-02-18","宮田金物","paint_tough_white","","","本",220,None,"伝票278032"],
    ["2025-02-18","宮田金物","paint_tough_red","","","本",220,None,"伝票278032"],
    ["2025-02-14","宮田金物","paint_tough_yellow","","","本",220,None,"伝票277903"],

    ["2025-02-18","宮田金物","course_thread_65","","","束",1000,50,"伝票278032"],
    ["2025-02-18","宮田金物","course_thread_75","","","束",1100,50,"伝票278032"],

    ["2025-02-14","宮田金物","boardnail_16x32","","","本",6,None,"伝票277903"],
], columns=[
    "date","vendor","item_id","standard","diameter","invoice_unit","unit_price","qty_per_invoice_unit","source"
])

# ==== 中村ブロック 初期価格（伝票ベースの代表単価） ====
PRICES_INIT = pd.concat([
    PRICES_INIT,
    pd.DataFrame([
        # date,       vendor,        item_id,               standard, diameter, invoice_unit, unit_price, qty_per_invoice_unit, source
        ["2025-03-01","中村ブロック","block_C12_basic",     "",       "",       "個",          180,        None,                "伝票写し"],
        ["2025-03-01","中村ブロック","block_C12_corner",    "",       "",       "個",          180,        None,                "伝票写し"],
        ["2025-03-01","中村ブロック","block_C12_yokokin",   "",       "",       "個",          180,        None,                "伝票写し"],
        ["2025-03-01","中村ブロック","block_C12_half",      "",       "",       "個",          180,        None,                "伝票写し"],

        ["2025-03-01","中村ブロック","block_C15_basic",     "",       "",       "個",          210,        None,                "伝票写し"],
        ["2025-03-01","中村ブロック","block_C15_yokokin",   "",       "",       "個",          210,        None,                "伝票写し"],

        ["2025-03-01","中村ブロック","block_C19_basic",     "",       "",       "個",          295,        None,                "伝票写し"],
        ["2025-03-01","中村ブロック","block_C19_yokokin",   "",       "",       "個",          295,        None,                "伝票写し"],

        ["2025-03-01","中村ブロック","block_B10_basic",     "",       "",       "個",          145,        None,                "伝票写し"],
        ["2025-03-01","中村ブロック","block_B10_corner",    "",       "",       "個",          145,        None,                "伝票写し"],

        ["2025-03-01","中村ブロック","bag_cement",          "",       "",       "袋",          780,        None,                "伝票写し"],
        ["2025-03-01","中村ブロック","bag_sand",            "",       "",       "袋",          280,        None,                "伝票写し"],
        ["2025-03-01","中村ブロック","bag_gravel",          "",       "",       "袋",          280,        None,                "伝票写し"],

        ["2025-03-01","中村ブロック","rebar_bar10_4m",      "",       "",       "本",          370,        None,                "伝票写し"],
    ], columns=["date","vendor","item_id","standard","diameter","invoice_unit","unit_price","qty_per_invoice_unit","source"])
])

_prices_add = pd.DataFrame([
    # 生コン 単価（円/m3）
    ["2025-03-10","某生コンプラント","rmx_18_18_20N","", "", "m3", 22800, None, "伝票"],
    ["2025-03-10","某生コンプラント","rmx_21_15_20N","", "", "m3", 23300, None, "伝票"],
    ["2025-03-10","某生コンプラント","rmx_24_18_20N","", "", "m3", 23800, None, "伝票"],
    ["2025-03-01","某生コンプラント","rmx_18_12_20BB","", "", "m3", 22200, None, "伝票"],

    # 生コン 割増（票に合わせて）
    ["2025-03-10","某生コンプラント","rmx_surcharge_smalltruck","", "", "m3", 2000, None, "小型車割増"],
    ["2025-03-10","某生コンプラント","rmx_surcharge_empty",     "", "", "台", 2000, None, "空積料"],
    ["2025-03-01","某生コンプラント","rmx_surcharge_remote",    "", "", "m3", 3500, None, "遠隔地割増"],
    ["2025-03-10","某生コンプラント","rmx_factory_truck_2t3t",  "", "", "台", 5000, None, "2t·3t車使用料(工場)"],

    # 砕石（通知書：令和7年10月1日実施／土場渡し 円/m3）
    ["2025-10-01","上野石材","agg_crusher_run_recycle","", "", "m3", 1700, None, "価格改定通知"],
    ["2025-10-01","上野石材","agg_katama_sp",          "", "", "m3", 1600, None, "価格改定通知"],
    ["2025-10-01","上野石材","agg_slag_rc30",          "", "", "m3", 1500, None, "価格改定通知"],
    ["2025-10-01","上野石材","agg_nj_slag",            "", "", "m3", 1000, None, "価格改定通知"],
], columns=["date","vendor","item_id","standard","diameter","invoice_unit","unit_price","qty_per_invoice_unit","source"])

PRICES_INIT = pd.concat([PRICES_INIT, _prices_add], ignore_index=True)



# -------------------------------------
# セッション初期化
# -------------------------------------
if "prices_raw" not in st.session_state:
    st.session_state["prices_raw"] = PRICES_INIT.copy()

# 商品辞書（以降の関数で参照）
ITEMS_D = ITEMS.to_dict(orient="index")

# ★ 自動投入の追跡用（鉄筋/メッシュを上書き管理）
st.session_state.setdefault("auto_injected", {"rebar": {}, "mesh": {}})

# ★ 見積カート（選択/数量）
st.session_state.setdefault("pick_state", {"selected": set(), "qty": {}})


# -------------------------------------
# ユーティリティ
# -------------------------------------
def base_unit(item_id):
    return ITEMS_D[item_id]["base_unit"]

def units_per_box(item_id):
    return ITEMS_D[item_id]["units_per_box"]

def is_rebar(item_id):
    return ITEMS_D[item_id]["category"] == "鉄筋" and ITEMS_D[item_id]["base_unit"] == "m"

# 単価をベース単位に正規化
# - 鉄筋(m基準): 円/kg→円/m（×kg/m）
# - 箱/束: 入数で按分して本単価に統一

def normalize_price(row):
    item_id = row["item_id"]
    inv_unit = str(row["invoice_unit"]) if row["invoice_unit"] is not None else ""
    price = float(row["unit_price"]) if row["unit_price"] is not None else np.nan
    qpu = row["qty_per_invoice_unit"]

    bunit = base_unit(item_id)

    # 箱/束 → 本に按分
    if inv_unit in ("箱","束"):
        n = units_per_box(item_id) or qpu
        if n and float(n) > 0:
            price = price / float(n)
            inv_unit = "本"

    # 鉄筋：kg→m
    if is_rebar(item_id):
        dia = str(row.get("diameter") or "")
        if inv_unit == "kg" and dia in REBAR_KG_PER_M:
            kgpm = REBAR_KG_PER_M[dia]
            return price * kgpm, f"kg→m換算 ×{kgpm}kg/m"
        elif inv_unit == "m":
            return price, "m単価"
        else:
            return np.nan, f"未対応({inv_unit})"

    # 非鉄筋：単位一致ならそのまま
    if inv_unit == bunit:
        return price, f"{bunit}単価"
    if inv_unit == "本" and bunit == "本":
        return price, "本単価(按分済)"

    return np.nan, f"未対応({inv_unit}→{bunit})"


def adopt_price(group_df, policy):
    df = group_df.dropna(subset=["price_per_base"])  # 正規化済
    if df.empty:
        return np.nan, "データなし", None

    if policy == "高い方（値上がり優先）":
        idx = df["price_per_base"].idxmax()
        r = df.loc[idx]
        return float(r["price_per_base"]), f"高値採用｜{r['vendor']}｜{r['date'].date()}｜{r['source']}", r
    elif policy == "最新日付":
        lastd = df["date"].max()
        last = df[df["date"]==lastd]
        idx = last["price_per_base"].idxmax()
        r = last.loc[idx]
        return float(r["price_per_base"]), f"最新採用｜{r['vendor']}｜{r['date'].date()}｜{r['source']}", r
    else:  # 期間平均
        return float(np.round(df["price_per_base"].mean(),1)), f"期間平均（{len(df)}件）", None

# -------------------------------------
# サイドバー：期間 / 採用ポリシー
# -------------------------------------
st.sidebar.header("フィルタ / 採用ポリシー")
policy = st.sidebar.radio("採用ポリシー", ["高い方（値上がり優先）","最新日付","期間平均"], index=0)

raw = st.session_state["prices_raw"].copy()
raw["date"] = pd.to_datetime(raw["date"], errors="coerce")

c1, c2 = st.sidebar.columns(2)
min_d = raw["date"].min() if raw["date"].notna().any() else pd.to_datetime("2025-01-01")
max_d = raw["date"].max() if raw["date"].notna().any() else pd.to_datetime("2025-12-31")
start = c1.date_input("開始日", value=min_d.date() if not pd.isna(min_d) else date.today())
end   = c2.date_input("終了日", value=max_d.date() if not pd.isna(max_d) else date.today())

flt = raw[(raw["date"]>=pd.to_datetime(start)) & (raw["date"]<=pd.to_datetime(end))].copy()

# 正規化
norm_rows = []
for _, r in flt.iterrows():
    p, note = normalize_price(r)
    norm_rows.append({**r.to_dict(), "price_per_base": np.round(p,1) if not pd.isna(p) else np.nan, "detail": note})
NORM = pd.DataFrame(norm_rows)

# -------------------------------------
# 商品主軸：◎〇▲ まとめテーブル
# -------------------------------------
st.markdown("### 商品一覧（商品→採用単価→履歴の順に表示）")

records = []
for item_id, meta in ITEMS_D.items():
    g = NORM[NORM["item_id"]==item_id]
    price_adopt, note_adopt, _ = adopt_price(g, policy)
    price_latest, _, _ = adopt_price(g, "最新日付")
    price_avg, _, _ = adopt_price(g, "期間平均")

    records.append({
        "商品ID": item_id,
        "カテゴリ": meta["category"],
        "商品名": meta["name"],
        "規格/仕様": meta["spec"],
        "基準単位": meta["base_unit"],
        "◎ 採用単価": price_adopt,
        "〇 最新単価": price_latest,
        "▲ 期間平均": price_avg,
        "採用注記": note_adopt,
    })

TABLE = pd.DataFrame(records).sort_values(["カテゴリ","商品名","規格/仕様"]).reset_index(drop=True)

st.caption("※ 鉄筋は 円/kg→円/m に換算済。箱/束は按分して本単価に統一。丸めは小数1位四捨五入。")

# -------------------------------------
# 商品選択（上：チェックのみ）＋ 選択品の数量入力（下）
# ー 選択・数量はセッション保持 ー
# -------------------------------------
st.markdown("### 商品選択（✔だけ）")

# セッション初期化
if "pick_state" not in st.session_state:
    st.session_state["pick_state"] = {"selected": set(), "qty": {}}
S = st.session_state["pick_state"]

# ★ 追加：auto_injected を必ず用意（KeyError防止）
st.session_state.setdefault("auto_injected", {"rebar": {}, "mesh": {}})



# 上：全商品一覧（チェックだけ／数量列は出さない）
table_pick = TABLE[["商品ID","カテゴリ","商品名","規格/仕様","基準単位","◎ 採用単価"]].copy()
table_pick.rename(columns={"◎ 採用単価":"単価（基準単位）"}, inplace=True)
table_pick.insert(0, "選択", table_pick["商品ID"].isin(S["selected"]))

edited_pick = st.data_editor(
    table_pick,
    use_container_width=True,
    hide_index=True,
    num_rows="fixed",
    key="picker_only",
    column_config={
        "選択": st.column_config.CheckboxColumn("選択"),
        "単価（基準単位）": st.column_config.NumberColumn("単価（基準単位）", format="%.1f"),
    }
)

# 選択状態を反映：新規に✔が付いた品は数量=1を初期セット（既存は維持）
new_selected = set(edited_pick.loc[edited_pick["選択"] == True, "商品ID"])
newly_added = new_selected.difference(S["selected"])

qty = dict(S["qty"])
for iid in newly_added:
    if iid not in qty or qty[iid] <= 0:
        qty[iid] = 1.0  # 初期値

# ✔が外れた品は数量も削除してスリムに
qty = {k: v for k, v in qty.items() if k in new_selected}

S["selected"] = new_selected
S["qty"] = qty

st.markdown("---")
st.subheader("選択品の数量入力（抽出表示）")

if len(S["selected"]) == 0:
    st.info("上の一覧で見積したい商品に ✔ を入れてください。")
else:
    # 下：選択品だけを抽出して数量を編集
    picked = TABLE[TABLE["商品ID"].isin(S["selected"])][
        ["商品ID","商品名","規格/仕様","基準単位"]
    ].copy()
    picked["単価（基準単位）"] = picked["商品ID"].map(TABLE.set_index("商品ID")["◎ 採用単価"])
    picked["数量（基準単位）"] = picked["商品ID"].map(S["qty"]).fillna(1.0)

    edit_sel = st.data_editor(
        picked,
        use_container_width=True,
        hide_index=True,
        num_rows="fixed",
        key="selected_only",
        column_config={
            "単価（基準単位）": st.column_config.NumberColumn("単価（基準単位）", format="%.1f"),
            "数量（基準単位）": st.column_config.NumberColumn("数量（基準単位）", step=1.0),
        }
    )

    # 数量の編集をセッションに反映（保持）
    S["qty"] = {
        row["商品ID"]: float(row["数量（基準単位）"])
        for _, row in edit_sel.iterrows() if row["数量（基準単位）"] > 0
    }

    # 計算
    calc = edit_sel.copy()
    calc["小計（税抜）"] = calc["数量（基準単位）"] * calc["単価（基準単位）"]

    c1, c2, _ = st.columns(3)
    tax_rate = c1.number_input("消費税率(%)", 0.0, 100.0, 10.0, 0.1)
    rounding = c2.selectbox("端数処理", ["四捨五入","切り上げ","切り捨て"], index=0)

    st.dataframe(calc, use_container_width=True, height=320)

    subtotal = float(calc["小計（税抜）"].sum())
    tax_raw = subtotal * tax_rate / 100.0

    def _round(x: float) -> float:
        if rounding == "四捨五入": return float(np.round(x, 0))
        if rounding == "切り上げ":  return float(np.ceil(x))
        return float(np.floor(x))

    tax = _round(tax_raw)
    grand = _round(subtotal + tax)

    m1, m2, m3 = st.columns(3)
    m1.metric("小計（税抜）", f"{subtotal:,.0f} 円")
    m2.metric(f"消費税（{tax_rate:.1f}%）", f"{tax:,.0f} 円")
    m3.metric("合計（税込）", f"{grand:,.0f} 円")

    # CSV
    export_cols = ["商品ID","商品名","規格/仕様","基準単位","単価（基準単位）","数量（基準単位）","小計（税抜）"]
    csv_quote = calc[export_cols].to_csv(index=False).encode("utf-8-sig")
    st.download_button("↓ この見積明細をCSVでダウンロード",
                       data=csv_quote,
                       file_name=f"easy_quote_{datetime.now():%Y%m%d}.csv",
                       mime="text/csv")

# -------------------------------------
# 鉄筋スラブ 自動拾い（鉄筋方式 vs メッシュ方式 比較・非累積反映）
# ※ TABLE が作成済みの箇所より後に置く
# -------------------------------------
st.markdown("---")
st.subheader("鉄筋スラブ自動拾い（鉄筋方式 vs メッシュ方式 比較）")

with st.form("rebar_mesh_form"):
    # 寸法入力（外寸）
    c1, c2 = st.columns(2)
    L = c1.number_input("長さ L (m)", min_value=0.0, step=0.1, value=10.0)
    W = c2.number_input("幅 W (m)",   min_value=0.0, step=0.1, value=6.0)
    P = 2*(L+W); A = L*W
    st.caption(f"→ 周長 = {P:.2f} m ／ 面積 = {A:.2f} ㎡")

    # かぶり・ロス
    c_cov1, c_cov2 = st.columns(2)
    cover_edge_mm = c_cov1.number_input("かぶり（周囲）mm", min_value=0.0, step=5.0, value=40.0)
    waste = c_cov2.number_input("ロス率(%)", min_value=0.0, max_value=30.0, step=0.5, value=5.0)

    # ピッチ & 配筋
    c3, c4, c5 = st.columns(3)
    pitch_x_mm = c3.number_input("X方向ピッチ(mm)", min_value=50.0, step=10.0, value=200.0)
    pitch_y_mm = c4.number_input("Y方向ピッチ(mm)", min_value=50.0, step=10.0, value=200.0)
    layer = c5.selectbox("配筋", ["単層(シングル)","複層(ダブル)"], index=0)
    layers = 2 if layer.startswith("複層") else 1

    # 鉄筋設定
    c6, c7, c8 = st.columns(3)
    stock_len = c6.number_input("定尺長 (m)", min_value=3.0, max_value=12.0, step=0.5, value=4.0)
    rebar_choice = c7.selectbox("鉄筋種類", [
        ("rebar_D10_NA",    "無規格 D10"),
        ("rebar_D10_SD295A","SD295A D10"),
        ("rebar_D13_SD295A","SD295A D13"),
        ("rebar_D16_SD345", "SD345 D16"),
    ], format_func=lambda x: x[1])
    dia_hint = "D10" if "D10" in rebar_choice[0] else ("D13" if "D13" in rebar_choice[0] else "D16")

    # 結束線・サイコロ（共通係数）
    c9, c10 = st.columns(2)
    tie_kg_per_sqm = c9.number_input("結束線係数 (kg/㎡/層)", min_value=0.0, step=0.1, value=0.4)
    sykoro_per_sqm_layer = c10.number_input("サイコロ係数 (個/㎡/層)", min_value=0.0, step=0.1, value=4.0)

    # メッシュ仕様
    st.markdown("**メッシュ仕様（0.9×1.8m）**")
    c11, c12 = st.columns(2)
    mesh_lap_x = c11.number_input("メッシュ重なり(横) m", min_value=0.0, step=0.05, value=0.15)
    mesh_lap_y = c12.number_input("メッシュ重なり(縦) m", min_value=0.0, step=0.05, value=0.15)

    # 見積反映モード（排他的）
    mode = st.radio("どちらの方式を見積に反映するか？",
                    ["反映しない","鉄筋方式","メッシュ方式"], index=0)

    submitted = st.form_submit_button("数量を計算して比較")

# ------- ここから計算と表示（フォームの外）-------
if submitted:
    # 安全な単価取得（未登録なら0円で進め、画面に注意表示）
    def price_of(item_id: str) -> float:
        try:
            v = TABLE.loc[TABLE["商品ID"]==item_id, "◎ 採用単価"].values
            return float(v[0]) if len(v) else 0.0
        except Exception:
            return 0.0

    cov = cover_edge_mm / 1000.0
    L_eff, W_eff = max(0.0, L - 2*cov), max(0.0, W - 2*cov)
    A_eff = L_eff * W_eff

    if L_eff <= 0 or W_eff <= 0:
        st.error("かぶりが大きすぎます。L-2×かぶり, W-2×かぶり が正になるようにしてください。")
    else:
        # 鉄筋方式
        px, py = pitch_x_mm/1000.0, pitch_y_mm/1000.0
        n_x = int(math.floor(W_eff / px)) + 1
        n_y = int(math.floor(L_eff / py)) + 1
        total_m = (n_x * L_eff + n_y * W_eff) * layers
        total_m *= (1.0 + waste/100.0)

        kgpm = REBAR_KG_PER_M.get(dia_hint, 0.0)
        total_kg = total_m * kgpm
        bars_stock = math.ceil(total_m / stock_len)
        tie_kg = A_eff * tie_kg_per_sqm * layers
        sykoro_pcs = math.ceil(A_eff * sykoro_per_sqm_layer * layers)

        rebar_cost = total_m * price_of(rebar_choice[0])
        tie_cost   = tie_kg * price_of("tie_wire_band5_350")
        sykoro_cost= sykoro_pcs * price_of("conc_sykoro_4x5x6")
        total_cost_rebar = rebar_cost + tie_cost + sykoro_cost

        # メッシュ方式
        mesh_w, mesh_h = 1.8, 0.9
        def needed_sheets(target, sheet, lap):
            if target <= 0: return 0
            if target <= sheet: return 1
            step = max(sheet - lap, 0.01)
            return 1 + int(math.ceil((target - sheet)/step))
        nxA = needed_sheets(L_eff, mesh_w, mesh_lap_x)
        nyA = needed_sheets(W_eff, mesh_h, mesh_lap_y)
        nxB = needed_sheets(L_eff, mesh_h, mesh_lap_x)
        nyB = needed_sheets(W_eff, mesh_w, mesh_lap_y)
        mesh_sheets = min(nxA*nyA, nxB*nyB) * layers

        mesh_cost  = mesh_sheets * price_of("cdmesh_6_150")
        tie_cost_m = tie_kg * price_of("tie_wire_band5_350")
        sykoro_cost_m = sykoro_pcs * price_of("conc_sykoro_4x5x6")
        total_cost_mesh = mesh_cost + tie_cost_m + sykoro_cost_m

        # 表示
        st.success("比較結果（税抜・原価）")
        colA, colB = st.columns(2)
        with colA:
            st.markdown("#### ■ 鉄筋方式")
            st.write({
                "総延長(m)": round(total_m,1),
                "重量(kg)": round(total_kg,1),
                "定尺本数(概算)": bars_stock,
                "結束線(kg)": round(tie_kg,2),
                "サイコロ(個)": int(sykoro_pcs),
                "小計(円)": round(total_cost_rebar),
            })
        with colB:
            st.markdown("#### ■ メッシュ方式")
            st.write({
                "枚数": int(mesh_sheets),
                "結束線(kg)": round(tie_kg,2),
                "サイコロ(個)": int(sykoro_pcs),
                "小計(円)": round(total_cost_mesh),
            })

        # 見積カートへ排他的に上書き
        st.session_state.setdefault("pick_state", {"selected": set(), "qty": {}})
        st.session_state.setdefault("auto_injected", {"rebar": {}, "mesh": {}})
        S  = st.session_state["pick_state"]
        AI = st.session_state["auto_injected"]

        def apply_mode(mode: str, new_items: dict):
            prev = AI.get(mode, {}) or {}
            # 差し戻し＋上書き
            for iid, new_q in new_items.items():
                cur = float(S["qty"].get(iid, 0.0)); prev_q = float(prev.get(iid, 0.0))
                nxt = cur - prev_q + float(new_q)
                if nxt <= 0:
                    S["qty"].pop(iid, None); S["selected"].discard(iid)
                else:
                    S["qty"][iid] = nxt; S["selected"].add(iid)
            # 今回なくなった品をクリア
            for iid in set(prev.keys()) - set(new_items.keys()):
                cur = float(S["qty"].get(iid, 0.0)); prev_q = float(prev.get(iid, 0.0))
                nxt = cur - prev_q
                if nxt <= 0:
                    S["qty"].pop(iid, None); S["selected"].discard(iid)
                else:
                    S["qty"][iid] = nxt; S["selected"].add(iid)
            AI[mode] = dict(new_items)

        rebar_items = {
            rebar_choice[0]: float(total_m),
            "tie_wire_band5_350": float(tie_kg),
            "conc_sykoro_4x5x6": float(sykoro_pcs),
        }
        mesh_items = {
            "cdmesh_6_150": float(mesh_sheets),
            "tie_wire_band5_350": float(tie_kg),
            "conc_sykoro_4x5x6": float(sykoro_pcs),
        }

        if mode == "鉄筋方式":
            apply_mode("mesh", {})           # メッシュをクリア
            apply_mode("rebar", rebar_items)
            st.success("鉄筋方式をカートに上書きしました。"); st.rerun()
        elif mode == "メッシュ方式":
            apply_mode("rebar", {})          # 鉄筋をクリア
            apply_mode("mesh", mesh_items)
            st.success("メッシュ方式をカートに上書きしました。"); st.rerun()

# -------------------------------------
# ブロック基礎（ブロック積） 自動拾い ＋ 見積カートへ上書き
# 位置：鉄筋スラブの直後～履歴の前に置く
# -------------------------------------
st.markdown("---")
st.subheader("ブロック基礎（ブロック積） 自動拾い")

with st.form("block_found_form"):
    c1, c2 = st.columns(2)
    L = c1.number_input("延長 L (m)", min_value=0.0, step=0.1, value=10.0)
    H = c2.number_input("高さ H (m)", min_value=0.0, step=0.1, value=0.8)

    # ブロック種別（厚み別）
    block_choice = st.selectbox(
        "ブロック種別",
        [
            ("block_B10_basic", "B種10cm 基本（100厚）"),
            ("block_C12_basic", "C種12cm 基本（120厚）"),
            ("block_C15_basic", "C種15cm 基本（150厚）"),
            ("block_C19_basic", "C種19cm 基本（190厚）"),
        ],
        index=1,
        format_func=lambda x: x[1]
    )

    st.caption("※ 隅・半マスは任意入力。未入力なら“基本”だけで計算（ロス率で吸収）。")

    c3, c4, c5 = st.columns(3)
    corners = c3.number_input("隅（コーナー）個数", min_value=0, step=1, value=0)
    halfs   = c4.number_input("1/2ブロック個数", min_value=0, step=1, value=0)
    joint_mm= c5.number_input("目地厚(mm)", min_value=5.0, step=1.0, value=10.0)

    c6, c7 = st.columns(2)
    loss_pct = c6.number_input("ロス率(%)", min_value=0.0, max_value=20.0, step=0.5, value=3.0)
    block_len_mm = c7.number_input("ブロック長さ(mm)（標準390）", min_value=300.0, max_value=450.0, step=5.0, value=390.0)

    st.markdown("**モルタル・鉄筋 係数（現場ごとに調整可）**")
    c8, c9, c10 = st.columns(3)
    cement_per_block = c8.number_input("セメント袋/ブロック（目安0.05）", min_value=0.0, step=0.01, value=0.05)
    sand_per_cement  = c9.number_input("袋砂 / セメント1袋（例4）", min_value=0.0, step=0.5, value=4.0)
    gravel_per_cement= c10.number_input("袋砂利 / セメント1袋（通常0）", min_value=0.0, step=0.5, value=0.0)

    c11, c12, c13 = st.columns(3)
    use_hbar = c11.checkbox("横筋を入れる（φ10 4m棒）", value=True)
    hbar_pitch_course = c12.number_input("横筋ピッチ（段おき）", min_value=1, step=1, value=1)  # 1=毎段, 2=1段おき
    vbar_pitch_m = c13.number_input("縦筋ピッチ（m）※任意", min_value=0.3, step=0.1, value=1.2)

    st.caption("※ 縦筋は“必要なら”チェック。4m棒の使用本数で概算します。")
    use_vbar = st.checkbox("縦筋も入れる（φ10 4m棒）", value=False)

    reflect = st.radio("見積への反映", ["反映しない","上書き反映"], index=1)
    submitted_blk = st.form_submit_button("数量を計算")

# ---- 計算＆表示（フォーム外）----
if submitted_blk:
    # 安全な単価取得
    def price_of(item_id: str) -> float:
        try:
            v = TABLE.loc[TABLE["商品ID"]==item_id, "◎ 採用単価"].values
            return float(v[0]) if len(v) else 0.0
        except Exception:
            return 0.0

    # --- ブロック個数 ---
    # 実効長（目地考慮）：1ピースの有効長 ≒ (ブロック長 + 目地)
    pitch_m = (block_len_mm + joint_mm) / 1000.0
    courses = int(max(1, round(H / 0.2)))  # 1段 ≒ 200mm（190+目地）とみなす簡易
    blocks_per_course = max(1, int(math.ceil(L / pitch_m)))
    base_blocks = blocks_per_course * courses
    # 追加（隅・半）
    base_blocks += int(max(0, corners))
    half_blocks = int(max(0, halfs))

    # ロス加算
    total_blocks = math.ceil(base_blocks * (1.0 + loss_pct/100.0))

    # --- モルタル（袋換算） ---
    cement_bags = total_blocks * cement_per_block
    sand_bags   = cement_bags * sand_per_cement
    gravel_bags = cement_bags * gravel_per_cement

    # --- 鉄筋（φ10 4m棒） ---
    rebar_id = "rebar_bar10_4m"
    hbars = 0
    vbars = 0

    if use_hbar:
        used_courses = math.ceil(courses / max(1, hbar_pitch_course))
        # 1段分の必要本数（4m定尺で割り付け）
        bars_per_course = math.ceil(L / 4.0)
        hbars = used_courses * bars_per_course

    if use_vbar and vbar_pitch_m > 0:
        pos = math.ceil(L / vbar_pitch_m) + 1  # 端部含めて+1
        total_len_v = pos * H                   # 全縦筋延長（m）
        vbars = math.ceil(total_len_v / 4.0)    # 4m棒換算

    # --- 結果表示 ---
    st.success("ブロック積 計算結果（数量）")
    st.write({
        "段数(概算)": int(courses),
        "ブロック基本(個)": int(total_blocks),
        "1/2ブロック(個)": int(half_blocks),
        "隅ブロック(個)": int(corners),
        "セメント(袋)": round(cement_bags, 2),
        "袋砂(袋)": round(sand_bags, 2),
        "袋砂利(袋)": round(gravel_bags, 2),
        "横筋 φ10 4m(本)": int(hbars),
        "縦筋 φ10 4m(本)": int(vbars),
    })

    # --- 見積に“非累積で上書き” ---
    if reflect == "上書き反映":
        st.session_state.setdefault("pick_state", {"selected": set(), "qty": {}})
        st.session_state.setdefault("auto_injected", {"block_found": {}})
        S  = st.session_state["pick_state"]
        AI = st.session_state["auto_injected"]

        # 商品IDのマッピング（基本/隅/半）
        item_basic = block_choice[0]
        item_corner = {
            "block_B10_basic":"block_B10_corner",
            "block_C12_basic":"block_C12_corner",
        }.get(item_basic, None)
        item_half = {
            "block_C12_basic":"block_C12_half",
        }.get(item_basic, None)

        new_items = { item_basic: float(total_blocks) }
        if item_corner and corners > 0:
            new_items[item_corner] = float(corners)
        if item_half and half_blocks > 0:
            new_items[item_half] = float(half_blocks)

        if cement_bags > 0: new_items["bag_cement"] = float(cement_bags)
        if sand_bags   > 0: new_items["bag_sand"]   = float(sand_bags)
        if gravel_bags > 0: new_items["bag_gravel"] = float(gravel_bags)

        if (use_hbar and hbars>0) or (use_vbar and vbars>0):
            new_items[rebar_id] = float(hbars + vbars)

        # 非累積の上書き（前回を差し戻して今回分に入れ替え）
        prev = AI.get("block_found", {}) or {}
        for iid, new_q in new_items.items():
            cur = float(S["qty"].get(iid, 0.0)); prv = float(prev.get(iid, 0.0))
            nxt = cur - prv + float(new_q)
            if nxt <= 0:
                S["qty"].pop(iid, None); S["selected"].discard(iid)
            else:
                S["qty"][iid] = nxt; S["selected"].add(iid)
        for iid in set(prev.keys()) - set(new_items.keys()):
            cur = float(S["qty"].get(iid, 0.0)); prv = float(prev.get(iid, 0.0))
            nxt = cur - prv
            if nxt <= 0:
                S["qty"].pop(iid, None); S["selected"].discard(iid)
            else:
                S["qty"][iid] = nxt; S["selected"].add(iid)
        AI["block_found"] = dict(new_items)

        st.success("ブロック基礎（ブロック積）を見積に上書き反映しました。")
        st.rerun()

# -------------------------------------
# 基礎：土間スラブ（ベタコン）フォーム
# （生コン・配筋・砕石・周囲型枠）
# -------------------------------------
st.markdown("---")
st.subheader("基礎 土間スラブ（ベタコン）｜生コン・配筋・砕石・周囲型枠")

with st.form("slab_form"):
    # 平面寸法
    c1, c2 = st.columns(2)
    L = c1.number_input("土間 長さ L (m)", min_value=0.0, step=0.1, value=12.290)
    W = c2.number_input("土間 幅 W (m)",   min_value=0.0, step=0.1, value=5.980)
    A = L * W
    P = 2*(L+W)
    st.caption(f"→ 面積 = {A:.2f} ㎡ ／ 周長 = {P:.2f} m")

    # 生コン
    c3, c4, c5 = st.columns(3)
    t_mm = c3.number_input("土間 厚み (mm)", min_value=50.0, step=10.0, value=100.0)
    rmx_item = c4.selectbox("生コン品番", [
        ("rmx_18_18_20N","18-18-20 N"),
        ("rmx_21_15_20N","21-15-20 N"),
        ("rmx_24_18_20N","24-18-20 N"),
        ("rmx_18_12_20BB","18-12-20 BB"),
    ], index=1, format_func=lambda x: x[1])
    conc_waste = c5.number_input("生コンロス率(%)", min_value=0.0, max_value=30.0, step=0.5, value=5.0)

    # スラブ配筋（2方向@ピッチ）
    st.markdown("**スラブ配筋（2方向@ピッチ）**")
    c6, c7, c8 = st.columns(3)
    cover_mm = c6.number_input("かぶり（外周）mm", min_value=0.0, step=5.0, value=40.0)
    pitch_mm = c7.number_input("配筋ピッチ (mm)", min_value=75.0, step=25.0, value=200.0)
    layers = c8.selectbox("配筋層", ["単層(シングル)","複層(ダブル)"], index=0)
    layer_n = 2 if layers.startswith("複層") else 1

    c9, c10, c11 = st.columns(3)
    slab_rebar = c9.selectbox("スラブ主筋", [
        ("rebar_D10_SD295A","SD295A D10"),
        ("rebar_D13_SD295A","SD295A D13"),
        ("rebar_D16_SD345", "SD345 D16"),
    ], index=0, format_func=lambda x: x[1])
    tie_kg_per_sqm = c10.number_input("結束線係数 (kg/㎡/層)", min_value=0.0, step=0.1, value=0.4)
    chair_per_sqm  = c11.number_input("サイコロ係数 (個/㎡/層)", min_value=0.0, step=0.5, value=4.0)

    # 砕石（下地）
    st.markdown("**砕石（下地）**")
    c12, c13 = st.columns(2)
    subbase_t_mm = c12.number_input("砕石厚 (mm)", min_value=0.0, step=10.0, value=100.0)
    agg_item = c13.selectbox("砕石品目", [
        ("agg_crusher_run_recycle","再生クラッシャーラン"),
        ("agg_katama_sp","カタマSP"),
        ("agg_slag_rc30","スラグ砕石RC-30"),
        ("agg_nj_slag","NJスラグ"),
    ], index=0, format_func=lambda x: x[1])

    # 周囲型枠（片面/両面切替：土間は通常片面）
    st.markdown("**周囲型枠（土間用）**")
    c14, c15, c16 = st.columns(3)
    form_side = c14.selectbox("型枠面", ["片面（通常）","両面（特殊）"], index=0)
    screws_per_sheet = c15.number_input("固定ビス 本/枚", min_value=0, step=1, value=30)
    form_waste = c16.number_input("型枠ロス率(%)", min_value=0.0, max_value=30.0, step=0.5, value=8.0)
    # サンギ：土間は片面想定→既定1m/か所（両面なら2m/か所）
    s_col1, _ = st.columns(2)
    sanki_override = s_col1.checkbox("サンギを両面換算にする（2m/か所）", value=False)

    submitted_slab = st.form_submit_button("数量を計算")

if submitted_slab:
    import math
    # 生コン
    slab_m3 = A * (t_mm/1000.0) * (1.0 + conc_waste/100.0)

    # 配筋（有効寸）
    cov = cover_mm/1000.0
    L_eff, W_eff = max(0.0, L-2*cov), max(0.0, W-2*cov)
    px = py = pitch_mm/1000.0
    n_x = int(math.floor(W_eff/px)) + 1 if px>0 else 0
    n_y = int(math.floor(L_eff/py)) + 1 if py>0 else 0
    total_m_slab = (n_x*L_eff + n_y*W_eff) * layer_n
    total_m_slab *= 1.0  # ロスは配筋では別途設定が無いので0%扱い（必要なら項目追加可能）

    # 重量・付帯
    dia = "D10" if "D10" in slab_rebar[0] else ("D13" if "D13" in slab_rebar[0] else "D16")
    kgpm = REBAR_KG_PER_M.get(dia, 0.0)
    slab_kg = total_m_slab * kgpm
    tie_kg  = A * tie_kg_per_sqm * layer_n
    chairs  = math.ceil(A * chair_per_sqm * layer_n)

    # 砕石
    agg_m3 = A * (subbase_t_mm/1000.0) if subbase_t_mm>0 else 0.0

    # 周囲型枠（パネル：1820×910、採用高さ＝土間厚の切上げ 200/300/450/600/900）
    avail = [200,300,450,600,900]
    H_use = next((x for x in avail if x>=t_mm), avail[-1])
    side_mul = 1 if form_side.startswith("片面") else 2
    sheet_len = 1.82
    sheet_h_m = H_use/1000.0
    area_per_sheet = sheet_len * sheet_h_m
    gross_area = P * sheet_h_m * side_mul * (1.0 + form_waste/100.0)
    sheets = math.ceil(gross_area / area_per_sheet)
    screws = sheets * screws_per_sheet

    # 土間周囲は通常「片面」でセパ/Pコン不要。サンギは 1m/か所（片面）/ 2m/か所（両面）
    pitch = 0.45
    cols = math.ceil(P / pitch) + 1
    rows = max(1, math.ceil((H_use/1000.0) / pitch))
    positions = math.ceil(cols * rows * (1.0 + form_waste/100.0))
    sanki_m = positions * (2.0 if (sanki_override or side_mul==2) else 1.0)

    st.success("土間スラブ 数量")
    st.write({
        "生コン(m³)": round(slab_m3,3),
        "スラブ鉄筋 延長(m)": round(total_m_slab,1),
        "スラブ鉄筋 重量(kg)": round(slab_kg,1),
        "結束線(kg)": round(tie_kg,2),
        "サイコロ(個)": int(chairs),
        "砕石(m³)": round(agg_m3,3),
        "周囲型枠 採用高さ(mm)": H_use,
        "コンパネ(枚)": sheets,
        "固定ビス(本)": screws,
        "サンギ30角(m)": round(sanki_m,1),
        "（注）土間周囲型枠は通常片面のためセパ/Pコンは計上しません": "必要時は両面に切替してください",
    })

# === 見積への上書き反映（スラブ） ===
reflect_slab = st.radio(
    "見積への反映（スラブ）",
    ["反映しない", "上書き反映"],
    index=0,
    key="reflect_slab"
)

if reflect_slab == "上書き反映":
    st.session_state.setdefault("pick_state", {"selected": set(), "qty": {}})
    st.session_state.setdefault("auto_injected", {"foundation_slab": {}})
    S  = st.session_state["pick_state"]
    AI = st.session_state["auto_injected"]

    # 反映する品（IDは既存マスタ）
    new_items = {
        rmx_item[0]: float(slab_m3),            # 生コン m3
        agg_item[0]: float(agg_m3),             # 砕石 m3
        slab_rebar[0]: float(total_m_slab),     # スラブ鉄筋 m（選択径）
        "tie_wire_band5_350": float(tie_kg),    # 結束線 kg
        "conc_sykoro_4x5x6": float(chairs),     # サイコロ 個
        "conpa_screw_35": float(screws),        # コンパネビス 本
        # ★ITEMS未登録のため見積反映は保留（数量は上で表示/CSVに出ています）
        # "form_panel_1820x910": float(sheets),  # コンパネ枚
        # "sanki_30_square": float(sanki_m),     # サンギ m
    }

    # 非累積の上書き（差し戻し→今回分に入替え）
    prev = AI.get("foundation_slab", {}) or {}
    for iid, new_q in new_items.items():
        cur = float(S["qty"].get(iid, 0.0)); prv = float(prev.get(iid, 0.0))
        nxt = cur - prv + float(new_q)
        if nxt <= 0:
            S["qty"].pop(iid, None); S["selected"].discard(iid)
        else:
            S["qty"][iid] = nxt; S["selected"].add(iid)
    for iid in set(prev.keys()) - set(new_items.keys()):
        cur = float(S["qty"].get(iid, 0.0)); prv = float(prev.get(iid, 0.0))
        nxt = cur - prv
        if nxt <= 0:
            S["qty"].pop(iid, None); S["selected"].discard(iid)
        else:
            S["qty"][iid] = nxt; S["selected"].add(iid)

    AI["foundation_slab"] = dict(new_items)
    st.success("土間スラブを見積に上書き反映しました。")
    st.rerun()


    # ===（土間スラブの st.write(...) の直後に追記）===

# 見積反映トグル
reflect_slab = st.radio("見積への反映（スラブ）", ["反映しない","上書き反映"], index=0, key="reflect_slab")

if reflect_slab == "上書き反映":
    st.session_state.setdefault("pick_state", {"selected": set(), "qty": {}})
    st.session_state.setdefault("auto_injected", {"foundation_slab": {}})
    S  = st.session_state["pick_state"]
    AI = st.session_state["auto_injected"]

    # 反映する品（IDは既存マスタ準拠）
    new_items = {
        rmx_item[0]: float(slab_m3),                      # 生コン m3
        agg_item[0]: float(agg_m3),                       # 砕石 m3
        slab_rebar[0]: float(total_m_slab),               # 鉄筋 m（選択径）
        "tie_wire_band5_350": float(tie_kg),              # 結束線 kg
        "conc_sykoro_4x5x6": float(chairs),               # サイコロ 個
        "conpa_screw_35": float(screws),                  # コンパネビス 本
        # ★以下はITEMS未登録につき見積反映は保留
        # "form_panel_1820x910": float(sheets),            # ←ITEMS追加後に有効化
        # "sanki_30_square": float(sanki_m),              # ←ITEMS追加後に有効化
    }

    # 非累積の上書き
    prev = AI.get("foundation_slab", {}) or {}
    for iid, new_q in new_items.items():
        cur = float(S["qty"].get(iid, 0.0)); prv = float(prev.get(iid, 0.0))
        nxt = cur - prv + float(new_q)
        if nxt <= 0:
            S["qty"].pop(iid, None); S["selected"].discard(iid)
        else:
            S["qty"][iid] = nxt; S["selected"].add(iid)
    # 今回なくなった品をクリア
    for iid in set(prev.keys()) - set(new_items.keys()):
        cur = float(S["qty"].get(iid, 0.0)); prv = float(prev.get(iid, 0.0))
        nxt = cur - prv
        if nxt <= 0:
            S["qty"].pop(iid, None); S["selected"].discard(iid)
        else:
            S["qty"][iid] = nxt; S["selected"].add(iid)

    AI["foundation_slab"] = dict(new_items)
    st.success("土間スラブを見積に上書き反映しました。")
    st.rerun()

    # === 見積への上書き反映（スラブ） ===
reflect_slab = st.radio(
    "見積への反映（スラブ）",
    ["反映しない", "上書き反映"],
    index=0,
    key="reflect_slab_v2"   # ← ユニークなキー名に変更
)


    # CSV
    import pandas as pd
    df_slab = pd.DataFrame([{
        "L(m)": L, "W(m)": W, "面積(㎡)": round(A,2), "周長(m)": round(P,2),
        "厚み(mm)": t_mm, "生コン(m³)": round(slab_m3,3),
        "鉄筋延長(m)": round(total_m_slab,1), "鉄筋重量(kg)": round(slab_kg,1),
        "結束線(kg)": round(tie_kg,2), "サイコロ(個)": int(chairs),
        "砕石(m³)": round(agg_m3,3),
        "型枠高さ(mm)": H_use, "パネル(枚)": sheets, "ビス(本)": screws, "サンギ(m)": round(sanki_m,1),
        "型枠面": form_side
    }])



    
    st.download_button("↓ 土間スラブ 明細CSV",
        data=df_slab.to_csv(index=False).encode("utf-8-sig"),
        file_name="slab_bedacon.csv", mime="text/csv")


# -------------------------------------
# 基礎：立上り梁フォーム（生コン・配筋係数・型枠）
# （延長モード：全周 / L×1+W×2 / L×2+W×1 / 任意）
# -------------------------------------
st.markdown("---")
st.subheader("基礎 立上り梁｜生コン・配筋（係数）・型枠（両面）")

with st.form("beam_form"):
    c1, c2 = st.columns(2)
    Lb = c1.number_input("建物長さ L (m)", min_value=0.0, step=0.1, value=12.290)
    Wb = c2.number_input("建物幅 W (m)",   min_value=0.0, step=0.1, value=5.980)

    mode = st.radio("梁延長の計算方法", [
        "全周 (L×2+W×2)",
        "L×1+W×2",
        "L×2+W×1",
        "任意入力"
    ], index=0)
    if mode == "全周 (L×2+W×2)":
        beam_len = 2*(Lb+Wb)
    elif mode == "L×1+W×2":
        beam_len = Lb + 2*Wb
    elif mode == "L×2+W×1":
        beam_len = 2*Lb + Wb
    else:
        beam_len = st.number_input("梁延長 任意入力 (m)", min_value=0.0, step=0.1, value=10.0)
    st.caption(f"→ 梁延長 = {beam_len:.2f} m")

    c3, c4 = st.columns(2)
    b = c3.number_input("梁幅 b (mm)", min_value=100.0, step=10.0, value=150.0)
    h = c4.number_input("梁成 h (mm)", min_value=100.0, step=10.0, value=450.0)

    # 生コン
    rmx_item_b = st.selectbox("生コン品番（立上り）", [
        ("rmx_18_18_20N","18-18-20 N"),
        ("rmx_21_15_20N","21-15-20 N"),
        ("rmx_24_18_20N","24-18-20 N"),
        ("rmx_18_12_20BB","18-12-20 BB"),
    ], index=1, format_func=lambda x: x[1])
    conc_waste_b = st.number_input("生コンロス率(%)（立上り）", min_value=0.0, max_value=30.0, step=0.5, value=5.0)

    # 配筋（係数）
    c5, c6 = st.columns(2)
    rebar_coef = c5.number_input("鉄筋係数 (kg/m³)", min_value=0.0, step=5.0, value=110.0)
    tie_coef   = c6.number_input("結束線係数 (kg/m³)", min_value=0.0, step=0.5, value=2.0)

    # 型枠（両面）＋ 金物（450×450固定）
    st.markdown("**型枠（両面）・金物**")
    c7, c8, c9 = st.columns(3)
    screws_per_sheet_b = c7.number_input("固定ビス 本/枚", min_value=0, step=1, value=30)
    form_waste_b = c8.number_input("型枠ロス率(%)", min_value=0.0, max_value=30.0, step=0.5, value=8.0)
    sanki_both_b = c9.checkbox("サンギ両面で計上（2m/か所）", value=True)

    submitted_beam = st.form_submit_button("数量を計算")

if submitted_beam:
    import math
    # 生コン
    beam_m3 = beam_len * (b/1000.0) * (h/1000.0) * (1.0 + conc_waste_b/100.0)

    # 配筋（係数）
    rebar_kg = beam_m3 * rebar_coef
    tie_kg   = beam_m3 * tie_coef

    # 型枠（パネル：1820×910・両面）
    avail = [200,300,450,600,900]
    H_use = next((x for x in avail if x>=h), avail[-1])
    sheet_len = 1.82
    sheet_h_m = H_use/1000.0
    area_per_sheet = sheet_len * sheet_h_m
    gross_area = beam_len * sheet_h_m * 2 * (1.0 + form_waste_b/100.0)
    sheets = math.ceil(gross_area / area_per_sheet)
    screws = sheets * screws_per_sheet_b

    # Pコン・セパ・サンギ（450×450固定）
    pitch = 0.45
    cols = math.ceil(beam_len / pitch) + 1
    rows = max(1, math.ceil((H_use/1000.0) / pitch))
    positions = math.ceil(cols * rows * (1.0 + form_waste_b/100.0))
    sepa_qty = positions               # 本（1か所=1本）
    pcon_qty = positions * 2           # 個（両端）
    sanki_m  = positions * (2.0 if sanki_both_b else 1.0)

    st.success("立上り梁 数量")
    st.write({
        "生コン(m³)": round(beam_m3,3),
        "鉄筋(kg)": round(rebar_kg,1),
        "結束線(kg)": round(tie_kg,1),
        "型枠 採用高さ(mm)": H_use,
        "コンパネ(枚)": sheets,
        "固定ビス(本)": screws,
        "セパ(本)": sepa_qty,
        "Pコン(個)": pcon_qty,
        "サンギ30角(m)": round(sanki_m,1),
        "ピッチ": "450×450（両方向）",
    })

# === 見積への上書き反映（立上り） ===
reflect_beam = st.radio(
    "見積への反映（立上り）",
    ["反映しない", "上書き反映"],
    index=0,
    key="reflect_beam"
)

if reflect_beam == "上書き反映":
    st.session_state.setdefault("pick_state", {"selected": set(), "qty": {}})
    st.session_state.setdefault("auto_injected", {"foundation_beam": {}})
    S  = st.session_state["pick_state"]
    AI = st.session_state["auto_injected"]

    # 鉄筋(kg) → D13の "m" 換算（見積の商品は m 単価のため）
    d13_kgpm = REBAR_KG_PER_M.get("D13", 0.0)
    rebar_d13_m = float(rebar_kg / d13_kgpm) if d13_kgpm > 0 else 0.0

    new_items = {
        rmx_item_b[0]: float(beam_m3),          # 生コン m3
        "rebar_D13_SD295A": rebar_d13_m,        # 鉄筋 D13（m換算）
        "tie_wire_band5_350": float(tie_kg),    # 結束線 kg
        "conpa_screw_35": float(screws),        # コンパネビス 本
        # ★ITEMS未登録のため見積反映は保留（数量は上で表示/CSVに出ています）
        # "form_panel_1820x910": float(sheets),  # コンパネ枚
        # "pcon_...": float(pcon_qty),           # Pコン
        # "sepa_...": float(sepa_qty),           # セパ
        # "sanki_30_square": float(sanki_m),     # サンギ m
    }

    # 非累積の上書き
    prev = AI.get("foundation_beam", {}) or {}
    for iid, new_q in new_items.items():
        cur = float(S["qty"].get(iid, 0.0)); prv = float(prev.get(iid, 0.0))
        nxt = cur - prv + float(new_q)
        if nxt <= 0:
            S["qty"].pop(iid, None); S["selected"].discard(iid)
        else:
            S["qty"][iid] = nxt; S["selected"].add(iid)
    for iid in set(prev.keys()) - set(new_items.keys()):
        cur = float(S["qty"].get(iid, 0.0)); prv = float(prev.get(iid, 0.0))
        nxt = cur - prv
        if nxt <= 0:
            S["qty"].pop(iid, None); S["selected"].discard(iid)
        else:
            S["qty"][iid] = nxt; S["selected"].add(iid)

    AI["foundation_beam"] = dict(new_items)
    st.success("立上り梁を見積に上書き反映しました。")
    st.rerun()

    # ===（立上り梁の st.write(...) の直後に追記）===

reflect_beam = st.radio("見積への反映（立上り）", ["反映しない","上書き反映"], index=0, key="reflect_beam")

if reflect_beam == "上書き反映":
    st.session_state.setdefault("pick_state", {"selected": set(), "qty": {}})
    st.session_state.setdefault("auto_injected", {"foundation_beam": {}})
    S  = st.session_state["pick_state"]
    AI = st.session_state["auto_injected"]

    # 鉄筋(kg) → D13の m 換算（見積の商品は m 単価）
    d13_kgpm = REBAR_KG_PER_M.get("D13", 0.0)
    rebar_d13_m = float(rebar_kg / d13_kgpm) if d13_kgpm>0 else 0.0

    new_items = {
        rmx_item_b[0]: float(beam_m3),                    # 生コン m3
        "rebar_D13_SD295A": rebar_d13_m,                  # 鉄筋 D13 を m換算で
        "tie_wire_band5_350": float(tie_kg),              # 結束線 kg
        "conpa_screw_35": float(screws),                  # コンパネビス 本
        # ★以下はITEMS未登録：数量は出力済だが見積反映は保留
        # "form_panel_1820x910": float(sheets),            # パネル枚数
        # "pcon_..." : float(pcon_qty),                    # Pコン
        # "sepa_..." : float(sepa_qty),                    # セパ
        # "sanki_30_square": float(sanki_m),               # サンギ30角 m
    }

    prev = AI.get("foundation_beam", {}) or {}
    for iid, new_q in new_items.items():
        cur = float(S["qty"].get(iid, 0.0)); prv = float(prev.get(iid, 0.0))
        nxt = cur - prv + float(new_q)
        if nxt <= 0:
            S["qty"].pop(iid, None); S["selected"].discard(iid)
        else:
            S["qty"][iid] = nxt; S["selected"].add(iid)
    for iid in set(prev.keys()) - set(new_items.keys()):
        cur = float(S["qty"].get(iid, 0.0)); prv = float(prev.get(iid, 0.0))
        nxt = cur - prv
        if nxt <= 0:
            S["qty"].pop(iid, None); S["selected"].discard(iid)
        else:
            S["qty"][iid] = nxt; S["selected"].add(iid)

    AI["foundation_beam"] = dict(new_items)
    st.success("立上り梁を見積に上書き反映しました。")
    st.rerun()

    # === 見積への上書き反映（立上り） ===
reflect_beam = st.radio(
    "見積への反映（立上り）",
    ["反映しない", "上書き反映"],
    index=0,
    key="reflect_beam_v2"   # ← ユニークなキー名に変更
)


    # CSV
    import pandas as pd
    df_beam = pd.DataFrame([{
        "梁延長(m)": round(beam_len,2),
        "幅b(mm)": b, "成h(mm)": h,
        "生コン(m³)": round(beam_m3,3),
        "鉄筋(kg)": round(rebar_kg,1),
        "結束線(kg)": round(tie_kg,1),
        "型枠高さ(mm)": H_use,
        "パネル(枚)": sheets, "ビス(本)": screws,
        "セパ(本)": sepa_qty, "Pコン(個)": pcon_qty,
        "サンギ(m)": round(sanki_m,1)
    }])
    st.download_button("↓ 立上り梁 明細CSV",
        data=df_beam.to_csv(index=False).encode("utf-8-sig"),
        file_name="beam_uprise.csv", mime="text/csv")




# -------------------------------------
# 履歴（任意表示）
# -------------------------------------
show_hist = st.checkbox("仕入先ごとの履歴を表示する", value=False)
if show_hist:
    st.markdown("### 履歴（商品別・仕入先別）")
    for item_id, meta in ITEMS_D.items():
        g = NORM[NORM["item_id"]==item_id].sort_values(["date","vendor"]) 
        with st.expander(f"{meta['name']}｜{meta['spec']}（{meta['category']}）【{meta['base_unit']}】"):
            if g.empty:
                st.info("履歴データがありません。")
            else:
                show = g[["date","vendor","invoice_unit","unit_price","qty_per_invoice_unit","standard","diameter","price_per_base","detail","source"]].copy()
                show.rename(columns={
                    "date":"日付","vendor":"仕入先","invoice_unit":"伝票単位","unit_price":"単価","qty_per_invoice_unit":"入数",
                    "standard":"規格","diameter":"径","price_per_base":"基準単価","detail":"換算","source":"伝票"
                }, inplace=True)
                st.dataframe(show, use_container_width=True, height=260)

st.caption("© VELOBI Cost — 商品→単価→仕入先履歴の順に管理。ヴェロビ思想：入力最小／内部で安全に補正／一貫フォーマット出力。")
