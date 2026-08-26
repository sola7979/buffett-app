# buffett-app
import streamlit as st
import yfinance as yf

# 画面設定（スマートフォン最適化）
st.set_page_config(page_title="Corporate Value Analyzer", layout="centered")

st.title("📊 企業コード自動取得・価値評価ツール")
st.caption("4桁の証券コードを入力するだけで財務データを自動取得します")

# 1. 企業コードの入力
st.subheader("🏢 分析対象企業の指定")
ticker_input = st.text_input("証券コード4桁（例: 7203）", value="7203")

# 初期値のセット
init_company = "手動入力モード"
init_fcf = 10.0
init_debt = 215.0
init_shares = 5002.0
init_price = 1263.0

# yfinanceからデータ自動取得を試みる
if ticker_input and len(ticker_input) == 4 and ticker_input.isdigit():
    ticker_code = f"{ticker_input}.T" # 日本株用に「.T」を付与
    try:
        with st.spinner("データを自動取得中..."):
            ticker = yf.Ticker(ticker_code)
            info = ticker.info
            
            # 株価・発行済株式数の取得
            init_price = info.get("currentPrice") or info.get("regularMarketPrice") or init_price
            init_shares = (info.get("sharesOutstanding") or (init_shares * 10000)) / 10000 # 万株単位に変換
            init_company = info.get("longName") or info.get("shortName") or f"コード: {ticker_input}"
            
            # 財務諸表（キャッシュフロー・バランスシート）の取得
            cf = ticker.cashflow
            bs = ticker.balance_sheet
            
            # フリーキャッシュフローの計算（営業CF + 投資CF）
            if not cf.empty and "Operating Cash Flow" in cf.index and "Investing Cash Flow" in cf.index:
                # 最新（0番目）のデータを億円単位に変換
                latest_ocf = cf.loc["Operating Cash Flow"].iloc[0]
                latest_icf = cf.loc["Investing Cash Flow"].iloc[0]
                init_fcf = (latest_ocf + latest_icf) / 100000000
            
            # 純有利子負債の計算（有利子負債 - 現預金）
            if not bs.empty:
                total_debt = bs.loc["Total Debt"].iloc[0] if "Total Debt" in bs.index else 0
                cash = bs.loc["Cash And Cash Equivalents"].iloc[0] if "Cash And Cash Equivalents" in bs.index else 0
                init_debt = (total_debt - cash) / 100000000
                
        st.success(f"経理データの自動取得に成功しました: {init_company}")
    except Exception as e:
        st.warning("一部のデータが自動取得できませんでした。手動で数値を修正・入力してください。")

# タブ機能
tab1, tab2, tab3 = st.tabs(["💰 財務基盤の確認", "🛡️ 競合優位性の評価", "🎯 試算結果"])

with tab1:
    st.subheader("1. 基礎財務データ（自動入力・修正可能）")
    target_company = st.text_input("分析対象企業名", value=init_company)
    current_fcf = st.number_input("フリーキャッシュフロー (億円)", value=float(init_fcf), step=1.0)
    net_interest_bearing_debt = st.number_input("純有利子負債 (億円)", value=float(init_debt), step=1.0)
    total_shares = st.number_input("発行済株式総数 (万株)", value=float(init_shares), step=10.0)
    market_stock_price = st.number_input("現在の市場株価 (円)", value=float(init_price), step=1.0)

with tab2:
    st.subheader("2. 事業の持続性と競合優位性（5項目チェック）")
    st.write("企業のビジネスモデルの強みを確認します：")
    factor1 = st.checkbox("高い価格決定力（顧客が他社製品に切り替えにくい）")
    factor2 = st.checkbox("スイッチングコスト（顧客が他社へ移行する際の負担が大きい）")
    factor3 = st.checkbox("規模の経済やプロセス優位による低コスト構造")
    factor4 = st.checkbox("法的規制、特許、許認可による保護")
    factor5 = st.checkbox("強固なネットワーク外部性、または独自の流通網")
    
    total_score = sum([factor1, factor2, factor3, factor4, factor5])
    st.metric(label="総合優位性スコア", value=f"{total_score} / 5")

with tab3:
    st.subheader("3. 収益還元法（DCF法）による評価")
    projected_growth = st.slider("想定成長率（今後5年間）(％)", min_value=-10, max_value=30, value=12) / 100
    discount_rate = st.slider("資本コスト / 割引率 (％)", min_value=3.0, max_value=15.0, value=6.5, step=0.5) / 100
    
    # DCF法による計算
    aggregated_pv = 0
    estimated_fcf = current_fcf
    for year in range(1, 11):
        if year <= 5:
            estimated_fcf = estimated_fcf * (1 + projected_growth)
        else:
            estimated_fcf = estimated_fcf * 1.02
        aggregated_pv += estimated_fcf / ((1 + discount_rate) ** year)
    
    terminal_val = (estimated_fcf * 1.02) / (discount_rate - 0.02)
    pv_terminal_val = terminal_val / ((1 + discount_rate) ** 10)
    
    calculated_ev = aggregated_pv + pv_terminal_val
    estimated_equity_value = calculated_ev - net_interest_bearing_debt
    
    theoretical_value = (estimated_equity_value * 100000000) / (total_shares * 10000)
    if theoretical_value < 0: theoretical_value = 0
    conservative_limit = theoretical_value * 0.8
    
    # 結果の出力
    st.metric(label="🎯 1株あたりの理論価値（適正株価）", value=f"{int(theoretical_value):,} 円")
    st.metric(label="🛡️ 保守的購入上限価格 (割引率20%適用)", value=f"{int(conservative_limit):,} 円")
    
    st.write("---")
    st.subheader("📢 投資アプローチの判定")
    if market_stock_price <= conservative_limit:
        st.success(f"✅ 【割安圏】現在の株価は保守的上限以下です。(優位性: {total_score}点)")
    elif market_stock_price <= theoretical_value:
        st.warning(f"⚠️ 【適正水準】理論価値の範囲内ですが、安全余裕は少なめです。")
    else:
        st.error(f"❌ 【割高圏】現在の株価は客観的な理論価値を上回っています。")

