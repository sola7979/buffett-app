import numpy as np
import requests
import streamlit as st

st.set_page_config(page_title="Buffett AI", layout="centered")
st.title("🏰 投資分析シミュレーター")
st.caption("初期値ゼロ設計：手動数値試算 ＆ 企業名AI自動リサーチ")

# 状態初期化（すべて白紙・ゼロに設定）
keys = [
    "c_name", "f_base", "n_debt", "shs", "c_prc", 
    "bt", "eq_r", "g_s1", "g_t", "ai_rep",
    "m1", "m2", "m3", "m4", "m5"
]
vals = [
    "", 0.0, 0.0, 0.0, 0.0, 
    1.0, 0.5, 0.0, 0.0, "「🤖 AI分析を実行する」ボタンを押すと、この企業名に関する最新の知財・技術レポートが自動生成されます。",
    False, False, False, False, False
]
for k, v in zip(keys, vals):
    if k not in st.session_state: st.session_state[k] = v

st.subheader("🔑 1. AI鍵設定")
api_key = st.text_input("Gemini API Key", type="password", key="g_key")

t1, t2, t3, t4 = st.tabs(["📊 財務手入力", "🔒 モート評価", "🎯 試算結果", "🤖 AI分析・名前検索"])

with t1:
    st.subheader("1. 財務数値を手入力（四季報や株探の数値を入力）")
    st.session_state.c_name = st.text_input("企業名（例: ソニーグループ）", value=st.session_state.c_name, key="in_name")
    st.session_state.c_prc = st.number_input("現在の株価（円）", value=float(st.session_state.c_prc), key="nm_cp")
    st.session_state.f_base = st.number_input("フリーキャッシュフロー（億円）", value=float(st.session_state.f_base), key="nm_fb")
    st.session_state.n_debt = st.number_input("純有利子負債（億円）", value=float(st.session_state.n_debt), key="nm_nd")
    st.session_state.shs = st.number_input("発行済株式数（万株）", value=float(st.session_state.shs), key="nm_sh")
    st.session_state.bt = st.number_input("ベータ値（β）", value=float(st.session_state.bt), key="nm_bt")
    st.session_state.eq_r = st.number_input("自己資本比率（0.0〜1.0）", value=float(st.session_state.eq_r), min_value=0.0, max_value=1.0, key="nm_eq")

with t2:
    st.subheader("2. 経済的お堀（モート）の自己評価")
    st.session_state.m1 = st.checkbox("🔮 強力なブランド力があるか？", value=st.session_state.m1, key="ck_m1")
    st.session_state.m2 = st.checkbox("🔗 他社への乗り換えコストが高いか？", value=st.session_state.m2, key="ck_m2")
    st.session_state.m3 = st.checkbox("🪙 圧倒的な低コスト構造があるか？", value=st.session_state.m3, key="ck_m3")
    st.session_state.m4 = st.checkbox("📜 特許や政府の許認可に守られているか？", value=st.session_state.m4, key="ck_m4")
    st.session_state.m5 = st.checkbox("🕸️ 強固なネットワーク効果があるか？", value=st.session_state.m5, key="ck_m5")

# パラメータ計算
c_eq = 0.01 + (st.session_state.bt * 0.06)
c_wacc = (c_eq * st.session_state.eq_r) + (0.02 * (1 - st.session_state.eq_r))
g_s1_p = st.session_state.g_s1 / 100
g_t_p = st.session_state.g_t / 100

if g_t_p >= c_wacc or st.session_state.shs == 0: 
    ins_v, tg_p, ins_lbl, tg_lbl = 0, 0, "未入力", "未入力"
else:
    pv = 0
    f = st.session_state.f_base
    for y in range(1, 6): f = f * (1 + g_s1_p); pv += f / ((1 + c_wacc) ** y)
    for y in range(6, 11): f = f * (1 + g_t_p); pv += f / ((1 + c_wacc) ** y)
    sh_v = (pv + ((f * (1 + g_t_p)) / (c_wacc - g_t_p)) / ((1 + c_wacc) ** 10)) - st.session_state.n_debt
    ins_v = max(0, (sh_v * 1E8) / (st.session_state.shs * 1E4))
    m_score = sum([st.session_state.m1, st.session_state.m2, st.session_state.m3, st.session_state.m4, st.session_state.m5])
    tg_p = ins_v * (1 - (0.40 - (m_score * 0.05)))
    cur_p = st.session_state.c_prc
    ins_lbl = f"{'+' if ((cur_p - ins_v)/ins_v*100) >= 0 else ''}{(cur_p - ins_v)/ins_v*100:.1f}%" if ins_v > 0 else "不可"
    tg_lbl = f"{'+' if ((cur_p - tg_p)/tg_p*100) >= 0 else ''}{(cur_p - tg_p)/tg_p*100:.1f}%" if tg_p > 0 else "不可"

