import streamlit as st
import json
import os
import logging

logger = logging.getLogger(__name__)

# ページ全体の設定（横幅広め・タイトルなど）
st.set_page_config(page_title="マンション建替シミュレーション", layout="wide")

# ちょっとした見た目の調整用スタイル
st.markdown(
    """
    <style>
      .block-container { padding-top: 1.2rem; }
      .section-card {
        padding: 1.0rem 1.2rem; border-radius: 10px; border: 1px solid #eee; background: #fafafa;
      }
      div[data-testid=\"stMetricValue\"] { font-size: 1.6rem; }
      div[data-testid=\"stMetricDelta\"] { font-size: 0.9rem; }
      .small-note { color:#666; font-size:0.9rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("マンション建替シミュレーション")
st.caption("入力と結果を見やすく整理しました。タブで操作できます。")

# 保存先フォルダの設定
folder_name = st.text_input(
    "結果を保存するフォルダ名（空欄可）",
    value="",
    help="入力すると results/＜フォルダ名＞ 配下に保存します。空欄なら results/ 配下に保存します。",
)
RESULTS_DIR = os.path.join("results", folder_name) if folder_name else "results"
try:
    os.makedirs(RESULTS_DIR, exist_ok=True)
except OSError as e:
    logger.warning("フォルダ作成に失敗: %s", e)
    st.warning(f"保存先フォルダの作成に失敗しました: {e}")
    RESULTS_DIR = "results"
    os.makedirs(RESULTS_DIR, exist_ok=True)

# セッション状態の初期化・検証
if "results" not in st.session_state:
    st.session_state.results = None
elif not isinstance(st.session_state.results, (dict, type(None))):
    logger.warning("セッション状態が不正です。リセットします。")
    st.session_state.results = None


# 入力 → 結果 → 保存/読み込み の順でタブ化
tab_input, tab_result, tab_store = st.tabs(["1. 入力", "2. 結果", "3. 保存/読み込み"])


def calculate_results(
    your_private_area_before_sqm: float,
    construction_cost_per_private_area_tsubo: float,
    sales_price_tsubo: float,
    other_expenses_rate: float,
    reserved_floor_purchase_price_rate: float,
    total_floor_area_before_sqm: float,
    total_private_area_before_sqm: float,
    total_floor_area_after_sqm: float,
    total_private_area_after_sqm: float,
):
    # 面積・単価換算
    construction_cost_per_total_floor_area_tsubo = (
        construction_cost_per_private_area_tsubo * total_private_area_after_sqm / total_floor_area_after_sqm
    )
    construction_cost_per_total_floor_area_sqm = construction_cost_per_total_floor_area_tsubo / 3.3
    construction_cost = construction_cost_per_total_floor_area_sqm * total_floor_area_after_sqm
    total_project_cost = construction_cost * other_expenses_rate
    project_cost_per_private_area_sqm = total_project_cost / total_private_area_after_sqm
    sales_price_sqm = sales_price_tsubo / 3.3
    reserved_floor_purchase_price_tsubo = sales_price_tsubo * reserved_floor_purchase_price_rate
    reserved_floor_purchase_price_sqm = reserved_floor_purchase_price_tsubo / 3.3

    # 面積バランス計算
    reserved_floor_area_sqm = total_project_cost / reserved_floor_purchase_price_sqm
    ownership_floor_area_sqm = total_private_area_after_sqm - reserved_floor_area_sqm
    reduced_area_ratio = ownership_floor_area_sqm / total_private_area_before_sqm

    # あなたの結果
    your_private_area_after_sqm = your_private_area_before_sqm * reduced_area_ratio
    your_private_area_sellingprice = int(round(your_private_area_after_sqm * sales_price_sqm, 0))
    your_cost_to_acquire_area_before = int(
        round((your_private_area_before_sqm - your_private_area_after_sqm) * reserved_floor_purchase_price_sqm, 0)
    )

    # 表示用のまとめ
    results = {
        "減歩率（マンション共通・%）": reduced_area_ratio * 100,
        "取得できる専有面積（平米）": your_private_area_after_sqm,
        "その換算売却価格（円）": your_private_area_sellingprice,
        "同面積取得に必要な負担額（円）": your_cost_to_acquire_area_before,
        # 詳細（必要に応じて確認）
        "詳細:工事単価（床面積当・坪）": construction_cost_per_total_floor_area_tsubo,
        "詳細:工事単価（床面積当・平米）": construction_cost_per_total_floor_area_sqm,
        "詳細:建築工事費（円）": construction_cost,
        "詳細:総事業費（円）": total_project_cost,
        "詳細:総事業費（専有平米当・円）": project_cost_per_private_area_sqm,
        "詳細:販売価格（平米・円）": sales_price_sqm,
        "詳細:保留床買取原価（坪・円）": reserved_floor_purchase_price_tsubo,
        "詳細:保留床買取原価（平米・円）": reserved_floor_purchase_price_sqm,
        "詳細:保留床面積（平米）": reserved_floor_area_sqm,
        "詳細:権利床面積（平米）": ownership_floor_area_sqm,
    }
    return results


with tab_input:
    st.markdown("#### 条件の入力")
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    with st.form("input_form"):
        st.markdown("##### あなたの情報")
        col_a1, _ = st.columns([1, 1])
        with col_a1:
            your_private_area_before_sqm = st.number_input(
                "建替前の専有面積（平米）", value=77.0, step=1.0, min_value=0.0
            )

        st.markdown("##### コスト・価格条件")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            construction_cost_per_private_area_tsubo = st.number_input(
                "工事単価（専有平米→共有含む床・坪単価に換算）",
                value=2_500_000.0,
                step=100_000.0,
                min_value=0.0,
                help="専有面積当たりの坪単価（目安）",
            )
        with c2:
            sales_price_tsubo = st.number_input(
                "販売価格（坪・円）",
                value=7_500_000.0,
                step=100_000.0,
                min_value=0.0,
            )
        with c3:
            other_expenses_rate = st.number_input(
                "建築工事費以外の事業費掛率",
                value=1.25,
                step=0.01,
                min_value=0.0,
                help="例: 1.25 で 25% 上乗せ",
            )
        with c4:
            reserved_floor_purchase_price_rate = st.number_input(
                "保留床買取価格の原価率",
                value=0.70,
                step=0.01,
                min_value=0.0,
                max_value=1.0,
            )

        st.markdown("##### 建替前の条件")
        b1, b2 = st.columns(2)
        with b1:
            total_floor_area_before_sqm = st.number_input(
                "総床面積（平米・建替前）", value=2398.0, step=1.0, min_value=0.0
            )
        with b2:
            total_private_area_before_sqm = st.number_input(
                "総専有面積（平米・建替前）", value=1893.0, step=1.0, min_value=0.0
            )

        st.markdown("##### 建替後の条件")
        a1, a2 = st.columns(2)
        with a1:
            total_floor_area_after_sqm = st.number_input(
                "総床面積（平米・建替後）", value=4628.0, step=1.0, min_value=0.0
            )
        with a2:
            total_private_area_after_sqm = st.number_input(
                "総専有面積（平米・建替後）", value=3041.0, step=1.0, min_value=0.0
            )

        submitted = st.form_submit_button("計算する", use_container_width=True)

        if submitted:
            st.session_state.results = calculate_results(
                your_private_area_before_sqm,
                construction_cost_per_private_area_tsubo,
                sales_price_tsubo,
                other_expenses_rate,
                reserved_floor_purchase_price_rate,
                total_floor_area_before_sqm,
                total_private_area_before_sqm,
                total_floor_area_after_sqm,
                total_private_area_after_sqm,
            )
    st.markdown("</div>", unsafe_allow_html=True)


with tab_result:
    st.markdown("#### 計算結果")
    if st.session_state.results:
        # 主要KPIをメトリクス表示
        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("減歩率（共通）", f"{st.session_state.results['減歩率（マンション共通・%）']:.2f}%")
        with m2:
            st.metric(
                "取得できる専有面積",
                f"{st.session_state.results['取得できる専有面積（平米）']:.2f} 平米",
            )
        with m3:
            st.metric(
                "同面積取得に必要な負担額",
                f"{st.session_state.results['同面積取得に必要な負担額（円）']:,} 円",
            )

        st.markdown("##### 詳細内訳")
        with st.expander("詳細を表示 / 非表示"):
            for key, value in st.session_state.results.items():
                if key.startswith("詳細:"):
                    # 値の表示フォーマット（円はカンマ区切り、小数は2桁）
                    if isinstance(value, (int,)):
                        st.write(f"{key.replace('詳細:', '')}: {value:,}")
                    else:
                        st.write(f"{key.replace('詳細:', '')}: {value:,.2f}")

        st.markdown("##### 一覧")
        # 見やすい一覧（主要項目のみ）
        show_items = [
            ("減歩率（マンション共通・%）", st.session_state.results["減歩率（マンション共通・%）"], "%"),
            ("取得できる専有面積（平米）", st.session_state.results["取得できる専有面積（平米）"], "平米"),
            ("その換算売却価格（円）", st.session_state.results["その換算売却価格（円）"], "円"),
            ("同面積取得に必要な負担額（円）", st.session_state.results["同面積取得に必要な負担額（円）"], "円"),
        ]
        for label, val, unit in show_items:
            if isinstance(val, int):
                st.write(f"- {label}: {val:,} {unit if unit!='円' else ''}")
            else:
                st.write(f"- {label}: {val:,.2f} {unit if unit!='円' else ''}")

        # ダウンロード（JSON）
        st.download_button(
            "結果をJSONでダウンロード",
            data=json.dumps(st.session_state.results, ensure_ascii=False, indent=2).encode("utf-8"),
            file_name="simulation_results.json",
            mime="application/json",
            use_container_width=True,
        )
    else:
        st.info("入力タブで条件を入れて『計算する』を押してください。")


with tab_store:
    st.markdown("#### 保存 / 読み込み")
    st.markdown(
        f"<div class='small-note'>保存先: <code>{RESULTS_DIR}</code></div>",
        unsafe_allow_html=True,
    )
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)

    c1, c2 = st.columns([2, 1])
    with c1:
        file_name = st.text_input("保存ファイル名（拡張子不要）", value="")
    with c2:
        can_save = st.session_state.results is not None and bool(file_name.strip())
        if st.button("結果を保存", use_container_width=True, disabled=not can_save):
            try:
                os.makedirs(RESULTS_DIR, exist_ok=True)
                with open(os.path.join(RESULTS_DIR, f"{file_name}.json"), "w", encoding="utf-8") as f:
                    json.dump(st.session_state.results, f, ensure_ascii=False, indent=4)
                st.success(f"保存しました: {file_name}.json")
            except OSError as e:
                st.error(f"保存中にエラーが発生しました: {e}")

    st.divider()

    # 保存された結果の読み込み
    try:
        saved_files = sorted([f for f in os.listdir(RESULTS_DIR) if f.endswith(".json")])
    except OSError as e:
        logger.warning("ファイル一覧の取得に失敗: %s", e)
        st.warning(f"保存先フォルダにアクセスできません: {e}")
        saved_files = []
    cols = st.columns([2, 1])
    with cols[0]:
        selected_file = st.selectbox("読み込むファイルを選択", saved_files)
    with cols[1]:
        if st.button("結果を読み込む", use_container_width=True, disabled=(len(saved_files) == 0)):
            try:
                with open(os.path.join(RESULTS_DIR, selected_file), "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                if not isinstance(loaded, dict):
                    st.error("ファイルの形式が正しくありません。")
                else:
                    st.session_state.results = loaded
                    st.success(f"読み込みました: {selected_file}")
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                st.error(f"ファイルの解析に失敗しました: {e}")
            except OSError as e:
                st.error(f"ファイルの読み込みに失敗しました: {e}")

    st.markdown("</div>", unsafe_allow_html=True)
