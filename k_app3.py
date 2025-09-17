# -*- coding: utf-8 -*-
"""
原価管理MVP｜商品主軸表示（ヴェロビ式）
- CSV不要。初期データをコード内に同梱。
- 商品→採用単価（◎）/ 最新（〇）/ 平均（▲）を表示。
- 履歴は仕入先ごとに展開表示。
- 単価入力フォームで伝票を追記可能（再現性のためアプリ内で一元管理）。

使い方：
$ streamlit run app.py
"""
import math
from datetime import date, datetime
import pandas as pd
import numpy as np
import streamlit as st

st.set_page_config(page_title="原価管理MVP（商品主軸・宮田金物 初期登録）", layout="wide")
st.title("原価管理MVP｜商品主軸・宮田金物 初期登録版")

# ===============================
# 初期データ（同梱）
# ===============================
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

# 径→kg/m（JISの実務値）
REBAR_KG_PER_M = {
    "D6":0.222,"D10":0.617,"D13":0.995,"D16":1.560,"D19":2.250,
    "D22":2.980,"D25":3.980,"D29":5.040,"D32":6.350,"D35":7.990,
    "D38":9.860,"D41":11.90,
}

# 価格履歴（宮田金物）
PRICES_INIT = pd.DataFrame([
    ["2025-03-21","宮田金物","rebar_D10_SD295A","SD295A","D10","kg",141,None,"伝票279300"],
    ["2025-03-21","宮田金物","rebar_D13_SD295A","SD295A","D13","kg",139,None,"伝票279300"],
    ["2025-03-21","宮田金物","rebar_D10_NA","無規格","D10","kg",139,None,"伝票272xxx"],
    ["2025-02-28","宮田金物","rebar_D10_NA","無規格","D10","kg",138,None,"伝票272896"],
    ["2024-11-30","宮田金物","rebar_D16_SD345","SD345","D16","kg",139,None,"伝票279458"],
    ["2024-10-31","宮田金物","rebar_D16_SD345","SD345","D16","kg",134,None,"伝票273079"],

    ["2024-11-30","宮田金物","cdmesh_6_150","", "", "枚",1300,None,"伝票279192"],

    ["2025-02-28","宮田金物","tie_wire_band5_350","", "", "kg",290,None,"伝票279150"],
    ["2024-09-30","宮田金物","tie_wire_band5_350","", "", "kg",260,None,"伝票272896"],
    ["2025-03-31","宮田金物","tie_wire_black5_300","", "", "kg",290,None,"伝票279458"],

    ["2024-12-18","宮田金物","mokkons_B200","", "", "本",23,None,"伝票275954"],
    ["2025-03-21","宮田金物","mokkons_B200","", "", "本",25,None,"伝票279300"],

    ["2024-11-18","宮田金物","anchor_btn_1_2x240","", "", "本",150,None,"伝票275036"],

    ["2025-02-14","宮田金物","conc_sykoro_4x5x6","", "", "個",25,None,"伝票277903"],

    ["2025-03-26","宮田金物","conpa_screw_35","", "", "箱",2500,1000,"伝票279290"],
    ["2025-02-10","宮田金物","conpa_screw_35","", "", "箱",2200,1000,"伝票277660"],

    ["2024-11-18","宮田金物","nut_chrome_M12","", "", "個",14,None,"伝票275036"],
    ["2025-03-27","宮田金物","nut_zinc_1_2","", "", "個",13,None,"伝票279394"],
    ["2025-03-27","宮田金物","washer_zinc_1_2","", "", "個",17,None,"伝票279394"],
    ["2024-11-18","宮田金物","washer_zinc_16mm","", "", "個",15,None,"伝票275036"],

    ["2025-02-18","宮田金物","paint_tough_white","", "", "本",220,None,"伝票278032"],
    ["2025-02-18","宮田金物","paint_tough_red","", "", "本",220,None,"伝票278032"],
    ["2025-02-14","宮田金物","paint_tough_yellow","", "", "本",220,None,"伝票277903"],

    ["2025-02-18","宮田金物","course_thread_65","", "", "束",1000,50,"伝票278032"],
    ["2025-02-18","宮田金物","course_thread_75","", "", "束",1100,50,"伝票278032"],

    ["2025-02-14","宮田金物","boardnail_16x32","", "", "本",6,None,"伝票277903"],
], columns=["date","vendor","item_id","standard","diameter","invoice_unit","unit_price","qty_per_invoice_unit","source"])

# ===============================
# セッション初期化
# ===============================
if "prices_raw" not in st.session_state:
    st.session_state["prices_raw"] = PRICES_INIT.copy()

# 商品辞書
ITEMS_D = ITEMS.to_dict(orient="index")

# ===============================
# ユーティリティ
# ===============================
def parse_date(x):
    try:
        return pd.to_datetime(x).date()
    except Exception:
        return None

def base_unit(item_id):
    return ITEMS_D[item_id]["base_unit"]

def units_per_box(item_id):
    return ITEMS_D[item_id]["units_per_box"]

def is_rebar(item_id):
    return ITEMS_D[item_id]["category"] == "鉄筋" and ITEMS_D[item_id]["base_unit"] == "m"

# 単価をベース単位へ正規化
# - 鉄筋(m基準): kg単価→m単価に換算（円/m=円/kg×kg/m）
# - 箱/束売り: 1箱(束)あたり本数で按分
# - 同一単位はそのまま

