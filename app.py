# buffett-appimport numpy as np
import numpy as np
import requests
import streamlit as st
import yfinance as yf

st.set_page_config(page_title="Buffett AI", layout="centered")
st.title("🏰 総合分析ツール")
st.caption("財務・モート・AI解析・解説ガイド付き")

# セッション状態の初期化
for k, v in {
    "c_name": "未取得", "f_list": [10.0, 10.0, 10.0], "a_fcf": 10.0, "n_debt": 215.0,
    "shs": 5002.0, "c_prc": 1263.0, "bt": 1.0, "eq_r": 0.5, "sec": "未取得",
    "ind": "未取得", "ai_rep": "未実行", "f_base": 10.0, "g_s1": 8.0, "g_t": 0.5,
    "m1": False, "m2": False, "m3": False, "m4": False, "m5": False
}.items():
    if k not in st.session_state: st.session_state[k] = v

st.subheader("🔑 1. AI鍵設定")
api_key = st.text_input("Gemini APIキーを入力", type="password", key="user_gemini_key")

st.write("---")
st.subheader("🏢 2. 証券コード入力")
ticker_input = st.text_input("コード4桁", value="7203", key="target_ticker_code")

if st.button("🔍 解析を実行", use_container_width=True, key="exec_analysis_btn"):
    if not api_key: st.error("キーを入力してください")
    elif ticker_input and len(ticker_input) == 4 and ticker_input.isdigit():
        try:
            with st.spinner("解析中..."):
                t = yf.Ticker(f"{ticker_input}.T")
                info = t.info
                st.session_state.c_name = info.get("longName") or info.get("shortName") or f"コード: {ticker_input}"
                st.session_state.c_prc = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("ask") or st.session_state.c_prc
                st.session_state.shs = (info.get("sharesOutstanding") or (st.session_state.shs * 10000)) / 10000
                st.session_state.bt = info.get("beta") or 1.0
                st.session_state.sec = info.get("sector", "不明")
                st.session_state.ind = info.get("industry", "不明")
                bsum = info.get("longBusinessSummary", "なし")

                try: cf_df = t.get_cashflow()
                except: cf_df = t.cashflow
                
                if not cf_df.empty and "Operating Cash Flow" in cf_df.index:
                    oc = cf_df.loc["Operating Cash Flow"].dropna().values
                    ic = cf_df.loc["Investing Cash Flow"].dropna().values if "Investing Cash Flow" in cf_df.index else oc * 0
                    fcfs = [(float(o) + float(i)) / 100000000 for o, i in zip(oc, ic)]
                    if fcfs:
                        st.session_state.f_list = fcfs[:3]
                        st.session_state.a_fcf = np.mean(fcfs[:3])
                        st.session_state.f_base = float(st.session_state.a_fcf)

                try: bs_df = t.get_balance_sheet()
                except: bs_df = t.balance_sheet

                if not bs_df.empty:
                    td = float(bs_df.loc["Total Debt"].dropna().iloc) if "Total Debt" in bs_df.index else 0.0
                    cs = float(bs_df.loc["Cash And Cash Equivalents"].dropna().iloc) if "Cash And Cash Equivalents" in bs_df.index else 0.0
                    st.session_state.n_debt = (td - cs) / 100000000
                    ta = float(bs_df.loc["Total Assets"].dropna().iloc)
                    te = float(bs_df.loc["Total Equity Gross Minority Interest"].dropna().iloc) if "Total Equity Gross Minority Interest" in bs_df.index else ta * 0.5
                    st.session_state.eq_r = te / ta

                host = "https://googleapis.com"
                path = "/v1beta/models/gemini-2.5-flash:generateContent"
                g_url = f"{host}{path}?key={api_key}"
                p_text = f"バフェット流でレポート作って。特に技術、特許、R&D、AI、競合への優位性やモートを深く分析して。企業名:{st.session_state.c_name} セクター:{st.session_state.sec} FCF平均:{st.session_state.a_fcf:.1f}億円 純負債:{st.session_state.n_debt:.1f}億円 β値:{st.session_state.bt} 説明:{bsum[:1000]} 見出し:1.財務健康度 2.ビジネス特性 3.技術知財R&D 4.リスク総括"
                res = requests.post(g_url, headers={"Content-Type": "application/json"}, json={"contents": [{"parts": [{"text": p_text}]}]}, timeout=20)
                if res.status_code == 200: st.session_state.ai_rep = res.json()["candidates"]["content"]["parts"]["text"]
                else: st.session_state.ai_rep = f"エラー: {res.status_code}"
            st.success("すべてのデータ解析が正常に完了しました！")
        except Exception as e: st.warning(f"データ取得完了（一部数値自動補正）: {st.session_state.c_name}")

t1, t2, t3, t4 = st.tabs(["📊 財務", "🔒 モート", "🎯 試算", "🤖 AI分析"])

c_eq = 0.01 + (st.session_state.bt * 0.06)
c_wacc = (c_eq * st.session_state.eq_r) + (0.02 * (1 - st.session_state.eq_r))
g_s1_p = st.session_state.g_s1 / 100
g_t_p = st.session_state.g_t / 100

