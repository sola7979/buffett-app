# buffett-app
import streamlit as st
import yfinance as yf
import numpy as np

# 画面設定（スマートフォン最適化）
st.set_page_config(page_title="Professional Buffett AI Analyzer", layout="centered")

st.title("🏰 本格派 DCF ＆ AI企業総合分析ツール")
st.caption("財務データ、競争優位性、そしてAIによる定性・定量・先端技術分析を1つに統合")

# すべてのデータをセッション（記憶保持）で一元管理
if "company_name" not in st.session_state: st.session_state.company_name = "未取得"
if "fcf_list" not in st.session_state: st.session_state.fcf_list = [10.0, 10.0, 10.0]
if "avg_fcf" not in st.session_state: st.session_state.avg_fcf = 10.0
if "net_debt" not in st.session_state: st.session_state.net_debt = 215.0
if "shares" not in st.session_state: st.session_state.shares = 5002.0
if "current_price" not in st.session_state: st.session_state.current_price = 1263.0
if "beta" not in st.session_state: st.session_state.beta = 1.0
if "equity_ratio" not in st.session_state: st.session_state.equity_ratio = 0.50

# AI分析用テキストデータの保持
if "ai_summary" not in st.session_state: st.session_state.ai_summary = "データが読み込まれていません。上のボタンを押してください。"
if "business_summary" not in st.session_state: st.session_state.business_summary = ""

# ユーザー入力値の保持
if "fcf_base" not in st.session_state: st.session_state.fcf_base = 10.0
if "g_stage1" not in st.session_state: st.session_state.g_stage1 = 8.0
if "g_terminal" not in st.session_state: st.session_state.g_terminal = 0.5

# 各モートのチェック状態
if "m1" not in st.session_state: st.session_state.m1 = False
if "m2" not in st.session_state: st.session_state.m2 = False
if "m3" not in st.session_state: st.session_state.m3 = False
if "m4" not in st.session_state: st.session_state.m4 = False
if "m5" not in st.session_state: st.session_state.m5 = False

st.subheader("🏢 1. 証券コードから財務・市場データを取得")
ticker_input = st.text_input("証券コード4桁（例: 7203）", value="7203")

if st.button("🔍 精密データ ＆ AI分析基盤を読み込む", use_container_width=True):
    if ticker_input and len(ticker_input) == 4 and ticker_input.isdigit():
        try:
            with st.spinner("財務・市場ニュース・知財技術資産をAI解析中..."):
                ticker = yf.Ticker(f"{ticker_input}.T")
                info = ticker.info
                
                st.session_state.company_name = info.get("longName") or info.get("shortName") or f"コード: {ticker_input}"
                st.session_state.current_price = info.get("currentPrice") or info.get("regularMarketPrice") or st.session_state.current_price
                st.session_state.shares = (info.get("sharesOutstanding") or (st.session_state.shares * 10000)) / 10000
                st.session_state.beta = info.get("beta") or 1.0
                st.session_state.business_summary = info.get("longBusinessSummary") or "記載なし"
                
                cf = ticker.cashflow
                bs = ticker.balance_sheet
                
                if not cf.empty and "Operating Cash Flow" in cf.index and "Investing Cash Flow" in cf.index:
                    ocfs = cf.loc["Operating Cash Flow"].values
                    icfs = cf.loc["Investing Cash Flow"].values
                    fcfs = [(o + i) / 100000000 for o, i in zip(ocfs, icfs)]
                    st.session_state.fcf_list = fcfs[:3]
                    st.session_state.avg_fcf = np.mean(fcfs[:3])
                    st.session_state.fcf_base = float(st.session_state.avg_fcf)
                
                if not bs.empty:
                    total_debt = bs.loc["Total Debt"].iloc if "Total Debt" in bs.index else 0
                    cash = bs.loc["Cash And Cash Equivalents"].iloc if "Cash And Cash Equivalents" in bs.index else 0
                    st.session_state.net_debt = (total_debt - cash) / 100000000
                    
                    total_assets = bs.loc["Total Assets"].iloc if "Total Assets" in bs.index else 1
                    total_equity = bs.loc["Total Equity Gross Minority Interest"].iloc if "Total Equity Gross Minority Interest" in bs.index else (total_assets * 0.5)
                    st.session_state.equity_ratio = total_equity / total_assets

                # 技術・知財、ニュースの抽出
                sector = info.get("sector", "不明")
                industry = info.get("industry", "不明")
                news_list = ticker.news[:3]
                news_titles = [n.get("title", "") for n in news_list] if news_list else ["直近の重大ニュースなし"]
                
                # 技術に関するキーワード抽出
                tech_keywords = ["technology", "patent", "R&D", "software", "AI", "intellectual property", "開発", "特許", "技術"]
                has_tech_focus = any(kw in st.session_state.business_summary.lower() for kw in tech_keywords)

                # 🤖 AIレポートの自動生成（これが4つ目のタブに表示されます）
                st.session_state.ai_summary = f"""
                **分析対象:** {st.session_state.company_name} ({ticker_input}.T)  
                **業界分類:** {sector} / {industry}  

                #### 1️⃣ 財務数値（定量面）の健康度チェック
                * **現金の創出力:** 過去3年間のフリーキャッシュフロー(FCF)平均は **{st.session_state.avg_fcf:.1f}億円**。突発的なノイズを排除したこの実質キャッシュが、企業の純粋な体力です。
                * **実質的な債務リスク:** 純有利子負債は **{st.session_state.net_debt:.1f}億円**。{'プラスのため、将来のキャッシュから負債を差し引く重みが発生します。' if st.session_state.net_debt > 0 else 'マイナス（実質無借金金利耐性株）のため、金利上昇局面でも現金の守りが極めて固いバフェット好みの財務構造です。'}

                #### 2️⃣ 事業構造と非数値（定性面）の競争力
                * **市場ポジション:** 株価連動リスク(β値)は「{st.session_state.beta}」です。市場平均（1.0）より{'ボラティリティが高いためマクロ経済の波を強く受けやすいハイリスク・ハイリターン型' if st.session_state.beta > 1.0 else '値動きがマイルドであり、景気後退期にも強いディフェンシブ型'}の収益基盤と推測されます。
                * **最新の市場の関心:** 直近のニュース・市場イベントでは以下が注目されています。
                  - *「{news_titles[0]}」*

                #### 3️⃣ アプリ試算（DCF・モート）との連動分析
                * **割引率の妥当性:** 本アプリがCAPM（資本資産価格モデル）を用いて動的に弾き出した割引率（WACC）は、企業の負債・自己資本比率とボラティリティを反映した「客観的なハードルレート」として機能しています。
                * **安全余裕の思想:** 定性お堀（モートスコア）が高ければ高いほど、将来予測のブレが小さくなるため、AIとしても買付上限の基準を理論株価に近づける判断を強く支持します。

                #### 4️⃣ 💡 技術・知財・イノベーションの優位性分析
                * **開示文書の技術判定:** {f'事業概要に特許、R&D、テクノロジーに関する強い言及が見られます。独自の知財保護や技術的な参入障壁（モートの項目④）を構築できている可能性が高いです。' if has_tech_focus else '伝統的・インフラ的なビジネスモデルであり、最新技術による急成長よりは、既存インフラや顧客基盤による安定性が強みとなります。'}
                * **技術リスク/機会:** テクノロジーのライフサイクルが早い現代において、当セクター（{sector}）は継続的なR&D投資やシステム内製化が、長期的なフリーキャッシュフローを維持するための生命線となります。
                """
            st.success(f"データおよび多角的AI分析基盤の取得完了: {st.session_state.company_name}")
        except Exception as e:
            st.warning(f"一部データの自動取得に失敗しました。数値を手動入力してください。")

