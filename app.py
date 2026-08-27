import streamlit as st
import google.generativeai as genai
import edge_tts
import asyncio

# === 画面の基本設定 ===
st.set_page_config(page_title="患者シミュレーター", page_icon="🩺")
st.title("🩺 信州さん")

# === サイドバー（設定画面） ===
with st.sidebar:
    st.header("⚙️ 設定パネル")
    
    # クラウドのSecretsにキーがあればそれを使い、なければ入力欄を表示
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
        st.success("✅ システムAPIキー接続済み")
    else:
        api_key = st.text_input("Gemini APIキーを入力", type="password")
        st.caption("※Google AI Studioで取得したAPIキーを入力してください。")
    
    st.divider()
    
    # 患者の基本設定（画面には表示させず、裏側でAIに読み込ませる）
    patient_setting = """あなたは以下の設定を持つ患者として振る舞ってください。
学生の質問に対して、一般人の言葉遣いで答えてください。
専門用語は使わず、聞かれたことだけに短く答えてください。

【患者情報】
- 氏名: 山田 太郎（65歳・男性）
- 主訴: 2日前からの胸の圧迫感
- 既往歴: 高血圧（薬はたまに飲み忘れる）
- 家族歴: 父親が心筋梗塞
- 性格: 少し不安そうにしている。痛みの詳細を聞かれるまで自分からは多くを語らない。"""
    
    if st.button("🔄 最初からやり直す（リセット）"):
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
        "gemini-3.6-flash", 
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
    # 音声データの形式（mime_type）を取得
    audio_type = audio_value.type
    
    # ユーザー表示用メッセージ
    with st.chat_message("user"):
        st.audio(audio_bytes, format=audio_type) # 形式を動的に設定
        st.caption("※音声メッセージを送信しました")
    st.session_state.messages.append({"role": "user", "content": "🎙️ (音声入力)"})

    # AI（患者）の応答を取得
    with st.chat_message("assistant"):
        try:
            # 音声データをGeminiへ直接送信
            audio_data = {
                "mime_type": audio_type, # 形式を動的に設定
                "data": audio_bytes
            }
            response = st.session_state.chat.send_message([audio_data, "この音声を聞いて患者として回答してください。"])
            
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            
            # 返答を音声合成して自動再生（男性の声：Keita）
            async def make_audio():
                communicate = edge_tts.Communicate(response.text, "ja-JP-KeitaNeural")
                audio_data = b""
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        audio_data += chunk["data"]
                return audio_data
            
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            audio_bytes = loop.run_until_complete(make_audio())
            st.audio(audio_bytes, format="audio/mp3", autoplay=True)

        except Exception as e:
            st.error(f"エラーが発生しました: {e}")
