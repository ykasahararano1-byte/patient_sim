import streamlit as st
import google.generativeai as genai
import streamlit as st
import google.generativeai as genai
from gtts import gTTS
from io import BytesIO

# === 画面の基本設定 ===
st.set_page_config(page_title="患者シミュレーター", page_icon="🩺")
st.title("🩺 患者シミュレーター (医療面接練習)")

# === サイドバー（設定画面） ===
with st.sidebar:
    st.header("⚙️ 設定パネル")
    
    # APIキーの入力欄
    api_key = st.text_input("Gemini APIキーを入力", type="password")
    st.caption("※Google AI Studioで取得したAPIキーを入力してください。")
    
    st.divider()
    
    # 患者の設定（ここで編集可能）
    st.subheader("📝 患者の基本設定")
    default_prompt = """あなたは以下の設定を持つ患者として振る舞ってください。
学生の質問に対して、一般人の言葉遣いで答えてください。
専門用語は使わず、聞かれたことだけに短く答えてください。

【患者情報】
- 氏名: 山田 太郎（65歳・男性）
- 主訴: 2日前からの胸の圧迫感
- 既往歴: 高血圧（薬はたまに飲み忘れる）
- 家族歴: 父親が心筋梗塞
- 性格: 少し不安そうにしている。痛みの詳細を聞かれるまで自分からは多くを語らない。"""
    
    patient_setting = st.text_area("プロンプト（設定）を編集", value=default_prompt, height=300)
    
    # 設定をリセットして最初からやり直すボタン
    if st.button("🔄 設定を反映してチャットをリセット"):
        st.session_state.messages = []
        st.session_state.chat = None
        st.rerun()

# APIキーが入力されていない場合はここでストップ
if not api_key:
    st.info("👈 まずは左側のサイドバーにGemini APIキーを入力してください。")
    st.stop()

# === AIの初期設定 ===
genai.configure(api_key=api_key)

# チャット履歴を保存する箱を作る
if "messages" not in st.session_state:
    st.session_state.messages = []

# AIモデルの初期化（設定プロンプトを読み込ませる）
if "chat" not in st.session_state or st.session_state.chat is None:
    # システムプロンプト（患者設定）をAIに指示
    model = genai.GenerativeModel(
        "gemini-3.6-flash", 
        system_instruction=patient_setting
    )
    st.session_state.chat = model.start_chat(history=[])

# === チャット画面の表示 ===
# 過去の会話履歴を画面に描画
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# === ユーザー（学生）からの入力 ===
if user_input := st.chat_input("患者に質問してください（例：今日はどうされましたか？）"):
    
    # ユーザーの入力を画面に表示＆保存
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # AI（患者）の応答を取得して画面に表示＆保存
    with st.chat_message("assistant"):
        try:
            response = st.session_state.chat.send_message(user_input)
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            tts = gTTS(text=response.text, lang='ja') # 日本語の音声を生成
            audio_fp = BytesIO()
            tts.write_to_fp(audio_fp)
            st.audio(audio_fp.getvalue(), format="audio/mp3", autoplay=True) # 自動再生
        except Exception as e:
            st.error(f"エラーが発生しました。APIキーが間違っていないか確認してください。\n詳細: {e}")