import numpy as np
import requests
import streamlit as st
import yfinance as yf

st.set_page_config(
    page_title="BA",
    layout="centered"
)
st.title("🏰 投資分析")

# 状態初期化
keys = [
    "c_name", "f_list", "a_fcf", 
    "n_debt", "shs", "c_prc", 
    "bt", "eq_r", "sec", 
    "ind", "ai_rep", "f_base", 
    "g_s1", "g_t", "m1", 
    "m2", "m3", "m4", "m5"
]
vals = [
    "未取得", [10.0]*3, 10.0, 
    215.0, 5002.0, 1263.0, 
    1.0, 0.5, "未取得", 
    "未取得", "未実行", 10.0, 
    8.0, 0.5, False, 
    False, False, False, False
]
for k, v in zip(keys, vals):
    if k not in st.session_state:
        st.session_state[k] = v

st.subheader("🔑 1. 鍵設定")
api_key = st.text_input(
    "Gemini API Key",
    type="password",
    key="g_key"
)

st.subheader("🏢 2. コード入力")
t_in = st.text_input(
    "4桁数字",
    value="7203",
    key="t_code"
)

if st.button(
    "📊 データ読込",
    use_container_width=True,
    key="btn_f"
):
    if t_in.isdigit() and len(t_in)==4:
        try:
            with st.spinner("取得中"):
                t = yf.Ticker(f"{t_in}.T")
                inf = t.info
                st.session_state.c_name = (
                    inf.get("longName")
                    or inf.get("shortName")
                    or f"コード:{t_in}"
                )
                st.session_state.c_prc = (
                    inf.get("currentPrice")
                    or inf.get("regularMarketPrice")
                    or inf.get("ask")
                    or st.session_state.c_prc
                )
                st.session_state.shs = (
                    inf.get("sharesOutstanding")
                    or (st.session_state.shs*1E4)
                ) / 1E4
                st.session_state.bt = (
                    inf.get("beta") or 1.0
                )
                st.session_state.sec = (
                    inf.get("sector") or "不明"
                )
                st.session_state.ind = (
                    inf.get("industry") or "不明"
                )
                bsm = (
                    inf.get("longBusinessSummary")
                    or "なし"
                )
                st.session_state.bsum_raw = bsm

                cf = t.get_cashflow()
                if (not cf.empty) and (
                    "Operating Cash Flow" in cf.index
                ):
                    o = cf.loc["Operating Cash Flow"].values
                    i = cf.loc["Investing Cash Flow"].values
                    fs = [
                        (float(x)+float(y))/1E8 
                        for x, y in zip(o, i)
                    ]
                    if fs:
                        st.session_state.f_list = fs[:3]
                        st.session_state.a_fcf = np.mean(fs[:3])
                        st.session_state.f_base = float(
                            st.session_state.a_fcf
                        )

                bs = t.get_balance_sheet()
                if not bs.empty:
                    td = (
                        float(bs.loc["Total Debt"].iloc)
                        if "Total Debt" in bs.index 
                        else 0.0
                    )
                    cs = (
                        float(bs.loc[
                            "Cash And Cash Equivalents"
                        ].iloc)
                        if "Cash And Cash Equivalents" 
                        in bs.index else 0.0
                    )
                    st.session_state.n_debt = (td-cs)/1E8
                    ta = float(bs.loc["Total Assets"].iloc)
                    te = (
                        float(bs.loc[
                            "Total Equity Gross "
                            "Minority Interest"
                        ].iloc)
                        if "Total Equity Gross "
                        "Minority Interest" in bs.index 
                        else ta*0.5
                    )
                    st.session_state.eq_r = te / ta
            st.success("財務同期完了！")
        except Exception as e:
            st.warning("手動モード起動")

t1, t2, t3, t4 = st.tabs(
    ["📊 財務", "🔒 モート", "🎯 試算", "🤖 AI分析"]
)

# 算出
c_eq = 0.01 + (st.session_state.bt * 0.06)
c_wacc = (c_eq * st.session_state.eq_r) + (
    0.02 * (1 - st.session_state.eq_r)
)
g_s1_p = st.session_state.g_s1 / 100
g_t_p = st.session_state.g_t / 100

if g_t_p >= c_wacc:
    ins_v, tg_p = 0, 0
    ins_lbl, tg_lbl = "エラー", "エラー"
else:
    pv = 0
    f = st.session_state.f_base
    for y in range(1, 6):
        f = f * (1 + g_s1_p)
        pv += f / ((1 + c_wacc) ** y)
    for y in range(6, 11):
        f = f * (1 + g_t_p)
        pv += f / ((1 + c_wacc) ** y)
    sh_v = (
        pv + ((f * (1 + g_t_p)) / (c_wacc - g_t_p)) 
        / ((1 + c_wacc) ** 10)
    ) - st.session_state.n_debt
    ins_v = max(
        0, (sh_v * 1E8) / (st.session_state.shs * 1E4)
    )
    m_score = sum([
        st.session_state.m1, st.session_state.m2, 
        st.session_state.m3, st.session_state.m4, 
        st.session_state.m5
    ])
    tg_p = ins_v * (1 - (0.40 - (m_score * 0.05)))
    cur_p = st.session_state.c_prc
    
    if ins_v > 0:
        v_in = ((cur_p - ins_v) / ins_v) * 100
        ins_lbl = f"{'+' if v_in >= 0 else ''}{v_in:.1f}%"
    else: ins_lbl = "不可"
    
    if tg_p > 0:
        v_tg = ((cur_p - tg_p) / tg_p) * 100
        tg_lbl = f"{'+' if v_tg >= 0 else ''}{v_tg:.1f}%"
    else: tg_lbl = "不可"

