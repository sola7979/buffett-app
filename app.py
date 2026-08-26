# buffett-app
import streamlit as st
import yfinance as yf
import numpy as np

st.set_page_config(page_title="Professional DCF Analyzer", layout="centered")

st.title("🏰 本格派 DCF・バフェット流分析ツール")
st.caption("財務データと『見えない強み（モート）』を融合した精密バリュエーション")

# セッション状態の初期化
if "data" not in st.session_state:
    st.session_state.data = {
        "company_name": "未取得", "fcf_list": [10.0, 10.0, 10.0], "avg_fcf": 10.0,
        "net_debt": 215.0, "shares": 5002.0, "current_price": 1263.0,
        "beta": 1.0, "equity_ratio": 0.50
    }
# 計算結果を保持するセッション
if "calc_results" not in st.session_state:
    st.session_state.calc_results = None

st.subheader("🏢 1. 証券コードから財務・市場データを取得")
ticker_input = st.text_input("証券コード4桁（例: 7203）", value="7203")

if st.button("🔍 精密データを読み込む", use_container_width=True):
    if ticker_input and len(ticker_input) == 4 and ticker_input.isdigit():
        try:
            with st.spinner("過去数年分の財務諸表および市場データを解析中..."):
                ticker = yf.Ticker(f"{ticker_input}.T")
                info = ticker.info
                
                # 基本情報の取得
                st.session_state.data["company_name"] = info.get("longName") or info.get("shortName") or f"コード: {ticker_input}"
                st.session_state.data["current_price"] = info.get("currentPrice") or info.get("regularMarketPrice") or st.session_state.data["current_price"]
                st.session_state.data["shares"] = (info.get("sharesOutstanding") or (st.session_state.data["shares"] * 10000)) / 10000
                st.session_state.data["beta"] = info.get("beta") or 1.0
                
                # 財務データの取得
                cf = ticker.cashflow
                bs = ticker.balance_sheet
                
                if not cf.empty and "Operating Cash Flow" in cf.index and "Investing Cash Flow" in cf.index:
                    ocfs = cf.loc["Operating Cash Flow"].values
                    icfs = cf.loc["Investing Cash Flow"].values
                    fcfs = [(o + i) / 100000000 for o, i in zip(ocfs, icfs)]
                    st.session_state.data["fcf_list"] = fcfs[:3]
                    st.session_state.data["avg_fcf"] = np.mean(fcfs[:3])
                
                if not bs.empty:
                    total_debt = bs.loc["Total Debt"].iloc if "Total Debt" in bs.index else 0
                    cash = bs.loc["Cash And Cash Equivalents"].iloc if "Cash And Cash Equivalents" in bs.index else 0
                    st.session_state.data["net_debt"] = (total_debt - cash) / 100000000
                    
                    total_assets = bs.loc["Total Assets"].iloc if "Total Assets" in bs.index else 1
                    total_equity = bs.loc["Total Equity Gross Minority Interest"].iloc if "Total Equity Gross Minority Interest" in bs.index else (total_assets * 0.5)
                    st.session_state.data["equity_ratio"] = total_equity / total_assets

            st.success(f"データ取得完了: {st.session_state.data['company_name']}")
        except Exception as e:
            st.warning(f"一部データの自動取得に失敗しました。手動で数値を調整してください。")

# タブの作成
tab1, tab2, tab3 = st.tabs(["📊 財務・市場パラメータ", "🔒 競争優位性(モート)", "🎯 精密バリュエーション"])

with tab1:
    st.subheader("1. 財務基礎データおよび市場変数の確認")
    c_name = st.text_input("企業名", value=st.session_state.data["company_name"])
    
    st.write(f"直近の過去FCF推移（億円）: {[round(x,1) for x in st.session_state.data['fcf_list']]}")
    fcf_base = st.number_input("予測基準とするFCF（億円／過去平均を推奨）", value=float(st.session_state.data["avg_fcf"]))
    
    with st.expander("📖 フリーキャッシュフロー（FCF）の考え方と調べ方"):
        st.markdown("""
        * **本質**: 企業が自由に使える純粋な現金。バフェット流投資で最も重視する指標です。
        * **式**: `営業CF` ＋ `投資CF`
        """)
        
    net_debt = st.number_input("純有利子負債（億円）", value=float(st.session_state.data["net_debt"]))
    shares = st.number_input("発行済株式数（万株）", value=float(st.session_state.data["shares"]))
    current_price = st.number_input("現在の市場株価（円）", value=float(st.session_state.data["current_price"]))
    
    st.write("---")
    st.subheader("📈 WACC（割引率）の自動推定変数")
    
    rf_rate = st.number_input("リスクフリーレート（日本国債10年利回り相当 ％）", value=1.0) / 100
    market_premium = st.number_input("市場全体の期待リターン（％）", value=6.0) / 100
    beta = st.number_input("この企業のベータ値（リスク指標 β）", value=float(st.session_state.data["beta"]))
    
    # WACCの計算
    cost_of_equity = rf_rate + (beta * market_premium)
    eq_ratio = st.session_state.data["equity_ratio"]
    cost_of_debt = 0.02
    calculated_wacc = (cost_of_equity * eq_ratio) + (cost_of_debt * (1 - eq_ratio))
    
    st.info(f"💡 現在の推定WACC（割引率）: **{calculated_wacc*100:.2f}%**")

