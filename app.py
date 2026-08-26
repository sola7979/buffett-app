# buffett-app
import numpy as np
import requests
import streamlit as st
import yfinance as yf

# 画面設定
st.set_page_config(
    page_title="Buffett AI",
    layout="centered",
)

st.title("🏰 総合分析ツール")
st.caption("財務・モート・AI解析")

# 記憶保持の設定
if "company_name" not in st.session_state:
    st.session_state.company_name = "未取得"
if "fcf_list" not in st.session_state:
    st.session_state.fcf_list = [10.0, 10.0, 10.0]
if "avg_fcf" not in st.session_state:
    st.session_state.avg_fcf = 10.0
if "net_debt" not in st.session_state:
    st.session_state.net_debt = 215.0
if "shares" not in st.session_state:
    st.session_state.shares = 5002.0
if "current_price" not in st.session_state:
    st.session_state.current_price = 1263.0
if "beta" not in st.session_state:
    st.session_state.beta = 1.0
if "equity_ratio" not in st.session_state:
    st.session_state.equity_ratio = 0.50
if "sector" not in st.session_state:
    st.session_state.sector = "未取得"
if "industry" not in st.session_state:
    st.session_state.industry = "未取得"
if "ai_report" not in st.session_state:
    st.session_state.ai_report = "未実行"

# 入力値の保持
if "fcf_base" not in st.session_state:
    st.session_state.fcf_base = 10.0
if "g_stage1" not in st.session_state:
    st.session_state.g_stage1 = 8.0
if "g_terminal" not in st.session_state:
    st.session_state.g_terminal = 0.5

# チェック保持
if "m1" not in st.session_state:
    st.session_state.m1 = False
if "m2" not in st.session_state:
    st.session_state.m2 = False
if "m3" not in st.session_state:
    st.session_state.m3 = False
if "m4" not in st.session_state:
    st.session_state.m4 = False
if "m5" not in st.session_state:
    st.session_state.m5 = False

# API入力 (衝突防止のkeyを追加)
st.subheader("🔑 1. AI鍵設定")
api_key = st.text_input(
    "Gemini APIキーを入力",
    type="password",
    key="user_gemini_key",
)

st.write("---")
st.subheader("🏢 2. 証券コード入力")
ticker_input = st.text_input(
    "コード4桁",
    value="7203",
    key="target_ticker_code",
)

