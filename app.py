import streamlit as st
import google.generativeai as genai
from gtts import gTTS
from io import BytesIO

# === 画面の基本設定 ===
st.set_page_config(page_title="患者シミュレーター", page_icon="🩺")
st.title("🩺 患者シミュレーター (音声対話版)")

# === サイドバー（設定画面） ===
with st.sidebar:
    st.header("⚙️ 設定パネル")
    
    api_key = st.text_input("Gemini APIキーを入力", type="password")
    st.caption("※Google AI Studioで取得したAPIキーを入力してください。")
    
    st.divider()
    
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
    
    patient_setting = st.text_area("プロンプト（設定）を編集", value=default_prompt, height=250)
    
    if st.button("🔄 設定を反映してチャットをリセット"):
        st.session_state.messages = []
        st.session_state.chat = None
        st.rerun()

if not api_key:
    st.info("👈 まずは左側のサイドバーにGemini APIキーを入力してください。")
    st.stop()

# === AIの初期設定 ===
genai.configure(api_key=api_key)

if "messages" not in st.session_state:
    st.session_state.messages = []

if "chat" not in st.session_state or st.session_state.chat is None:
    model = genai.GenerativeModel(
        "gemini-3.6-flash-latest", 
        system_instruction=patient_setting
    )
    st.session_state.chat = model.start_chat(history=[])

# === チャット画面の表示 ===
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# === 音声入力ウィジェット（トランシーバー型） ===
audio_value = st.audio_input("🎤 マイクボタンを押して患者に話しかける")

# 音声入力があった場合の処理
if audio_value:
    audio_bytes = audio_value.read()
    
    # ユーザー表示用メッセージ
    with st.chat_message("user"):
        st.audio(audio_bytes, format="audio/wav")
        st.caption("※音声メッセージを送信しました")
    st.session_state.messages.append({"role": "user", "content": "🎙️ (音声入力)"})

    # AI（患者）の応答を取得
    with st.chat_message("assistant"):
        try:
            # 音声データをGeminiへ直接送信
            audio_data = {
                "mime_type": "audio/wav",
                "data": audio_bytes
            }
            response = st.session_state.chat.send_message([audio_data, "この音声を聞いて患者として回答してください。"])
            
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            
            # 返答を音声合成して自動再生
            tts = gTTS(text=response.text, lang='ja')
            audio_fp = BytesIO()
            tts.write_to_fp(audio_fp)
            st.audio(audio_fp.getvalue(), format="audio/mp3", autoplay=True)

        except Exception as e:
            st.error(f"エラーが発生しました: {e}")