# タブの作成（財務、お堀、試算、AIレポートの4大要素）
tab1, tab2, tab3, tab4 = st.tabs(["📊 財務パラメータ", "🔒 競争優位性(モート)", "🎯 精密バリュエーション", "🤖 AI総合分析レポート"])

with tab1:
    st.subheader("1. 財務基礎データおよび市場変数の確認")
    c_name = st.text_input("企業名", value=st.session_state.company_name)
    st.write(f"直近の過去FCF推移（億円）: {[round(x,1) for x in st.session_state.fcf_list]}")
    st.session_state.fcf_base = st.number_input("予測基準とするFCF（億円／過去平均を推奨）", value=float(st.session_state.fcf_base))
    with st.expander("📖 フリーキャッシュフロー（FCF）の考え方と調べ方", expanded=False):
        st.markdown("* **本質**: 企業が自由に使える純粋な現金。バフェット流投資で最も重視する指標です。")
    st.session_state.net_debt = st.number_input("純有利子負債（億円）", value=float(st.session_state.net_debt))
    st.session_state.shares = st.number_input("発行済株式数（万株）", value=float(st.session_state.shares))
    st.session_state.current_price = st.number_input("現在の市場株価（円）", value=float(st.session_state.current_price))
    st.write("---")
    st.subheader("📈 WACC（割引率）の自動推定変数")
    rf_rate = st.number_input("リスクフリーレート（日本国債10年利回り相当 ％）", value=1.0) / 100
    market_premium = st.number_input("市場全体の期待リターン（％）", value=6.0) / 100
    st.session_state.beta = st.number_input("この企業のベータ値（リスク指標 β）", value=float(st.session_state.beta))
    
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
    st.info(f"モートスコア: {moat_score}点 ➡️ 要求する安全余裕率: **{int(mos_rate*100)}%**")

with tab3:
    st.subheader("3. 2段階DCFモデルによる理論株価試算")
    st.markdown("**📊 将来予測パラメータ**")
    st.session_state.g_stage1 = st.number_input("① 今後5年間の予測成長率（％）", value=float(st.session_state.g_stage1), step=0.5)
    st.session_state.g_terminal = st.number_input("② 6年目以降の永久成長率（％）", value=float(st.session_state.g_terminal), step=0.1)
    st.write("---")
    
    g_s1_parsed = st.session_state.g_stage1 / 100
    g_t_parsed = st.session_state.g_terminal / 100
    
    if g_t_parsed >= calculated_wacc:
        st.error("エラー: 永久成長率はWACC（割引率）未満に設定してください。")
    else:
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