with t1:
    st.subheader("財務確認")
    st.text_input(
        "企業名", value=st.session_state.c_name, 
        key="ds_n"
    )
    st.write(
        "過去FCF:", 
        [round(x, 1) for x in st.session_state.f_list]
    )
    st.session_state.f_base = st.number_input(
        "基準FCF", 
        value=float(st.session_state.f_base), 
        key="nm_fb"
    )
    st.session_state.n_debt = st.number_input(
        "純負債", 
        value=float(st.session_state.n_debt), 
        key="nm_nd"
    )
    st.session_state.shs = st.number_input(
        "株式数(万)", 
        value=float(st.session_state.shs), 
        key="nm_sh"
    )
    st.session_state.c_prc = st.number_input(
        "現在株価", 
        value=float(st.session_state.c_prc), 
        key="nm_cp"
    )
    st.session_state.bt = st.number_input(
        "β値", 
        value=float(st.session_state.bt), 
        key="nm_bt"
    )

with t2:
    st.subheader("モート評価")
    st.session_state.m1 = st.checkbox(
        "🔮 ブランド", value=st.session_state.m1, key="k1"
    )
    st.session_state.m2 = st.checkbox(
        "🔗 障壁", value=st.session_state.m2, key="k2"
    )
    st.session_state.m3 = st.checkbox(
        "🪙 低コスト", value=st.session_state.m3, key="k3"
    )
    st.session_state.m4 = st.checkbox(
        "📜 特許", value=st.session_state.m4, key="k4"
    )
    st.session_state.m5 = st.checkbox(
        "🕸️ ネット網", value=st.session_state.m5, key="k5"
    )

with t3:
    st.subheader("試算結果")
    st.session_state.g_s1 = st.number_input(
        "5年成長率(%)", 
        value=float(st.session_state.g_s1), 
        step=0.5, key="n_g1"
    )
    st.session_state.g_t = st.number_input(
        "永久成長率(%)", 
        value=float(st.session_state.g_t), 
        step=0.1, key="n_gt"
    )
    st.write("---")
    if g_t_p >= c_wacc:
        st.error("永久成長率エラー")
    else:
        st.success("計算完了")
        col1, col2, col3 = st.columns(3)
        col1.metric("🏪 現在株価", f"{int(cur_p):,}円")
        col2.metric("🎯 適正", f"{int(ins_v):,}円", f"現在 {ins_lbl}", "inverse")
        col3.metric("🛡️ 上限", f"{int(tg_p):,}円", f"現在 {tg_lbl}", "inverse")
        st.write("---")
        if cur_p <= tg_p: st.success("✅ 【Buy】買付上限以下")
        elif cur_p <= ins_v: st.warning("⚠️ 【Hold】余裕不足")
        else: st.error("❌ 【Avoid】割高")

with t4:
    st.subheader("🤖 AI分析")
    if st.button(
        "🤖 AI分析起動",
        type="primary",
        use_container_width=True,
        key="btn_ai"
    ):
        if not api_key:
            st.error("キー未入力")
        elif st.session_state.c_name == "未取得":
            st.error("財務を先に読込してください")
        else:
            try:
                with st.spinner("AI解析中..."):
                    h = "https://googleapis.com"
                    p = "/v1beta/models/gemini-2.5-flash:generateContent"
                    u = f"{h}{p}?key={api_key}"
                    txt = f"バフェット流でレポート作って。特に技術、特許、R&D、AI、競合への優位性やモートを深く分析して。企業名:{st.session_state.c_name} セクター:{st.session_state.sec} 業界:{st.session_state.ind} FCF平均:{st.session_state.a_fcf:.1f}億円 純負債:{st.session_state.n_debt:.1f}億円 β値:{st.session_state.bt} 説明:{st.session_state.get('bsum_raw','')[:500]} 見出し:1.財務健康度 2.ビジネス特性 3.技術知財R&D 4.リスク総括"
                    res = requests.post(
                        u, 
                        headers={"Content-Type": "application/json"}, 
                        json={"contents": [{"parts": [{"text": txt}]}]}, 
                        timeout=25
                    )
                    if res.status_code == 200:
                        st.session_state.ai_rep = (
                            res.json()["candidates"][0]
                            ["content"]["parts"][0]["text"]
                        )
                    else:
                        st.session_state.ai_rep = "通信エラー"
                st.success("レポート生成完了！")
            except Exception as e:
                st.error("解析失敗")
    st.write("---")
    st.markdown(st.session_state.ai_rep)
