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

if submitted:
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

        rebar_price = float(TABLE.loc[TABLE["商品ID"]==rebar_choice[0], "◎ 採用単価"].values[0])
        tie_price   = float(TABLE.loc[TABLE["商品ID"]=="tie_wire_band5_350", "◎ 採用単価"].values[0])
        sykoro_price= float(TABLE.loc[TABLE["商品ID"]=="conc_sykoro_4x5x6", "◎ 採用単価"].values[0])
        rebar_cost = total_m * rebar_price
        tie_cost   = tie_kg * tie_price
        sykoro_cost= sykoro_pcs * sykoro_price
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

        mesh_price = float(TABLE.loc[TABLE["商品ID"]=="cdmesh_6_150", "◎ 採用単価"].values[0])
        mesh_cost  = mesh_sheets * mesh_price
        tie_cost_m = tie_kg * tie_price
        sykoro_cost_m = sykoro_pcs * sykoro_price
        total_cost_mesh = mesh_cost + tie_cost_m + sykoro_cost_m

        # 表示
        st.success("比較結果（税抜・原価）")
        colA, colB = st.columns(2)
        with colA:
            st.markdown("#### ■ 鉄筋方式")
            st.write({"総延長(m)": round(total_m,1),"重量(kg)": round(total_kg,1),
                      "定尺本数(概算)": bars_stock,"結束線(kg)": round(tie_kg,2),
                      "サイコロ(個)": int(sykoro_pcs),"小計(円)": round(total_cost_rebar)})
        with colB:
            st.markdown("#### ■ メッシュ方式")
            st.write({"枚数": int(mesh_sheets),"結束線(kg)": round(tie_kg,2),
                      "サイコロ(個)": int(sykoro_pcs),"小計(円)": round(total_cost_mesh)})

        # ---- 見積カート反映（非累積）----
        st.session_state.setdefault("pick_state", {"selected": set(), "qty": {}})
        st.session_state.setdefault("auto_injected", {"rebar": {}, "mesh": {}})
        S  = st.session_state["pick_state"]
        AI = st.session_state["auto_injected"]

        def apply_mode(mode: str, new_items: dict):
            prev = AI.get(mode, {}) or {}
            # 差し戻し＆上書き
            for iid, new_q in new_items.items():
                cur = float(S["qty"].get(iid, 0.0))
                prev_q = float(prev.get(iid, 0.0))
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

        # 今回数量
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

        # 排他的に上書き
        if mode == "鉄筋方式":
            apply_mode("mesh", {})           # メッシュをクリア
            apply_mode("rebar", rebar_items)
            st.success("鉄筋方式をカートに上書きしました。"); st.rerun()
        elif mode == "メッシュ方式":
            apply_mode("rebar", {})          # 鉄筋をクリア
            apply_mode("mesh", mesh_items)
            st.success("メッシュ方式をカートに上書きしました。"); st.rerun()


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