with t3:
    st.subheader("3. 計算結果（数値シミュレーション）")
    st.session_state.g_s1 = st.number_input("今後5年の予測成長率(％)", value=float(st.session_state.g_s1), step=0.5, key="nm_g1")
    st.session_state.g_t = st.number_input("6年目以降の永久成長率(％)", value=float(st.session_state.g_t), step=0.1, key="nm_gt")
    st.write("---")
    if st.session_state.shs == 0:
        st.info("💡 タブ1で財務数値を入力すると、ここに自動で適正株価が計算されます。")
    elif g_t_p >= c_wacc: 
        st.error("永久成長率エラー：WACC未満に調整してください")
    else:
        st.success(f"📊 {st.session_state.c_name} の試算結果")
        col1, col2, col3 = st.columns(3)
        col1.metric("🏪 現在株価", f"{int(cur_p):,}円")
        col2.metric("🎯 適正", f"{int(ins_v):,}円", f"現在 {ins_lbl}", "inverse")
        col3.metric("🛡️ 上限", f"{int(tg_p):,}円", f"現在 {tg_lbl}", "inverse")
        st.write("---")
        st.subheader("📢 投資判断シグナル")
        if cur_p <= tg_p: st.success("✅ 【Buy】買付上限以下です。")
        elif cur_p <= ins_v: st.warning("⚠️ 【Hold】理論価値の範囲内ですが余裕不足です。")
        else: st.error("❌ 【Avoid】割高水準です。")

with t4:
    st.subheader("🤖 AI多角的ビジネス解析 ＆ 名前検索")
    st.caption("入力された「企業名」をベースに、AIがその企業の最新の特許・技術競争力、ビジネスモデルを深掘りします")
    
    if st.button("🤖 企業名からAI分析を実行する", type="primary", use_container_width=True, key="btn_ai"):
        if not api_key: 
            st.error("キー未入力です。画面上部に貼り付けてください。")
        elif not st.session_state.c_name:
            st.error("企業名が空欄です。タブ1の「企業名」の欄に、調べたい会社名を入力してください。")
        else:
            try:
                with st.spinner(f"Gemini AIが「{st.session_state.c_name}」の最新技術・知財データをリサーチ中..."):
                    u = f"https://googleapis.com{api_key}"
                    
                    # 💡 財務数値が未入力でも、名前だけでAIがインターネット情報を元に独自の定性・知財分析を行えるようにプロンプトを強化
                    txt = f"投資家ウォーレン・バフェットの視点を持つアナリストとして、以下の企業を徹底的に日本語でリサーチ・分析したレポートを作成してください。特に最新の技術トレンド、特許資産、研究開発（R&D）への注力度、AIやデジタル戦略、他社に対する技術的な優位性や参入障壁（経済的お堀＝モート）を深く掘り下げてください。企業名:{st.session_state.c_name} (手入力財務参考値がある場合 FCF:{st.session_state.f_base}億円 純負債:{st.session_state.n_debt}億円) 見出し:1️⃣ 企業のビジネスモデル特性と市場ポジション 2️⃣ 🔮 経済的お堀（モート）の強さ評価 3️⃣ 💡【最重要】技術・知財・R&Dイノベーション競争力（他社が真似できない強み） 4️⃣ 総括と長期的なテクノロジーリスク"
                    
                    res = requests.post(u, headers={"Content-Type": "application/json"}, json={"contents": [{"parts": [{"text": txt}]}]}, timeout=25)
                    if res.status_code == 200: 
                        st.session_state.ai_rep = res.json()["candidates"][0]["content"]["parts"][0]["text"]
                    else: 
                        st.session_state.ai_rep = f"通信失敗 コード: {res.status_code} キーが正しいか確認してください。"
                st.success("AIレポートの生成が完了しました！")
            except Exception as e: 
                st.error(f"解析失敗: {e}")
    st.write("---")
    st.markdown(st.session_state.ai_rep)