with tab2:
    st.subheader("2. 経済的お堀（モート）による安全余裕率の決定")
    m1 = st.checkbox("🔮 ブランド力（プレミアム価格での販売維持力）")
    m2 = st.checkbox("🔗 高いスイッチングコスト（顧客の離脱障壁）")
    m3 = st.checkbox("🪙 構造的な低コスト優位性")
    m4 = st.checkbox("📜 法的規制・特許・独占的許認可")
    m5 = st.checkbox("🕸️ 強固なネットワーク効果")
    
    moat_score = sum([m1, m2, m3, m4, m5])
    mos_rate = 0.40 - (moat_score * 0.05)
    st.info(f"モートスコア: {moat_score}点 ➡️ 要求する安全余裕率: **{int(mos_rate*100)}%**")

with tab3:
    st.subheader("3. 2段階DCFモデルによる理論株価試算")
    
    st.markdown("**📊 将来予測パラメータ（テンキー入力に変更）**")
    # ★スライダーを廃して、スマホで入力しやすいnumber_inputに変更
    g_stage1 = st.number_input("① 今後5年間の予測成長率（％）", value=8.0, step=0.5) / 100
    g_terminal = st.number_input("② 6年目以降の永久成長率（％）", value=0.5, step=0.1) / 100
    
    st.write("---")
    
    # ★「結果更新ボタン」の配置
    if st.button("🔄 試算結果を更新する", type="primary", use_container_width=True):
        if g_terminal >= calculated_wacc:
            st.error("エラー: 永久成長率はWACC（割引率）未満に設定してください。")
        else:
            # 1〜10年のキャッシュフロー予測と現在価値化
            pv_stage1 = 0
            fcf = fcf_base
            for year in range(1, 6):
                fcf = fcf * (1 + g_stage1)
                pv_stage1 += fcf / ((1 + calculated_wacc) ** year)
                
            pv_stage2 = 0
            for year in range(6, 11):
                fcf = fcf * (1 + g_terminal)
                pv_stage2 += fcf / ((1 + calculated_wacc) ** year)
                
            terminal_value = (fcf * (1 + g_terminal)) / (calculated_wacc - g_terminal)
            pv_terminal = terminal_value / ((1 + calculated_wacc) ** 10)
            
            enterprise_value = pv_stage1 + pv_stage2 + pv_terminal
            shareholder_value = enterprise_value - net_debt
            
            intrinsic_value = (shareholder_value * 100000000) / (shares * 10000)
            intrinsic_value = max(0, intrinsic_value)
            target_price = intrinsic_value * (1 - mos_rate)
            
            # 結果をセッションに格納
            st.session_state.calc_results = {
                "intrinsic": intrinsic_value,
                "target": target_price,
                "current": current_price
            }

    # 結果の表示
    if st.session_state.calc_results is not None:
        res = st.session_state.calc_results
        st.metric(label="🎯 1株あたりの理論価値（適正株価）", value=f"{int(res['intrinsic']):,} 円")
        st.metric(label="🛡️ モート連動型 買付上限価格", value=f"{int(res['target']):,} 円")
        
        st.write("---")
        st.subheader("📢 投資判断シグナル")
        if res['current'] <= res['target']:
            st.success(f"✅ 【お買い得 / Buy】現在の株価（{int(res['current'])}円）は、買付上限以下です。")
        elif res['current'] <= res['intrinsic']:
            st.warning(f"⚠️ 【適正価格 / Hold】理論価値の範囲内ですが、下値のクッションが不足しています。")
        else:
            st.error(f"❌ 【割高・見送り / Avoid】現在の株価は、理論上の本質的価値を超えています。")
    else:
        st.info("💡 上の「🔄 試算結果を更新する」ボタンを押すと、最新の入力に基づいたシグナルが表示されます。")
