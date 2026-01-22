import streamlit as st
import google.generativeai as genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import pandas as pd
from datetime import datetime

# ==========================================
# ⚙️ 設定エリア（先生のパスワードはここで決める）
# ==========================================
# 先生のIDとパスワードの設定
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
    # SecretsからJSON文字列を読み込んで辞書に変換
    json_key = json.loads(st.secrets["GCP_SERVICE_ACCOUNT"])
    scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_dict(json_key, scope)
    client = gspread.authorize(creds)
    
    # スプレッドシートを開く（名前が間違っているとエラーになるので注意！）
    sheet = client.open("univoice_db").sheet1
except Exception as e:
    st.error(f"⚠️ スプレッドシートへの接続に失敗しました: {e}")

# ==========================================
# 2. 画面のデザイン
# ==========================================
st.set_page_config(page_title="UniVoice", page_icon="🎓")

# サイドバーでモード切替
st.sidebar.title("メニュー")
mode = st.sidebar.radio("モードを選択", ["学生用（相談を送る）", "先生用（相談を見る）"])

# ==========================================
# 3. 学生用モード（匿名送信）
# ==========================================
if mode == "学生用（相談を送る）":
    st.title("先生への匿名相談BOX")
    st.write("ここで送った内容は、AIが丁寧に修正して先生に届きます。")
    st.info("誰が送ったかは先生には分かりません（匿名）。安心して書いてね。")

    # 先生を選ぶ
    teacher_options = [data["name"] for data in TEACHER_DB.values()]
    selected_teacher_name = st.selectbox("誰に送りますか？", teacher_options)

    # 相談内容
    user_text = st.text_area("相談したい内容（愚痴でも質問でもOK！）", height=150, 
                             placeholder="例：授業の進むスピードが速すぎてついていけません...、来週休みます")

    if st.button("送信する "):
        if not user_text:
            st.warning("内容を書いてください！")
        else:
            with st.spinner("AIが文章を整えて送信中..."):
                try:
                    # AIに文章を整えさせる
                    prompt = f"""
                    以下の学生からの相談内容を、先生に送るのにふさわしい「丁寧で失礼のない文章」にリライトしてください。
                    匿名なので署名は不要です。
                    
                    【宛先】{selected_teacher_name}
                    【元の内容】{user_text}
                    """
                    response = model.generate_content(prompt)
                    ai_text = response.text

                    # 現在時刻
                    now = datetime.now().strftime("%Y/%m/%d %H:%M")

                    # スプレッドシートに保存（日付, 宛先, 元の内容, AI修正後の内容）
                    sheet.append_row([now, selected_teacher_name, user_text, ai_text])

                    st.success("✅ 送信完了しました！")
                    st.write("▼ 実際に先生に届いた内容")
                    st.info(ai_text)
                
                except Exception as e:
                    st.error(f"エラーが発生しました: {e}")

# ==========================================
# 4. 先生用モード（ログイン＆分析）
# ==========================================
elif mode == "先生用（相談を見る）":
    st.title("教員用管理画面")
    
    # ログイン画面
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        with st.form("login_form"):
            user_id = st.text_input("先生ID (例: tanaka)")
            password = st.text_input("パスワード", type="password")
            submit = st.form_submit_button("ログイン")
            
            if submit:
                if user_id in TEACHER_DB and TEACHER_DB[user_id]["pass"] == password:
                    st.session_state.logged_in = True
                    st.session_state.teacher_name = TEACHER_DB[user_id]["name"]
                    st.success(f"ようこそ、{st.session_state.teacher_name}！")
                    st.rerun() # 画面リロード
                else:
                    st.error("IDまたはパスワードが違います")
    else:
        # ログイン後の画面
        teacher_name = st.session_state.teacher_name
        st.subheader(f"{teacher_name} 宛てのメッセージ一覧")
        
        if st.button("ログアウト"):
            st.session_state.logged_in = False
            st.rerun()

        # スプレッドシートからデータを取得
        try:
            # 全データを取得してDataFrameにする
            data = sheet.get_all_values()
            # 1行目をヘッダーとして扱う
            df = pd.DataFrame(data[1:], columns=data[0])
            
            # 自分宛てのメッセージだけフィルター
            my_messages = df[df["宛先"] == teacher_name]

            if len(my_messages) == 0:
                st.info("現在、新しいメッセージはありません。")
            else:
                st.write(f"お疲れ様です。**{len(my_messages)}件** の相談が届いています。")
                
                # データ表示
                for index, row in my_messages.iterrows():
                    with st.expander(f"📩 {row['日付']} のメッセージ"):
                        st.write("**【AI修正版】**")
                        st.write(row["AI修正後の内容"])
                        st.divider()
                        st.caption("▼ 学生が入力した元の内容")
                        st.text(row["元の内容"])

        except Exception as e:
            st.error("データの読み込みに失敗しました")
