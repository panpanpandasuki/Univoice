import streamlit as st
import google.generativeai as genai
import gspread
import pandas as pd
from datetime import datetime

# ==========================================
# ⚙️ 設定エリア
# ==========================================
TEACHER_DB = {
    "tanaka": {"name": "田中先生", "pass": "1234"},
    "sato":   {"name": "佐藤先生", "pass": "5678"},
    "suzuki": {"name": "鈴木先生", "pass": "9999"}
}

# ==========================================
# 1. APIとスプレッドシートの接続設定
# ==========================================
# Geminiの設定
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-pro')
except:
    st.error("⚠️ GeminiのAPIキーが設定されていません")
    # スプレッドシートの設定
try:
    # Secretsからデータを取り出す
    secret_data = st.secrets["gcp_service_account"]

    # 鍵のクリーニング処理（念入り版）
    # 1. 改行コードを直す
    # 2. 前後の余計な空白(.strip)を消す ← これを追加！
    pkey = secret_data["private_key"].replace("\\n", "\n").strip()

    credentials_dict = {
        "type": "service_account",
        "project_id": "unknown",
        "private_key_id": "unknown",
        "private_key": pkey,  # クリーニングした鍵を使う
        "client_email": secret_data["client_email"],
        "client_id": "unknown",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "unknown"
    }

    client = gspread.service_account_from_dict(credentials_dict)
    sheet = client.open("univoice_db").sheet1
    
except Exception as e:
    st.error(f"⚠️ スプレッドシートへの接続に失敗しました: {e}")
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "unknown"
    }

    # 新しいシンプルな接続方法（gspread純正）
    # 古い oauth2client は使いません！
    client = gspread.service_account_from_dict(credentials_dict)
    
    # スプレッドシートを開く
    sheet = client.open("univoice_db").sheet1
    
except Exception as e:
    st.error(f"⚠️ スプレッドシートへの接続に失敗しました: {e}")

# ==========================================
# 2. 画面のデザイン
# ==========================================
st.set_page_config(page_title="UniVoice", page_icon="🎓")

st.sidebar.title("メニュー")
mode = st.sidebar.radio("モードを選択", ["📮 学生用（相談を送る）", "🏫 先生用（相談を見る）"])

# ==========================================
# 3. 学生用モード
# ==========================================
if mode == "📮 学生用（相談を送る）":
    st.title("📮 先生への匿名相談BOX")
    st.write("ここで送った内容は、AIが丁寧に修正して先生に届きます。")

    teacher_options = [data["name"] for data in TEACHER_DB.values()]
    selected_teacher_name = st.selectbox("誰に送りますか？", teacher_options)

    user_text = st.text_area("相談したい内容", height=150)

    if st.button("送信する 🚀"):
        if not user_text:
            st.warning("内容を書いてください！")
        else:
            with st.spinner("送信中..."):
                try:
                    prompt = f"""
                    以下の相談内容を、先生に送るのにふさわしい丁寧な文章に直してください。
                    宛先：{selected_teacher_name}
                    内容：{user_text}
                    """
                    response = model.generate_content(prompt)
                    ai_text = response.text
                    now = datetime.now().strftime("%Y/%m/%d %H:%M")
                    
                    sheet.append_row([now, selected_teacher_name, user_text, ai_text])
                    st.success("✅ 送信完了しました！")
                    st.info(ai_text)
                except Exception as e:
                    st.error(f"エラー: {e}")

# ==========================================
# 4. 先生用モード
# ==========================================
elif mode == "🏫 先生用（相談を見る）":
    st.title("🏫 教員用管理画面")
    
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        with st.form("login_form"):
            user_id = st.text_input("先生ID")
            password = st.text_input("パスワード", type="password")
            if st.form_submit_button("ログイン"):
                if user_id in TEACHER_DB and TEACHER_DB[user_id]["pass"] == password:
                    st.session_state.logged_in = True
                    st.session_state.teacher_name = TEACHER_DB[user_id]["name"]
                    st.rerun()
                else:
                    st.error("IDかパスワードが違います")
    else:
        st.subheader(f"{st.session_state.teacher_name} 宛てのメッセージ")
        if st.button("ログアウト"):
            st.session_state.logged_in = False
            st.rerun()

        try:
            data = sheet.get_all_values()
            df = pd.DataFrame(data[1:], columns=data[0])
            my_messages = df[df["宛先"] == st.session_state.teacher_name]

            if len(my_messages) == 0:
                st.info("メッセージはありません。")
            else:
                for index, row in my_messages.iterrows():
                    with st.expander(f"📩 {row['日付']}"):
                        st.write(row["AI修正後の内容"])
                        st.caption("元の内容: " + row["元の内容"])
        except Exception as e:
            st.error("データ読み込み失敗")