if st.button(
    "🔍 解析を実行",
    use_container_width=True,
    key="exec_analysis_btn",
):
    if not api_key:
        st.error("キーを入力してください")
    elif (
        ticker_input
        and len(ticker_input) == 4
        and ticker_input.isdigit()
    ):
        try:
            with st.spinner("解析中..."):
                t_code = f"{ticker_input}.T"
                ticker = yf.Ticker(t_code)
                info = ticker.info

                st.session_state.company_name = (
                    info.get("longName")
                    or info.get("shortName")
                    or f"コード: {ticker_input}"
                )
                st.session_state.current_price = (
                    info.get("currentPrice")
                    or info.get("regularMarketPrice")
                    or st.session_state.current_price
                )
                st.session_state.shares = (
                    info.get("sharesOutstanding")
                    or (st.session_state.shares * 10000)
                ) / 10000
                st.session_state.beta = (
                    info.get("beta") or 1.0
                )
                st.session_state.sector = info.get(
                    "sector", "不明"
                )
                st.session_state.industry = info.get(
                    "industry", "不明"
                )
                b_summary = info.get(
                    "longBusinessSummary", "なし"
                )

                cf = ticker.cashflow
                bs = ticker.balance_sheet

                if (
                    not cf.empty
                    and "Operating Cash Flow" in cf.index
                    and "Investing Cash Flow" in cf.index
                ):
                    ocfs = cf.loc[
                        "Operating Cash Flow"
                    ].values
                    icfs = cf.loc[
                        "Investing Cash Flow"
                    ].values
                    fcfs = [
                        (o + i) / 100000000
                        for o, i in zip(ocfs, icfs)
                    ]
                    st.session_state.fcf_list = fcfs[:3]
                    st.session_state.avg_fcf = np.mean(
                        fcfs[:3]
                    )
                    st.session_state.fcf_base = float(
                        st.session_state.avg_fcf
                    )

                if not bs.empty:
                    t_debt = (
                        bs.loc["Total Debt"].iloc
                        if "Total Debt" in bs.index
                        else 0
                    )
                    cash = (
                        bs.loc[
                            "Cash And Cash Equivalents"
                        ].iloc
                        if "Cash And Cash Equivalents"
                        in bs.index
                        else 0
                    )
                    st.session_state.net_debt = (
                        t_debt - cash
                    ) / 100000000

                    t_assets = bs.loc[
                        "Total Assets"
                    ].iloc
                    t_equity = (
                        bs.loc[
                            "Total Equity Gross"
                            " Minority Interest"
                        ].iloc
                        if "Total Equity Gross"
                        " Minority Interest"
                        in bs.index
                        else (t_assets * 0.5)
                    )
                    st.session_state.equity_ratio = (
                        t_equity / t_assets
                    )

                # AI呼び出し
                g_url = (
                    "https://generativelanguage"
                    "://"
                    "models/gemini-2.5-flash:"
                    f"generateContent?key={api_key}"
                )
                p_text = f"""
                バフェット流のアナリストとして
                以下企業の日本語レポートを作って。
                特に技術視点、特許、R&D、AI、
                競合に対する技術の優位性や
                参入障壁(モート)を深く分析して。
                企業名: {st.session_state.company_name}
                セクター: {st.session_state.sector}
                FCF平均: {st.session_state.avg_fcf:.1f}億円
                純負債: {st.session_state.net_debt:.1f}億円
                β値: {st.session_state.beta}
                説明: {b_summary[:1500]}
                見出しは以下4つにして。
                1.財務の健康度
                2.ビジネスモデル特性
                3.技術・知財・R&D競争力
                4.総括とテクノロジーリスク
                """

                headers = {
                    "Content-Type": "application/json"
                }
                payload = {
                    "contents": [
                        {"parts": [{"text": p_text}]}
                    ]
                }

                res = requests.post(
                    g_url,
                    headers=headers,
                    json=payload,
                    timeout=20,
                )
                if res.status_code == 200:
                    r_json = res.json()
                    st.session_state.ai_report = (
                        r_json["candidates"]
                        ["content"]["parts"]["text"]
                    )
                else:
                    st.session_state.ai_report = (
                        f"エラー: {res.status_code}"
                    )

            st.success("解析が完了しました！")
        except Exception as e:
            st.warning("手動補正してください。")

# タブ作成
t1, t2, t3, t4 = st.tabs(
    ["📊 財務", "🔒 モート", "🎯 試算", "🤖 AI分析"]
)

# パラメータ計算
g_s1_parsed = st.session_state.g_stage1 / 100
g_t_parsed = st.session_state.g_terminal / 100

c_equity = 0.01 + (st.session_state.beta * 0.06)
c_wacc = (
    c_equity * st.session_state.equity_ratio
) + (0.02 * (1 - st.session_state.equity_ratio))

if g_t_parsed >= c_wacc:
    intrinsic_value, target_price = 0, 0
    ins_label, tg_label = "エラー", "エラー"
