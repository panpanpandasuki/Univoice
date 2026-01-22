import streamlit as st
import google.generativeai as genai
import datetime
import pandas as pd  # グラフを作るための計算部品

# ==========================================
# 1. APIキーの設定
# ==========================================
import streamlit as st  # これが必要です
import google.generativeai as genai

# ==========================================
# 1. APIキーの設定（クラウド対応版）
# ==========================================
try:
    # Streamlit Cloud（ネット上）で動くときは、
    # 向こうの「秘密の金庫」からキーを読み込みます
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
except:
    # GitHubに上げるために、ここはわざと空欄にしておきます
    GOOGLE_API_KEY = ""

genai.configure(api_key=GOOGLE_API_KEY)
# ==========================================
# 2. 設定（パスワード）
# ==========================================
PASSWORD_STUDENT = "student"
PASSWORD_PROF = "teacher"

# ==========================================
# 3. 準備
# ==========================================
if "messages_db" not in st.session_state:
    st.session_state["messages_db"] = []

if "login_status" not in st.session_state:
    st.session_state["login_status"] = "LOGOUT"

def ai_rewrite(text):
    """Gemini 2.5 で変換"""
    prompt = f"""
    以下の学生の言葉を、大学教授への要望として適切なビジネス敬語に書き換えてください。
    【絶対ルール】
    1. 差出人の名前は一切出さず、「ある学生より」としてください。
    2. 個人が特定されるような表現はぼかしてください。
    3. 攻撃的な言葉は、建設的な「要望」や「提案」の言葉に変換してください。
    
    元の言葉: {text}
    """
    try:
        model = genai.GenerativeModel('models/gemini-2.5-flash')
        response = model.generate_content(prompt)
        return response.text
    except:
        return "エラー"

# ==========================================
# 4. 画面切り替え
# ==========================================
st.sidebar.title("UniVoice")
mode = st.sidebar.radio("モード選択", ["ホーム", "学生モード", "教授モード"])

if st.sidebar.button("ログアウト"):
    st.session_state["login_status"] = "LOGOUT"
    st.rerun()

# ==========================================
# A. ホーム
# ==========================================
if mode == "ホーム":
    st.title("UniVoice へようこそ")
    st.write("匿名で意見を届け、授業をより良くするためのプラットフォームです。")
    st.info(f"テスト用パスワード：\n- 学生用: {PASSWORD_STUDENT}\n- 教授用: {PASSWORD_PROF}")

# ==========================================
# B. 学生モード
# ==========================================
elif mode == "学生モード":
    if st.session_state["login_status"] != "STUDENT":
        st.subheader("学生ログイン")
        input_pass = st.text_input("パスワード", type="password")
        if st.button("ログイン"):
            if input_pass == PASSWORD_STUDENT:
                st.session_state["login_status"] = "STUDENT"
                st.rerun()
            else:
                st.error("パスワードが違います")
    else:
        st.title("🕊 匿名意見ボックス")
        
        # --- 入力エリア ---
        col1, col2 = st.columns([2, 1])
        with col1:
            student_text = st.text_area("本音を書いてください", height=150)
        with col2:
            category = st.radio("カテゴリ", ["授業スピード", "課題の量", "進路相談", "その他"])

        if st.button("匿名で送信する"):
            if student_text:
                with st.spinner("AIが暗号化中..."):
                    clean_text = ai_rewrite(student_text)
                    now = datetime.datetime.now().strftime("%m/%d %H:%M")
                    # データに「元の文章」も含めて保存（学生が見るため）
                    new_msg = {
                        "time": now,
                        "category": category,
                        "content": clean_text,
                        "original": student_text
                    }
                    st.session_state["messages_db"].append(new_msg)
                    st.success("送信完了！")
            else:
                st.warning("文字を入力してください")

        # --- ★追加機能：自分の送信履歴 ---
        st.divider()
        st.subheader("あなたの送信履歴")
        st.caption("※ここに履歴が表示されますが、教授には「変換後（右側）」しか見えていません。")
        
        messages = st.session_state["messages_db"]
        if len(messages) > 0:
            for msg in reversed(messages):
                with st.expander(f"{msg['time']} : {msg['category']}"):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown("**あなた（元の言葉）**")
                        st.text(msg['original'])
                    with c2:
                        st.markdown("**教授へ届いた言葉**")
                        st.info(msg['content'])
        else:
            st.write("まだ履歴はありません。")

# ==========================================
# C. 教授モード
# ==========================================
elif mode == "教授モード":
    if st.session_state["login_status"] != "PROF":
        st.subheader("教授ログイン")
        input_pass = st.text_input("パスワード", type="password")
        if st.button("ログイン"):
            if input_pass == PASSWORD_PROF:
                st.session_state["login_status"] = "PROF"
                st.rerun()
            else:
                st.error("パスワードが違います")
    else:
        st.title("📊 教授用ダッシュボード")
        messages = st.session_state["messages_db"]

        # --- ★追加機能：データ分析グラフ ---
        if len(messages) > 0:
            st.subheader("意見の傾向データ")
            
            # カテゴリごとの数を数える
            df = pd.DataFrame(messages)
            category_counts = df['category'].value_counts()
            
            # 棒グラフを表示
            st.bar_chart(category_counts)
            
            # 一番多い意見を表示
            top_category = category_counts.idxmax()
            st.warning(f"💡 現在、 **「{top_category}」** に関する意見が最も多いです。")
            
        else:
            st.info("データが集まっていません。")

        # --- メッセージ一覧 ---
        st.divider()
        st.subheader("受信メッセージ一覧")
        
        if len(messages) == 0:
            st.write("新着なし")
        else:
            for i, msg in enumerate(reversed(messages)):
                # 教授には「丁寧な言葉」だけ見せる
                with st.expander(f"📥 {msg['time']} - {msg['category']}"):
                    st.write(msg['content'])
                    st.caption("※原文は非表示です")
