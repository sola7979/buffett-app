# buffett-app
import streamlit as st
import yfinance as yf
import numpy as np

st.set_page_config(page_title="Professional DCF & Help Guide", layout="centered")

st.title("🏰 本格派 DCF・バフェット流分析ツール")
st.caption("財務データと『見えない強み（モート）』を融合した精密バリュエーション")

# セッション状態の初期化
if "data" not in st.session_state:
    st.session_state.data = {
        "company_name": "未取得", "fcf_list": [10.0, 10.0, 10.0], "avg_fcf": 10.0,
        "net_debt": 215.0, "shares": 5002.0, "current_price": 1263.0,
        "beta": 1.0, "equity_ratio": 0.50
    }

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
    
    # 💡 フリーキャッシュフローの解説
    with st.expander("📖 フリーキャッシュフロー（FCF）の考え方と調べ方"):
        st.markdown("""
        * **考え方**: 企業が自由に使える「手元の現金」です。バフェット流投資では、表面上の利益（純利益）よりも、この実際に残ったキャッシュを最も重視します。
        * **計算式**: `営業キャッシュフロー（本業で稼いだお金）` ＋ `投資キャッシュフロー（設備投資などで使ったお金：マイナス値）`
        * **自動取得が失敗した場合の調べ方**: 企業の決算短信の「キャッシュ・フロー計算書」のページを開き、上記の2つの数字を足してください。
        """)
        
    net_debt = st.number_input("純有利子負債（億円）", value=float(st.session_state.data["net_debt"]))
    
    # 💡 純有利子負債の解説
    with st.expander("📖 純有利子負債（ネットデット）の考え方"):
        st.markdown("""
        * **考え方**: `借金（有利子負債）` から `会社の現預金` を差し引いた「実質的な借金」です。
        * 数値が**マイナス（実質無借金）**の企業は財務が非常に健全で、バフェットが好む「現金をため込んでいる優良企業」の確率が高くなります。
        """)
        
    shares = st.number_input("発行済株式数（万株）", value=float(st.session_state.data["shares"]))
    current_price = st.number_input("現在の市場株価（円）", value=float(st.session_state.data["current_price"]))
    
    st.write("---")
    st.subheader("📈 CAPMによるWACC（割引率）の動的推定")
    
    rf_rate = st.number_input("リスクフリーレート（日本国債10年物利回り相当 ％）", value=1.0) / 100
    market_premium = st.number_input("市場全体の期待リターン（マーケットプレミアム ％）", value=6.0) / 100
    beta = st.number_input("この企業のベータ値（市場連動性リスク β）", value=float(st.session_state.data["beta"]))
    
    # 💡 WACCとベータの解説
    with st.expander("📈 割引率（WACC）とベータ（β）の考え方"):
        st.markdown("""
        * **ベータ（β）とは**: 市場全体（TOPIXなど）が1%動いたときに、その株が何%動くかを示すリスク指標です。
            * `1.0より高い`: 値動きが激しいハイリスク株（AI関連、新興企業など）
            * `1.0より低い`: 値動きが穏やかなディフェンシブ株（インフラ、食品など）
        * **WACC（割引率）とは**: 将来もらえるお金の「不確実性」を考慮して、今の価値に割り引くための割合です。リスクが高い企業（高β）ほど割引率が高くなり、理論株価は厳しく算出されます。
        """)
        
    cost_of_equity = rf_rate + (beta * market_premium)
    eq_ratio = st.session_state.data["equity_ratio"]
    cost_of_debt = 0.02
    calculated_wacc = (cost_of_equity * eq_ratio) + (cost_of_debt * (1 - eq_ratio))
    
    st.info(f"💡 算出された株主資本コスト: {cost_of_equity*100:.2f}% / 調整後WACC（割引率）: **{calculated_wacc*100:.2f}%**")

with tab2:
    st.subheader("2. 経済的お堀（モート）による安全余裕率の決定")
    st.markdown("**【重要】バフェット流投資の本質です。企業のビジネスモデルを評価してください：**")
    
    m1 = st.checkbox("🔮 ブランド力（プレミアム価格での販売維持力）")
    m2 = st.checkbox("🔗 高いスイッチングコスト（顧客の離脱障壁）")
    m3 = st.checkbox("🪙 構造的な低コスト優位性")
    m4 = st.checkbox("📜 法的規制・特許・独占的許認可")
    m5 = st.checkbox("🕸️ 強固なネットワーク効果")
    
    moat_score = sum([m1, m2, m3, m4, m5])
    mos_rate = 0.40 - (moat_score * 0.05)
    
    # 💡 経済的お堀と安全余裕率の解説
    with st.expander("🏰 経済的お堀（モート）と安全余裕率（MoS）の関係"):
        st.markdown("""
        * **なぜお堀を評価するのか？**: どんなに今儲かっていても、ライバルに真似されたら将来のFCFは激減します。参入障壁が高い企業ほど、将来の予測が裏切られるリスクが低くなります。
        * **安全余裕率（Margin of Safety）との連動**:
            * **お堀が強い（5点）**: 将来の予測がズレるリスクが低いため、安全余裕率は**15%**（理論株価にかなり近い価格）でもGOサインを出します。
            * **お堀が無い（0点）**: 将来ライバルに潰されるリスクが高いため、理論株価から**40%引き**された超バーゲンセール価格でないと買いません。
        """)
    st.info(f"モートスコア: {moat_score}点 ➡️ 要求する安全余裕率: **{int(mos_rate*100)}%**")

with tab3:
    st.subheader("3. 2段階DCFモデルによる理論株価試算")
    
    g_stage1 = st.slider("第1ステージ（今後5年間）の予測成長率（％）", min_value=-10, max_value=30, value=8) / 100
    g_terminal = st.slider("第2ステージ（6年目以降）の永久成長率（％）", min_value=-2.0, max_value=2.0, value=0.5, step=0.1) / 100
    
    # 💡 2段階成長率の解説
    with st.expander("🧮 2段階DCFモデルと永久成長率の考え方"):
        st.markdown("""
        * **第1ステージ（今後5年）**: 新製品のヒットや市場の拡大など、企業が中期的に達成できそうな現実的な成長率を設定します。
        * **第2ステージ（永久成長率）**: 6年目以降、会社が存続する限り「永遠に続く成長率」です。日本のような成熟国では、どんな大企業でも**0%〜1%程度**にするのが現実的（保守的）な投資判断になります。
        """)
        
    if g_terminal >= calculated_wacc:
        st.error("エラー: 永久成長率はWACC（割引率）未満に設定してください。計算が無限大に発散します。")
    else:
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
        
        st.metric(label="🎯 1株あたりの理論価値（適正株価）", value=f"{int(intrinsic_value):,} 円")
        st.metric(label="🛡️ モート連動型 買付上限価格", value=f"{int(target_price):,} 円")
        
        st.write("---")
        st.subheader("📢 投資判断シグナル")
        if current_price <= target_price:
            st.success(f"✅ 【お買い得 / Buy】現在の株価（{int(current_price)}円）は、安全余裕を持たせた買付上限以下です。")
        elif current_price <= intrinsic_value:
            st.warning(f"⚠️ 【適正価格 / Hold】理論価値の範囲内ですが、安全余裕（下値のクッション）が不足しています。")
        else:
            st.error(f"❌ 【割高・見送り / Avoid】現在の株価は、理論上の本質的価値を超えています。")
