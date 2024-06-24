import streamlit as st
import json
import os

st.title("マンション建替シミュレーション")
# 保存先ディレクトリの入力

st.subheader("Step1: 保存先フォルダの設定")
RESULTS_DIR = os.path.join("results", st.text_input("あなたの結果を保存するフォルダ名を入力してください（入力するとあとで呼び出すことができます）", ""))

# ディレクトリが存在しない場合は作成
if not os.path.exists(RESULTS_DIR):
    os.makedirs(RESULTS_DIR)
# セッション状態を初期化
if 'results' not in st.session_state:
    st.session_state.results = None

st.subheader("Step2: 条件の入力")
# ユーザー入力
your_private_area_before_sqm = st.number_input("あなたの建替前の専有面積（平米）※平米単位で上下できます", value=77, step=1)
construction_cost_per_private_area_tsubo = st.number_input("工事単価（専有面積当）（円／坪）※十万円単位で上下できます", value=2500000,step=100000)
sales_price_tsubo = st.number_input("分譲価格（円／坪）※十万円単位で上下できます", value=7500000,step=100000)
other_expenses_rate = st.number_input("建築工事費以外の事業費を含める掛率（例：1.25）", value=1.25,step=0.01)
reserved_floor_purchase_price_rate = st.number_input("保留床買取価格率（原価率）", value=0.70, step=0.01)
total_floor_area_before_sqm = st.number_input("建替前_マンションの総床面積（平米）", value=2398, step=1)
total_private_area_before_sqm = st.number_input("建替前_マンションの総専有面積（平米）", value=1893, step=1)
total_floor_area_after_sqm = st.number_input("建替後_マンションの総床面積（平米）", value=4628, step=1)
total_private_area_after_sqm = st.number_input("建替後_マンションの総専有面積（平米）", value=3041, step=1)

# 計算を行う関数
def calculate_results():
    construction_cost_per_total_floor_area_tsubo = construction_cost_per_private_area_tsubo * total_private_area_after_sqm / total_floor_area_after_sqm
    construction_cost_per_total_floor_area_sqm = construction_cost_per_total_floor_area_tsubo / 3.3
    construction_cost = construction_cost_per_total_floor_area_sqm * total_floor_area_after_sqm
    total_project_cost = construction_cost * other_expenses_rate
    project_cost_per_private_area_sqm = total_project_cost / total_private_area_after_sqm
    sales_price_sqm = sales_price_tsubo / 3.3
    reserved_floor_purchase_price_tsubo = sales_price_tsubo * reserved_floor_purchase_price_rate
    reserved_floor_purchase_price_sqm = reserved_floor_purchase_price_tsubo / 3.3
    reserved_floor_area_sqm = total_project_cost / reserved_floor_purchase_price_sqm
    ownership_floor_area_sqm = total_private_area_after_sqm - reserved_floor_area_sqm
    reduced_area_ratio = ownership_floor_area_sqm / total_private_area_before_sqm
    your_private_area_after_sqm = your_private_area_before_sqm * reduced_area_ratio
    your_private_area_sellingprice = int(round(your_private_area_after_sqm * sales_price_sqm,0))
    your_cost_to_aquire_area_before = int(round((your_private_area_before_sqm - your_private_area_after_sqm) * reserved_floor_purchase_price_sqm,0))

    results = {
        # "工事単価（共用部も含めた床面積当）（円／坪）": construction_cost_per_total_floor_area_tsubo,
        # "工事単価（共用部も含めた床面積当）（円／平米）": construction_cost_per_total_floor_area_sqm,
        # "建築工事費（円）": construction_cost,
        # "総事業費（円）": total_project_cost,
        # "総事業費（円／平米）": project_cost_per_private_area_sqm,
        # "分譲価格（円／平米）": sales_price_sqm,
        # "保留床買取価格（原価）（円／坪）": reserved_floor_purchase_price_tsubo,
        # "保留床買取価格（原価）（円／平米）": reserved_floor_purchase_price_sqm,
        # "保留床床面積（平米）": reserved_floor_area_sqm,
        # "権利床床面積（平米）": ownership_floor_area_sqm,
        "還元率（マンション共通）（％）": reduced_area_ratio * 100,
        "あなたが負担金なく取得できる専有面積（平米）": your_private_area_after_sqm,
        "その分譲価格換算（円）": your_private_area_sellingprice,
        "あなたが建替前と同じ面積を取得する場合に必要な負担金（円）": your_cost_to_aquire_area_before
    }

    return results

st.subheader("Step3: 結果の計算")
# 計算結果を表示

if st.button("計算する"):
    st.session_state.results = calculate_results()

if st.session_state.results:
    st.subheader("計算結果")
    for key, value in st.session_state.results.items():
        if isinstance(value, int):
            st.write(f"{key}: {value:,}")
        else:
            st.write(f"{key}: {value:,.2f}")

    # ファイル名の入力と保存ボタンの表示
    file_name = st.text_input("※あとで呼び出すために結果を保存するファイル名を入力してください（例: 結果１）", "")
    if st.button("結果を保存"):
        try:
            with open(f"{RESULTS_DIR}/{file_name}.json", "w") as f:
                json.dump(st.session_state.results, f, ensure_ascii=False, indent=4)
            st.success(f"結果を {file_name}.json として保存しました。")
        except Exception as e:
            st.error(f"結果の保存中にエラーが発生しました: {e}")


# 保存された結果を読み込む
st.subheader("Step4: 保存された結果を読み込んで再表示")
saved_files = [f for f in os.listdir(RESULTS_DIR) if f.endswith(".json")]
selected_file = st.selectbox("読み込むファイルを選択してください", saved_files)


if st.button("結果を表示"):
    if selected_file:
        try:
            with open(f"{RESULTS_DIR}/{selected_file}", "r") as f:
                loaded_results = json.load(f)
            st.subheader(f"{selected_file} の結果")
            for key, value in loaded_results.items():
                st.write(f"{key}: {value:,.2f}")
        except Exception as e:
            st.error(f"ファイルの読み込み中にエラーが発生しました: {e}")
    else:
        st.error("ファイルが選択されていません。")