else:
    pv_s1 = 0
    fcf = st.session_state.fcf_base
    for y in range(1, 6):
        fcf = fcf * (1 + g_s1_parsed)
        pv_s1 += fcf / ((1 + c_wacc) ** y)
    pv_s2 = 0
    for y in range(6, 11):
        fcf = fcf * (1 + g_t_parsed)
        pv_s2 += fcf / ((1 + c_wacc) ** y)
    tv = (fcf * (1 + g_t_parsed)) / (c_wacc - g_t_parsed)
    pv_tv = tv / ((1 + c_wacc) ** 10)
    ev = pv_s1 + pv_s2 + pv_tv
    sh_value = ev - st.session_state.net_debt
    intrinsic_value = (sh_value * 100000000) / (
        st.session_state.shares * 10000
    )
    intrinsic_value = max(0, intrinsic_value)
    m_score = sum(
        [
            st.session_state.m1,
            st.session_state.m2,
            st.session_state.m3,
            st.session_state.m4,
            st.session_state.m5,
        ]
    )
    m_rate = 0.40 - (m_score * 0.05)
    target_price = intrinsic_value * (1 - m_rate)
    cur_p = st.session_state.current_price

    if intrinsic_value > 0:
        vs_ins = (
            (cur_p - intrinsic_value) / intrinsic_value
        ) * 100
        ins_label = (
            f"{'+' if vs_ins >= 0 else ''}"
            f"{vs_ins:.1f}%"
        )
    else:
        ins_label = "計算不可"

    if target_price > 0:
        vs_tg = (
            (cur_p - target_price) / target_price
        ) * 100
        tg_label = (
            f"{'+' if vs_tg >= 0 else ''}"
            f"{vs_tg:.1f}%"
        )
    else:
        tg_label = "計算不可"

with t1:
    st.subheader("1. 財務データの確認")
    st.text_input(
        "企業名",
        value=st.session_state.company_name,
        key="disp_company_name",
    )
    st.write(
        "過去FCF推移（億円）:",
        [round(x, 1) for x in st.session_state.fcf_list],
    )
    st.session_state.fcf_base = st.number_input(
        "予測基準FCF",
        value=float(st.session_state.fcf_base),
        key="num_fcf_base",
    )
    st.session_state.net_debt = st.number_input(
        "純有利子負債",
        value=float(st.session_state.net_debt),
        key="num_net_debt",
    )
    st.session_state.shares = st.number_input(
        "発行済株式数(万株)",
        value=float(st.session_state.shares),key="num_shares_cnt",)st.session_state.current_price = (st.number_input("現在の株価",value=float(st.session_state.current_price),key="num_cur_price",))st.session_state.beta = st.number_input("ベータ値(β)",value=float(st.session_state.beta),key="num_beta_val",)with t2:st.subheader("2. モート評価")st.session_state.m1 = st.checkbox("🔮 ブランド力", value=st.session_state.m1, key="chk_m1")st.session_state.m2 = st.checkbox("🔗 スイッチングコスト", value=st.session_state.m2, key="chk_m2")st.session_state.m3 = st.checkbox("🪙 低コスト優位性", value=st.session_state.m3, key="chk_m3")st.session_state.m4 = st.checkbox("📜 特許・許認可", value=st.session_state.m4, key="chk_m4")st.session_state.m5 = st.checkbox("🕸️ ネットワーク効果", value=st.session_state.m5, key="chk_m5")with t3:st.subheader("3. 理論株価試算")st.session_state.g_stage1 = st.number_input("今後5年の予測成長率(％)", value=float(st.session_state.g_stage1), step=0.5, key="num_g_s1")st.session_state.g_terminal = st.number_input("6年目以降の永久成長率(％)", value=float(st.session_state.g_terminal), step=0.1, key="num_g_term")st.write("---")if g_t_parsed >= c_wacc:st.error("永久成長率はWACC未満にしてください")else:st.success("試算完了")col1, col2, col3 = st.columns(3)col1.metric(label="🏪 現在株価", value=f"{int(cur_p):,} 円")col2.metric(label="🎯 適正株価", value=f"{int(intrinsic_value):,} 円", delta=f"現在値 {ins_label}", delta_color="inverse")col3.metric(label="🛡️ 買付上限", value=f"{int(target_price):,} 円", delta=f"現在値 {tg_label}", delta_color="inverse")st.write("---")st.subheader("📢 投資判断シグナル")if cur_p <= target_price: st.success("✅ 【Buy】買付上限以下です。")elif cur_p <= intrinsic_value: st.warning("⚠️ 【Hold】クッション不足です。")else: st.error("❌ 【Avoid】割高水準です。")with t4:st.subheader("🤖 AI多角的ビジネス解析")st.markdown(st.session_state.ai_report)
