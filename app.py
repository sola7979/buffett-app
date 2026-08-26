# buffett-app
import streamlit as st
import yfinance as yf
import numpy as np

st.set_page_config(page_title="Professional DCF Analyzer", layout="centered")

st.title("🏰 本格派 DCF・バフェット流分析ツール")
st.caption("財務データと『見えない強み（モート）』を融合した精密バリュエーション")

# すべてのデータをセッション（記憶保持）で一元管理
if "company_name" not in st.session_state: st.session_state.company_name = "未取得"
if "fcf_list" not in st.session_state: st.session_state.fcf_list = [10.0, 10.0, 10.0]
if "avg_fcf" not in st.session_state: st.session_state.avg_fcf = 10.0
if "net_debt" not in st.session_state: st.session_state.net_debt = 215.0
if "shares" not in st.session_state: st.session_state.shares = 5002.0
if "current_price" not in st.session_state: st.session_state.current_price = 1263.0
if "beta" not in st.session_state: st.session_state.beta = 1.0
if "equity_ratio" not in st.session_state: st.session_state.equity_ratio = 0.50

# ユーザーが画面上で入力した値を一時保存するセッション
if "fcf_base" not in st.session_state: st.session_state.fcf_base = 10.0
if "g_stage1" not in st.session_state: st.session_state.g_stage1 = 8.0
if "g_terminal" not in st.session_state: st.session_state.g_terminal = 0.5

# 各モートのチェック状態も保持
if "m1" not in st.session_state: st.session_state.m1 = False
if "m2" not in st.session_state: st.session_state.m2 = False
if "m3" not in st.session_state: st.session_state.m3 = False
if "m4" not in st.session_state: st.session_state.m4 = False
if "m5" not in st.session_state: st.session_state.m5 = False

st.subheader("🏢 1. 証券コードから財務・市場データを取得")
ticker_input = st.text_input("証券コード4桁（例: 7203）", value="7203")

if st.button("🔍 精密データを読み込む", use_container_width=True):
    if ticker_input and len(ticker_input) == 4 and ticker_input.isdigit():
        try:
            with st.spinner("過去数年分の財務諸表および市場データを解析中..."):
                ticker = yf.Ticker(f"{ticker_input}.T")
                info = ticker.info
                
                st.session_state.company_name = info.get("longName") or info.get("shortName") or f"コード: {ticker_input}"
                st.session_state.current_price = info.get("currentPrice") or info.get("regularMarketPrice") or st.session_state.current_price
                st.session_state.shares = (info.get("sharesOutstanding") or (st.session_state.shares * 10000)) / 10000
                st.session_state.beta = info.get("beta") or 1.0
                
                cf = ticker.cashflow
                bs = ticker.balance_sheet
                
                if not cf.empty and "Operating Cash Flow" in cf.index and "Investing Cash Flow" in cf.index:
                    ocfs = cf.loc["Operating Cash Flow"].values
                    icfs = cf.loc["Investing Cash Flow"].values
                    fcfs = [(o + i) / 100000000 for o, i in zip(ocfs, icfs)]
                    st.session_state.fcf_list = fcfs[:3]
                    st.session_state.avg_fcf = np.mean(fcfs[:3])
                    st.session_state.fcf_base = float(st.session_state.avg_fcf) # 初期予測値にセット
                
                if not bs.empty:
                    total_debt = bs.loc["Total Debt"].iloc if "Total Debt" in bs.index else 0
                    cash = bs.loc["Cash And Cash Equivalents"].iloc if "Cash And Cash Equivalents" in bs.index else 0
                    st.session_state.net_debt = (total_debt - cash) / 100000000
                    
                    total_assets = bs.loc["Total Assets"].iloc if "Total Assets" in bs.index else 1
                    total_equity = bs.loc["Total Equity Gross Minority Interest"].iloc if "Total Equity Gross Minority Interest" in bs.index else (total_assets * 0.5)
                    st.session_state.equity_ratio = total_equity / total_assets

            st.success(f"データ取得完了: {st.session_state.company_name}")
        except Exception as e:
            st.warning(f"一部データの自動取得に失敗しました。数値を手動入力してください。")

# タブの作成
tab1, tab2, tab3 = st.tabs(["📊 財務・市場パラメータ", "🔒 競争優位性(モート)", "🎯 精密バリュエーション"])

with tab1:
    st.subheader("1. 財務基礎データおよび市場変数の確認")
    c_name = st.text_input("企業名", value=st.session_state.company_name)
    
    st.write(f"直近の過去FCF推移（億円）: {[round(x,1) for x in st.session_state.fcf_list]}")
    st.session_state.fcf_base = st.number_input("予測基準とするFCF（億円／過去平均を推奨）", value=float(st.session_state.fcf_base))
    
    # ★考え方ガイド（記憶保持される仕組みの中に配置）
    with st.expander("📖 フリーキャッシュフロー（FCF）の考え方と調べ方", expanded=False):
        st.markdown("""
        * **本質**: 企業が自由に使える純粋な現金。バフェット流投資で最も重視する指標です。
        * **式**: `営業CF` ＋ `投資CF`
        """)
        
    st.session_state.net_debt = st.number_input("純有利子負債（億円）", value=float(st.session_state.net_debt))
    with st.expander("📖 純有利子負債（ネットデット）の考え方", expanded=False):
        st.markdown("* **本質**: `借金` から `現預金` を引いた実質的な借金。マイナスなら実質無借金で超健全です。")

    st.session_state.shares = st.number_input("発行済株式数（万株）", value=float(st.session_state.shares))
    st.session_state.current_price = st.number_input("現在の市場株価（円）", value=float(st.session_state.current_price))
    
    st.write("---")
    st.subheader("📈 WACC（割引率）の自動推定変数")
    
    rf_rate = st.number_input("リスクフリーレート（日本国債10年利回り相当 ％）", value=1.0) / 100
    market_premium = st.number_input("市場全体の期待リターン（％）", value=6.0) / 100
    st.session_state.beta = st.number_input("この企業のベータ値（リスク指標 β）", value=float(st.session_state.beta))
    
    with st.expander("📈 割引率（WACC）とベータ（β）の考え方", expanded=False):
        st.markdown("* **ベータ値**: 1.0より高いとハイリスク、低いとディフェンシブ。高い企業ほど割引率が上がり、株価が厳しく評価されます。")

    # WACCのリアルタイム計算
    cost_of_equity = rf_rate + (st.session_state.beta * market_premium)
    eq_ratio = st.session_state.equity_ratio
    cost_of_debt = 0.02
    calculated_wacc = (cost_of_equity * eq_ratio) + (cost_of_debt * (1 - eq_ratio))
    
    st.info(f"💡 現在の推定WACC（割引率）: **{calculated_wacc*100:.2f}%**")

