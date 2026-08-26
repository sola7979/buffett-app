# buffett-app
import streamlit as st

# ページ設定（スマホの画面幅に自動で合わせる）
st.set_page_config(page_title="バフェット流・企業分析", layout="centered")

st.title("📈 バフェット流・企業分析ツール")
st.caption("スマホで完結！企業の真の価値を計算します")

# 画面をすっきりさせるためのタブ
tab1, tab2, tab3 = st.tabs(["① データ入力", "② モート(堀)", "③ 判定結果"])

with tab1:
    st.subheader("📊 企業の財務データを入力")
    company_name = st.text_input("企業名", value="オカムラ食品工業")
    base_fcf = st.number_input("現在のフリーキャッシュフロー（億円）", value=10.0, step=1.0)
    net_debt = st.number_input("ネット有利子負債（億円）", value=215.0, step=1.0)
    shares = st.number_input("発行済株式数（万株）", value=5002.0, step=10.0)
    current_price = st.number_input("現在の株価（円）", value=1263.0, step=1.0)

with tab2:
    st.subheader("🏰 経済的なお堀（モート）")
    st.write("バフェットの5つの視点。当てはまるものにチェック：")
    m1 = st.checkbox("強力なブランド力がある（他より高くても買われる）")
    m2 = st.checkbox("他社への乗り換えコストが高い（やめにくい）")
    m3 = st.checkbox("圧倒的な低コストで製造・提供できる")
    m4 = st.checkbox("特許や政府の許認可・規制に守られている")
    m5 = st.checkbox("独自の大規模なネットワークや技術がある")
    
    moat_score = sum([m1, m2, m3, m4, m5])
    st.metric(label="モートスコア（5点満点）", value=f"{moat_score} 点")

with tab3:
    st.subheader("🧮 価値判定シミュレーション")
    growth_rate = st.slider("今後5年の成長率（％）", min_value=-10, max_value=30, value=12) / 100
    wacc = st.slider("割引率 / WACC（％）", min_value=3.0, max_value=15.0, value=6.5, step=0.5) / 100
    
    # 簡易DCF計算（10年分のキャッシュフローを予測して現在価値に直す）
    pv_sum = 0
    fcf = base_fcf
    for year in range(1, 11):
        if year <= 5:
            fcf = fcf * (1 + growth_rate)
        else:
            fcf = fcf * 1.02 # 6年目以降は安定成長2%
        pv_sum += fcf / ((1 + wacc) ** year)
    
    # 永続価値（11年目以降）の追加
    terminal_value = (fcf * 1.02) / (wacc - 0.02)
    pv_terminal = terminal_value / ((1 + wacc) ** 10)
    
    # 企業価値と株主価値
    enterprise_value = pv_sum + pv_terminal
    shareholder_value = enterprise_value - net_debt
    
    # 1株あたりの本質的価値
    intrinsic_value = (shareholder_value * 100000000) / (shares * 10000)
    if intrinsic_value < 0: intrinsic_value = 0
    
    # 安全余裕率（MoS）20%を考慮した買付上限
    target_price = intrinsic_value * 0.8
    
    # 結果表示
    st.metric(label="🎯 1株あたりの本質的価値", value=f"{int(intrinsic_value):,} 円")
    st.metric(label="🛡️ 買付上限価格 (安全余裕率20%)", value=f"{int(target_price):,} 円")
    
    st.write("---")
    st.subheader("📢 投資判断")
    if current_price <= target_price:
        st.success(f"✅ 【お買い得】現在の株価は買付上限以下です！(モート: {moat_score}点)")
    elif current_price <= intrinsic_value:
        st.warning(f"⚠️ 【適正価格〜やや割高】安全余裕はありませんが、本質的価値の範囲内です。")
    else:
        st.error(f"❌ 【見送り / 割高】現在の株価は本質的価値を超えています。")
