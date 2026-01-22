import streamlit as st
import google.generativeai as genai

# ==========================================
# 1. APIキーの設定
# ==========================================
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
except:
    GOOGLE_API_KEY = ""

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-pro')

# ==========================================
# 2. 画面のデザイン
# ==========================================
st.set_page_config(page_title="UniVoice", page_icon="🎓")

# サイドバー（メニュー）
st.sidebar.title("メニュー")
mode = st.sidebar.radio("選んでください", ["ホーム", "メール作成ツール"])

# ==========================================
# 3. ホーム画面
# ==========================================
if mode == "ホーム":
    st.title("UniVoice へようこそ ")
    st.write("大学生活の「困った」をAIが解決します。")
    st.info("左のメニューから「メール作成ツール」を選んでね！")

# ==========================================
# 4. メール作成ツール（先生リスト機能付き）
# ==========================================
elif mode == "メール作成ツール":
    st.title("教授へのメール作成")

    # ▼▼▼ ここで先生のリストを作ります（ID代わり） ▼▼▼
    # 左側に名前、右側にメールアドレスを書きます
    teacher_list = {
        "手入力（リストにない場合）": "",
        "田中先生": "tanaka@university.ac.jp",
        "佐藤先生": "sato@university.ac.jp",
        "鈴木先生": "suzuki@university.ac.jp"
    }
    
    # セレクトボックス（選択肢）を表示
    selected_teacher = st.selectbox("宛先の先生を選んでください", list(teacher_list.keys()))

    # 選んだ先生によって動きを変える
    if selected_teacher == "手入力（リストにない場合）":
        teacher_name = st.text_input("先生の名前（名字のみ）", placeholder="例：田中")
        teacher_email = st.text_input("先生のメールアドレス")
    else:
        # "田中先生" という文字から "先生" を取って名前にする
        teacher_name = selected_teacher.replace("先生", "")
        teacher_email = teacher_list[selected_teacher]
        st.info(f"送信先: {selected_teacher} ({teacher_email})")

    # 本文を入れる欄
    text_input = st.text_area("伝えたい内容", height=200, placeholder="・風邪をひいたので休みます...")

    # ボタン
    if st.button("メールを作る 📝"):
        if not teacher_name:
            st.warning("⚠️ 先生の名前を入力してください！")
        elif not text_input:
            st.warning("⚠️ 内容を入力してください！")
        else:
            with st.spinner("AIが考え中..."):
                prompt = f"""
                宛先: {teacher_name} 先生
                内容: {text_input}
                条件: 丁寧な大学のメール形式で作成。件名も含める。
                """
                
                try:
                    response = model.generate_content(prompt)
                    st.success("✨ 完成！以下の文章をコピーしてメールで送ってください")
                    
                    # 便利なコピー用エリア
                    st.code(response.text)
                    
                    # メールアドレスも表示してあげる
                    if teacher_email:
                        st.write(f"📧 **送信先アドレス:** `{teacher_email}`")
                        st.caption("↑ これを宛先にコピペしてね！")
                    
                except Exception as e:
                    st.error("エラーが発生しました")