with tab2:
    st.subheader("2. 経済的お堀（モート）による安全余裕率の決定")
    st.session_state.m1 = st.checkbox("🔮 ブランド力（プレミアム価格での販売維持力）", value=st.session_state.m1)
    st.session_state.m2 = st.checkbox("🔗 高いスイッチングコスト（顧客の離脱障壁）", value=st.session_state.m2)
    st.session_state.m3 = st.checkbox("🪙 構造的な低コスト優位性", value=st.session_state.m3)
    st.session_state.m4 = st.checkbox("📜 法的規制・特許・独占的許認可", value=st.session_state.m4)
    st.session_state.m5 = st.checkbox("🕸️ 強固なネットワーク効果", value=st.session_state.m5)
    
    moat_score = sum([st.session_state.m1, st.session_state.m2, st.session_state.m3, st.session_state.m4, st.session_state.m5])
    mos_rate = 0.40 - (moat_score * 0.05)
    
    with st.expander("🏰 経済的お堀（モート）と安全余裕率（MoS）の関係", expanded=False):
        st.markdown("* **本質**: ライバルに負けない障壁がある企業（5点）は予測リスクが低いため、安全余裕率は**15%**でOK。お堀がない企業（0点）は**40%引き**じゃないと買いません。")
        
    st.info(f"モートスコア: {moat_score}点 ➡️ 要求する安全余裕率: **{int(mos_rate*100)}%**")

with tab3:
    st.subheader("3. 2段階DCFモデルによる理論株価試算")
    
    st.markdown("**📊 将来予測パラメータ**")
    st.session_state.g_stage1 = st.number_input("① 今後5年間の予測成長率（％）", value=float(st.session_state.g_stage1), step=0.5)
    st.session_state.g_terminal = st.number_input("② 6年目以降の永久成長率（％）", value=float(st.session_state.g_terminal), step=0.1)
    
    with st.expander("🧮 2段階DCFモデルと永久成長率の考え方", expanded=False):
        st.markdown("* **永久成長率**: 6年目以降に会社が永久に続ける成長。成熟した日本市場では**0%〜1%**にするのが保守的で安全です。")
        
    st.write("---")
    
    # ★計算ロジック（ボタンを押さなくても動く、または押して確定する両対応に改善）
    g_s1_parsed = st.session_state.g_stage1 / 100
    g_t_parsed = st.session_state.g_terminal / 100
    
    if g_t_parsed >= calculated_wacc:
        st.error("エラー: 永久成長率はWACC（割引率）未満に設定してください。")
    else:
        # 計算を実行
        pv_stage1 = 0
        fcf = st.session_state.fcf_base
        for year in range(1, 6):
            fcf = fcf * (1 + g_s1_parsed)
            pv_stage1 += fcf / ((1 + calculated_wacc) ** year)
            
        pv_stage2 = 0
        for year in range(6, 11):
            fcf = fcf * (1 + g_t_parsed)
            pv_stage2 += fcf / ((1 + calculated_wacc) ** year)
            
        terminal_value = (fcf * (1 + g_t_parsed)) / (calculated_wacc - g_t_parsed)
        pv_terminal = terminal_value / ((1 + calculated_wacc) ** 10)
        
        enterprise_value = pv_stage1 + pv_stage2 + pv_terminal
        shareholder_value = enterprise_value - st.session_state.net_debt
        
        intrinsic_value = (shareholder_value * 100000000) / (st.session_state.shares * 10000)
        intrinsic_value = max(0, intrinsic_value)
        target_price = intrinsic_value * (1 - mos_rate)
        
        # 画面に結果を常時リアルタイム出力（ボタンを押す手間も無くしました！）
        st.success("✨ 試算完了（リアルタイム更新中）")
        st.metric(label="🎯 1株あたりの理論価値（適正株価）", value=f"{int(intrinsic_value):,} 円")
        st.metric(label="🛡️ モート連動型 買付上限価格", value=f"{int(target_price):,} 円")
        
        st.write("---")
        st.subheader("📢 投資判断シグナル")
        cur_p = st.session_state.current_price
        if cur_p <= target_price:
            st.success(f"✅ 【お買い得 / Buy】現在の株価（{int(cur_p)}円）は、買付上限以下です。")
        elif cur_p <= intrinsic_value:
            st.warning(f"⚠️ 【適正価格 / Hold】理論価値の範囲内ですが、下値のクッションが不足しています。")
        else:
            st.error(f"❌ 【割高・見送り / Avoid】現在の株価は、理論上の本質的価値を超えています。")