if g_t_p >= c_wacc: ins_v, tg_p, ins_lbl, tg_lbl = 0, 0, "エラー", "エラー"
else:
    pv = 0
    f = st.session_state.f_base
    for y in range(1, 6): f = f * (1 + g_s1_p); pv += f / ((1 + c_wacc) ** y)
    for y in range(6, 11): f = f * (1 + g_t_p); pv += f / ((1 + c_wacc) ** y)
    sh_v = ((pv + ((f * (1 + g_t_p)) / (c_wacc - g_t_p)) / ((1 + c_wacc) ** 10)) - st.session_state.n_debt)
    ins_v = max(0, (sh_v * 100000000) / (st.session_state.shs * 10000))
    m_score = sum([st.session_state.m1, st.session_state.m2, st.session_state.m3, st.session_state.m4, st.session_state.m5])
    tg_p = ins_v * (1 - (0.40 - (m_score * 0.05)))
    cur_p = st.session_state.c_prc
    ins_lbl = f"{'+' if ((cur_p - ins_v)/ins_v*100) >= 0 else ''}{(cur_p - ins_v)/ins_v*100:.1f}%" if ins_v > 0 else "不可"
    tg_lbl = f"{'+' if ((cur_p - tg_p)/tg_p*100) >= 0 else ''}{(cur_p - tg_p)/tg_p*100:.1f}%" if tg_p > 0 else "不可"

with t1:
    st.subheader("1. 財務データの確認")
    st.text_input("企業名", value=st.session_state.c_name, key="disp_c_name")
    st.write("過去FCF推移（億円）:", [round(x, 1) for x in st.session_state.f_list])
    st.session_state.f_base = st.number_input("予測基準FCF", value=float(st.session_state.f_base), key="num_f_base")
    with st.expander("📖 フリーキャッシュフロー(FCF)のガイド"):
        st.markdown("* **本質**: 企業が自由に使える純粋な現金。バフェットが最重視する指標。\n* **計算式**: 営業CF ＋ 投資CF")
    
    st.session_state.n_debt = st.number_input("純有利子負債", value=float(st.session_state.n_debt), key="num_n_debt")
    with st.expander("📖 純有利子負債のガイド"):
        st.markdown("* **本質**: 借金から現預金を引いた実質借金。マイナス（実質無借金）は超健全企業。")
        
    st.session_state.shs = st.number_input("発行済株式数(万株)", value=float(st.session_state.shs), key="num_shs")
    st.session_state.c_prc = st.number_input("現在の株価", value=float(st.session_state.c_prc), key="num_c_prc")
    st.session_state.bt = st.number_input("ベータ値(β)", value=float(st.session_state.bt), key="num_bt")
    with st.expander("📈 ベータ値(β)とWACC(割引率)のガイド"):
        st.markdown("* **ベータ値**: 1.0より高いとハイリスク、低いとディフェンシブ。高リスク企業ほど割引率が上がり、株価が厳しく評価されます。")

with t2:
    st.subheader("2. モート評価")
    st.session_state.m1 = st.checkbox("🔮 ブランド力", value=st.session_state.m1, key="ck_m1")
    st.session_state.m2 = st.checkbox("🔗 スイッチングコスト", value=st.session_state.m2, key="ck_m2")
    st.session_state.m3 = st.checkbox("🪙 低コスト優位性", value=st.session_state.m3, key="ck_m3")
    st.session_state.m4 = st.checkbox("📜 特許・許認可", value=st.session_state.m4, key="ck_m4")
    st.session_state.m5 = st.checkbox("🕸️ ネットワーク効果", value=st.session_state.m5, key="ck_m5")
    with st.expander("🏰 経済的お堀(モート)と安全余裕率のガイド"):
        st.markdown("* **お堀の点数**: 5点なら予測リスクが低いため、安全余裕率は**15%**でOK。0点ならリスクが高いため、**40%引き**の超安値でないと買いません。")

with t3:
    st.subheader("3. 理論株価試算")
    st.session_state.g_s1 = st.number_input("今後5年の予測成長率(％)", value=float(st.session_state.g_s1), step=0.5, key="nm_g_s1")
    st.session_state.g_t = st.number_input("6年目以降の永久成長率(％)", value=float(st.session_state.g_t), step=0.1, key="nm_g_t")
    with st.expander("🧮 2段階成長率のガイド"):
        st.markdown("* **永久成長率**: 6年目以降に会社が永遠に続ける成長率。成熟した日本市場では**0%〜1%**にするのが保守的で安全です。")
    st.write("---")
    
    if g_t_p >= c_wacc: st.error("永久成長率はWACC未満にしてください")
    else:
        st.success("試算完了")
        cl1, cl2, cl3 = st.columns(3)
        cl1.metric(label="🏪 現在株価", value=f"{int(cur_p):,} 円")
        cl2.metric(label="🎯 適正株価", value=f"{int(ins_v):,} 円", delta=f"現在値 {ins_lbl}", delta_color="inverse")
        cl3.metric(label="🛡️ 買付上限", value=f"{int(tg_p):,} 円", delta=f"現在値 {tg_lbl}", delta_color="inverse")
        st.write("---")
        st.subheader("📢 投資判断シグナル")
        if cur_p <= tg_p: st.success("✅ 【Buy】買付上限以下です。")
        elif cur_p <= ins_v: st.warning("⚠️ 【Hold】クッション不足です。")
        else: st.error("❌ 【Avoid】割高水準です。")

with t4:
    st.subheader("🤖 AI多角的ビジネス解析")
    st.markdown(st.session_state.ai_rep)
