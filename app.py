import streamlit as st
import streamlit.components.v1 as components
import google.generativeai as genai
import edge_tts
import asyncio
import base64

# === 画面の基本設定 ===
st.set_page_config(page_title="患者シミュレーター", page_icon="🩺", layout="wide")
st.title("🩺 患者シミュレーター (長押しマイク版)")

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
学生の質問に対して、一般人の言葉遣いで答え、短く話してください。
専門用語は使わず、聞かれたことだけに短く答してください。
痛みや不安を表現するような声色（「うーん」などの間）を少し交えてください。

【患者情報】
- 氏名: 信州　俊彦（50歳代後半・男性）
- 診断名: 虚血性心疾患（狭心症）三枝病変、2型糖尿病、高血圧、脂質異常症
- 職業: 会社員（営業部長）
- 既往歴: 2型糖尿病、高血圧、脂質異常症
- 家族構成: 地方都市で妻（主婦）と二人暮らし。長男夫婦（長男30歳代前半・会社員、長男の妻・クリニック勤務看護師）、孫（5歳、3歳共に男児、平日は保育園）が同じ市に住んでいる。休日は孫が遊びに来ることが多く、孫と遊ぶことを楽しみにしている。
- 生活歴: 営業部長職として、接待や付き合いで週に2～3回外食をすることがあり、帰宅は深夜になることもある。管理職になりストレスは増大した。飲酒は外食時の機会飲酒のみ。タバコは20歳から30年以上1日2箱（40本）吸っていたが、2年前から禁煙に取り組み、現在は1日10本程度。飲食の嗜好は、野菜が苦手で、肉が好き。味付けは濃い目のものを好み、特にラーメンや蕎麦など麺類が好物である。塩分量を気にして、汁は残すようにしている。糖尿病の教育入院後、糖尿病の悪化を心配する妻はパートを辞め、信州さんのためにカロリー制限や減塩を考えた調理を工夫しているが、不満を言って一人で外食をすることもあった。朝、夕食は妻の手料理、昼食は社員食堂で定食を頼むようにしていた。通勤は自家用車で、休日も出勤することが多い。趣味の釣りは、月に2回出かける程度で、インターネットで釣り情報を収集している。運動不足を解消するためにエルゴメーターを購入したが、利用頻度は週に1～2回10分程度であった。毎日の睡眠時間は6時間程度、熟睡感はある。排尿は1日に5～6回、排便は2～3日に1回程度である。
- 現病歴: 約20年前に会社の健診で尿糖（＋）、高血圧症、脂質異常症を指摘された。約10年前に糖尿病と診断され、定期的に外来通院していた。7年前から内服薬メトグルコ®500mg/日を処方されていたが、2年前に自己中断。定期受診も中断し糖尿病が悪化。約2年前に1週間、糖尿病の教育入院をした。その後は定期受診を続け、糖尿病、高血圧、脂質異常症の治療を継続している。2か月前から、階段を上るときや早歩きをした時に胸部が圧迫される違和感があり、定期受診時に医師へ相談。トレッドミル負荷心電図でST低下の陽性所見があり、冠状動脈造影（CAG）を実施。多枝病変（RCA＃2 75％狭窄、LAD＃7 90％狭窄　＃9 75％狭窄、LCX＃11 50％ #14 75％狭窄）を認め、冠状動脈バイパス術目的で入院となった。服薬アドヒアランスは良好で、現在の内服薬は、メトグルコ®750㎎/日、ジャヌビア®50㎎/日、アムロジピン®OD錠5㎎/日、フランドルテープ40mg1枚/1日、ピタバスタチン®2㎎/日。ニトロール®錠5㎎ 胸痛発作時舌下（屯用）が処方されている。
- 性格: 人前では社交的で明るいが、本来は短気で頑固。仕事に対して完璧主義で、部下の仕事をフォローし自分でやってしまう面もある。部下や同僚から信頼されている。（妻・談）
- 主訴: 労作時の胸部圧迫感
- 術創: 胸部正中切開（開胸）：20㎝程度, 左大腿（グラフト採取部）：20㎝程度
- 身体への挿入物・装着物: 酸素カニュラ（経鼻）, 中心静脈（CV）カテーテル（右鎖骨下動脈）, 末梢静脈ライン（左前腕）, 心電図モニター（3点誘導）, ペーシングリード, 心嚢内ドレーン　1本, 前縦隔内ドレーン　1本, クオリブレス（胸帯）, 膀胱留置カテーテル, 弾性ストッキング
- 現在の時間: 術後2日目の10:00
- 現在のバイタルサイン: 体温37.4℃, 血圧138/82mmHg, 脈拍96回/分, SpO2 95%(酸素2L), 呼吸数24回/分
- 現在の呼吸音: 右肺上葉に水泡音
- 現在の痰の状態: 痰がらみがあり、咳嗽は痛いので我慢している、吸引をした場合の性状は透明〜白色でやや粘稠な痰が中等量出たことを認識している
- 現在の腸蠕動音: 減弱
- 現在の排ガス: なし
- 現在の創部: 胸部・大腿部とも出血、腫脹、発赤なし
- 現在の疼痛: すごく痛い、0〜10で聞かれたら6〜7くらい
- 痛み止めの使用を提案された場合の回答: 「どのくらいで効きますか？」
- 痛み止めを使用した場合: 少し経ったら「マシになった」「今の痛みは3くらい」"""
    
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
    # モデル名を安定バージョンに戻します
    model = genai.GenerativeModel(
        "gemini-1.5-flash", 
        system_instruction=patient_setting
    )
    st.session_state.chat = model.start_chat(history=[])

# === チャット画面の表示 ===
# チャットメッセージを表示するコンテナを作成
chat_container = st.container()
with chat_container:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            # 音声データがあれば表示（自動再生されるので、再生ボタンは表示させない）
            if "assistant" == msg["role"] and "audio" in msg:
                # st.audio(msg["audio"], format="audio/mp3") # 自動再生するので非表示
                pass

# === 長押しマイクコンポーネント（インライン実装） ===

def ptt_mic_component():
    # JavaScript, HTML, CSSをインラインで記述
    component_code = """
    <style>
        #ptt-button {
            position: fixed;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            width: 150px;
            height: 150px;
            background-color: #ff4b4b;
            color: white;
            border: none;
            border-radius: 50%;
            font-size: 60px;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            display: flex;
            align-items: center;
            justify-content: center;
            outline: none;
            -webkit-tap-highlight-color: transparent; /* モバイルでのタップハイライトを無効化 */
            transition: background-color 0.2s;
            z-index: 9999;
        }
        #ptt-button:active {
            background-color: #b52b2b;
        }
        #status {
            position: fixed;
            bottom: 180px;
            left: 50%;
            transform: translateX(-50%);
            color: white;
            font-size: 18px;
            font-weight: bold;
            background-color: rgba(0,0,0,0.5);
            padding: 5px 10px;
            border-radius: 5px;
            display: none;
            z-index: 9998;
        }
    </style>
    
    <div id="status">録音中...</div>
    <button id="ptt-button">🎤</button>
    
    <script>
        // Streamlitとの通信用
        function sendValue(value) {
            Streamlit.setComponentValue(value);
        }

        const button = document.getElementById('ptt-button');
        const status = document.getElementById('status');
        let mediaRecorder;
        let audioChunks = [];

        async function startRecording() {
            try {
                // MediaStream Recording APIを使用して音声を録音
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                mediaRecorder = new MediaRecorder(stream);
                
                mediaRecorder.ondataavailable = (event) => {
                    audioChunks.push(event.data);
                };

                mediaRecorder.onstop = async () => {
                    const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                    audioChunks = []; // クリア

                    // BlobをBase64に変換してPythonに送る
                    const reader = new FileReader();
                    reader.readAsDataURL(audioBlob);
                    reader.onloadend = () => {
                        // データURLからBase64部分のみを抽出
                        const base64Audio = reader.result.split(',')[1];
                        sendValue(base64Audio);
                    };
                    
                    // マイクの使用を停止
                    stream.getTracks().forEach(track => track.stop());
                };

                mediaRecorder.start();
                status.style.display = 'block';
                console.log('Recording started');
            } catch (err) {
                console.error('Error accessing microphone:', err);
                status.innerText = 'マイクエラー';
                status.style.display = 'block';
            }
        }

        function stopRecording() {
            if (mediaRecorder && mediaRecorder.state === 'recording') {
                mediaRecorder.stop();
                status.style.display = 'none';
                console.log('Recording stopped');
            }
        }

        // マウスイベント
        button.addEventListener('mousedown', startRecording);
        button.addEventListener('mouseup', stopRecording);
        button.addEventListener('mouseleave', stopRecording); // ボタンから外れたら停止

        // タッチイベント (モバイル向け)
        button.addEventListener('touchstart', (e) => {
            e.preventDefault(); // デフォルトのスクロールなどを無効化
            startRecording();
        });
        button.addEventListener('touchend', stopRecording);
        
        // コンポーネントが準備できたら Streamlit に通知。高さを確保。
        Streamlit.setFrameHeight(180); 
    </script>
    """
    
    # コンポーネントを定義して呼び出す。
    declare_ptt_mic = components.declare_component("ptt_mic", content=component_code)
    # データを返させる。
    return declare_ptt_mic(key="ptt_mic_instance")

# === 音声入力処理ロジック ===

# カスタムコンポーネントからデータ（Base64文字列）を受け取る
base64_audio = ptt_mic_component()

# データがあった場合の処理
if base64_audio:
    try:
        # Base64をバイナリ（bytes）にデコード
        audio_bytes = base64.b64decode(base64_audio)
        
        # ユーザー表示用メッセージ（音声データをそのまま履歴に保存）
        st.session_state.messages.append({"role": "user", "content": "🎙️ (音声入力)"})
        with chat_container:
            with st.chat_message("user"):
                st.audio(audio_bytes, format="audio/wav")
                st.caption("※音声メッセージを送信しました")

        # AI（患者）の応答を取得
        with chat_container:
            with st.chat_message("assistant"):
                try:
                    # 音声データをGeminiへ直接送信
                    # (edge-ttsに切り替えたので、wavとして扱う)
                    audio_data = {
                        "mime_type": "audio/wav",
                        "data": audio_bytes
                    }
                    response = st.session_state.chat.send_message([audio_data, "この音声を聞いて患者として短く回答してください。"])
                    
                    st.markdown(response.text)
                    
                    # 返答を音声合成して自動再生（男性の声：Keita）
                    async def make_audio(text):
                        communicate = edge_tts.Communicate(text, "ja-JP-KeitaNeural")
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
                    
                    tts_audio_bytes = loop.run_until_complete(make_audio(response.text))
                    
                    # 履歴にも保存（表示用テキストと再生用音声）
                    st.session_state.messages.append({"role": "assistant", "content": response.text, "audio": tts_audio_bytes})
                    
                    # 自動再生（表示はしない）
                    st.audio(tts_audio_bytes, format="audio/mp3", autoplay=True)

                except Exception as e:
                    st.error(f"エラーが発生しました: {e}")
                    st.session_state.messages.append({"role": "assistant", "content": f"エラーが発生しました: {e}"})

    except Exception as e:
        st.error(f"音声データの変換エラー: {e}")

# === UIの微調整 ===
# ボタンが画面下部に固定されるため、チャットコンテナと重ならないように下に余白を作る
st.markdown('<div style="height: 180px;"></div>', unsafe_allow_html=True)