def normalize_price(row):
    item_id = row["item_id"]
    inv_unit = str(row["invoice_unit"]) if row["invoice_unit"] is not None else ""
    price = float(row["unit_price"]) if row["unit_price"] is not None else np.nan
    qpu = row["qty_per_invoice_unit"]  # e.g., 箱入数 or 束入数

    bunit = base_unit(item_id)

    # 箱・束 → 本に按分（商品固有の箱入数/束入数を優先、なければqty_per_invoice_unit）
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

    # 非鉄筋：単位をベースへ（同一ならそのまま）
    if inv_unit == bunit:
        return price, f"{bunit}単価"

    # 例：箱/束が上で本になっていれば、base_unitが本ならOK
    if inv_unit == "本" and bunit == "本":
        return price, "本単価(按分済)"

    return np.nan, f"未対応({inv_unit}→{bunit})"


def adopt_price(group_df, policy):
    """ポリシー別に採用単価を決定。返り値: price, label, picked_row"""
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
        idx = last["price_per_base"].idxmax()  # 同日複数なら高い方
        r = last.loc[idx]
        return float(r["price_per_base"]), f"最新採用｜{r['vendor']}｜{r['date'].date()}｜{r['source']}", r
    else:  # 期間平均
        return float(np.round(df["price_per_base"].mean(),1)), f"期間平均（{len(df)}件）", None

# ===============================
# オプション（期間 / ポリシー）
# ===============================
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
for i, r in flt.iterrows():
    p, note = normalize_price(r)
    norm_rows.append({
        **r.to_dict(),
        "price_per_base": np.round(p,1) if not pd.isna(p) else np.nan,
        "detail": note
    })
NORM = pd.DataFrame(norm_rows)

# ===============================
# 商品主軸：◎〇▲ と履歴
# ===============================
st.markdown("### 商品一覧（商品→採用単価→履歴の順に表示）")

records = []
for item_id, meta in ITEMS_D.items():
    g = NORM[NORM["item_id"]==item_id]
    # ◎採用
    price_adopt, note_adopt, picked = adopt_price(g, policy)
    # 〇最新
    price_latest, note_latest, _ = adopt_price(g, "最新日付")
    # ▲平均
    price_avg, note_avg, _ = adopt_price(g, "期間平均")

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
st.dataframe(TABLE, use_container_width=True, height=420)

st.caption("※ 鉄筋は 円/kg→円/m に厳密換算。箱/束は按分し、本単価に統一。丸めは小数1位四捨五入。")

# 履歴表示（商品ごとに展開）
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

# ===============================
# 伝票入力（追加登録）
# ===============================
st.markdown("---")
st.subheader("伝票入力（価格履歴の追加）")
with st.form("invoice_add"):
    c1, c2, c3 = st.columns(3)
    d = c1.date_input("日付", value=date.today())
    vendor = c2.text_input("仕入先", value="宮田金物")
    item_sel = c3.selectbox("商品", list(ITEMS_D.keys()), format_func=lambda i: f"{ITEMS_D[i]['name']}｜{ITEMS_D[i]['spec']}（{i}）")

    c4, c5, c6 = st.columns(3)
    inv_unit = c4.selectbox("伝票単位", ["kg","m","本","箱","束","枚","個"], index=0)
    unit_price = c5.number_input("単価（伝票単位あたり）", min_value=0.0, step=1.0)
    qty_per = c6.number_input("入数（箱/束など）", min_value=0.0, step=1.0, value=0.0)

    c7, c8, c9 = st.columns(3)
    standard = c7.text_input("規格（例：SD295A / 無規格）")
    diameter = c8.text_input("径（例：D10、鉄筋のみ）")
    source = c9.text_input("伝票番号/備考")

    submitted = st.form_submit_button("この内容で履歴に追加する")
    if submitted:
        new_row = {
            "date": pd.to_datetime(d),
            "vendor": vendor,
            "item_id": item_sel,
            "standard": standard,
            "diameter": diameter,
            "invoice_unit": inv_unit,
            "unit_price": unit_price,
            "qty_per_invoice_unit": (None if qty_per==0 else qty_per),
            "source": source,
        }
        st.session_state["prices_raw"] = pd.concat([st.session_state["prices_raw"], pd.DataFrame([new_row])], ignore_index=True)
        st.success("履歴を追加しました。上の表が更新されています。")

# ===============================
# エクスポート（任意）：採用単価のスナップショット
# ===============================
st.markdown("---")
st.subheader("採用単価スナップショット（任意）")
st.caption("※ 再現性のため、必要に応じてCSVでエクスポートできます（閲覧のみでOK）。")
exp = TABLE.copy()
exp.rename(columns={
    "商品ID":"item_id","カテゴリ":"category","商品名":"name","規格/仕様":"spec","基準単位":"base_unit",
    "◎ 採用単価":"adopt_price","〇 最新単価":"latest_price","▲ 期間平均":"avg_price","採用注記":"adopt_note"
}, inplace=True)
exp_csv = exp.to_csv(index=False).encode("utf-8-sig")
st.download_button("↓ 採用単価CSVをダウンロード", data=exp_csv, file_name=f"adopt_prices_{datetime.now():%Y%m%d}.csv", mime="text/csv")

st.caption("© VELOBI Cost — 商品→単価→仕入先履歴の順に管理。ヴェロビ思想：入力最小／内部で安全に補正／一貫フォーマット出力。")

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
