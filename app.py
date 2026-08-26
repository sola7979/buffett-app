# buffett-app
import streamlit as st

# 画面設定（スマートフォン最適化）
st.set_page_config(page_title="Corporate Value & Moat Analyzer", layout="centered")

st.title("📊 企業価値・競争優位性評価ツール")
st.caption("財務データと事業の持続性から適正株価を試算します")

# 構成をシャッフルし、一般的な用語に言い換え
tab1, tab2, tab3 = st.tabs(["💰 財務基盤の入力", "🛡️ 競合優位性の評価", "🎯 試算結果"])

with tab1:
    st.subheader("1. 基礎財務データの入力")
    target_company = st.text_input("分析対象（企業名など）", value="対象企業A")
    current_fcf = st.number_input("フリーキャッシュフロー (億円)", value=10.0, step=1.0)
    net_interest_bearing_debt = st.number_input("純有利子負債 (億円)", value=215.0, step=1.0)
    total_shares = st.number_input("発行済株式総数 (万株)", value=5002.0, step=10.0)
    market_stock_price = st.number_input("現在の市場株価 (円)", value=1263.0, step=1.0)

with tab2:
    st.subheader("2. 事業の持続性と競合優位性（5項目チェック）")
    st.write("企業のビジネスモデルの強みを確認します。該当する項目を選択してください：")
    
    # 表現をビジネス用語に完全に言い換え
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
    
    # 将来キャッシュフローの現在価値算定
    aggregated_pv = 0
    estimated_fcf = current_fcf
    for year in range(1, 11):
        if year <= 5:
            estimated_fcf = estimated_fcf * (1 + projected_growth)
        else:
            estimated_fcf = estimated_fcf * 1.02 # 6年目以降の継続成長率を2%と仮定
        aggregated_pv += estimated_fcf / ((1 + discount_rate) ** year)
    
    # ターミナルバリュー（残存価値）の算出
    terminal_val = (estimated_fcf * 1.02) / (discount_rate - 0.02)
    pv_terminal_val = terminal_val / ((1 + discount_rate) ** 10)
    
    # 企業価値および株主価値の計算
    calculated_ev = aggregated_pv + pv_terminal_val
    estimated_equity_value = calculated_ev - net_interest_bearing_debt
    
    # 1株あたり理論株価の算出
    theoretical_value = (estimated_equity_value * 100000000) / (total_shares * 10000)
    if theoretical_value < 0: theoretical_value = 0
    
    # 保守的スタンス（安全余裕率20%）を反映した購入上限目安
    conservative_limit = theoretical_value * 0.8
    
    # 評価結果の出力
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
