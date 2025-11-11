<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🤟 Pengenalan Bahasa Isyarat Multi-Bahasa</title>
    <script src="https://cdn.jsdelivr.net/npm/@mediapipe/hands/hands.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/@mediapipe/camera_utils/camera_utils.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/@mediapipe/drawing_utils/drawing_utils.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            overflow: hidden;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }

        .school-background {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(135deg, #2c5aa0 0%, #1e8c93 50%, #20b2aa 100%);
            z-index: 0;
        }

        .grid-pattern {
            position: absolute;
            width: 100%;
            height: 100%;
            background-image: 
                repeating-linear-gradient(0deg, rgba(255,255,255,0.03) 0px, transparent 1px, transparent 40px),
                repeating-linear-gradient(90deg, rgba(255,255,255,0.03) 0px, transparent 1px, transparent 40px);
        }

        .header-bar {
            position: fixed;
            top: 0;
            width: 100%;
            height: 80px;
            background: linear-gradient(135deg, #ff9d4d 0%, #ffb347 100%);
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 30px;
            z-index: 100;
            border-bottom: 4px solid #ff8c00;
        }

        .header-title {
            font-size: 28px;
            font-weight: bold;
            color: white;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }

        .header-info {
            display: flex;
            gap: 20px;
            align-items: center;
        }

        .info-badge {
            background: rgba(255,255,255,0.9);
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: bold;
            color: #2c5aa0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        }

        .footer-bar {
            position: fixed;
            bottom: 0;
            width: 100%;
            height: 60px;
            background: linear-gradient(135deg, #32b4ff 0%, #4d9fff 100%);
            box-shadow: 0 -4px 15px rgba(0,0,0,0.3);
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 30px;
            z-index: 100;
            border-top: 4px solid #1e90ff;
        }

        .control-btn {
            background: rgba(255,255,255,0.9);
            border: none;
            padding: 10px 25px;
            border-radius: 25px;
            font-weight: bold;
            color: #2c5aa0;
            cursor: pointer;
            transition: all 0.3s;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
            font-size: 14px;
        }

        .control-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            background: white;
        }

        .container {
            position: relative;
            z-index: 10;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            padding: 100px 20px 80px;
        }

        .video-container {
            position: relative;
            border-radius: 20px;
            overflow: hidden;
            box-shadow: 0 10px 40px rgba(0,0,0,0.4);
            border: 5px solid rgba(255,255,255,0.3);
        }

        #videoElement {
            display: block;
            width: 100%;
            max-width: 960px;
            height: auto;
            transform: scaleX(-1);
        }

        .canvas-overlay {
            position: absolute;
            top: 0;
            left: 0;
            transform: scaleX(-1);
        }

        .detection-panel {
            position: absolute;
            top: 20px;
            left: 20px;
            right: 20px;
            background: rgba(0,0,0,0.75);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 20px;
            color: white;
            box-shadow: 0 4px 20px rgba(0,0,0,0.5);
            border: 2px solid rgba(255,255,255,0.2);
        }

        .detected-text {
            font-size: 32px;
            font-weight: bold;
            text-align: center;
            margin-bottom: 15px;
            color: #00ff88;
            text-shadow: 0 0 10px rgba(0,255,136,0.5);
            min-height: 40px;
        }

        .finger-status {
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 10px;
            margin-top: 15px;
        }

        .finger-item {
            text-align: center;
            padding: 10px;
            background: rgba(255,255,255,0.1);
            border-radius: 10px;
            border: 2px solid rgba(255,255,255,0.2);
            transition: all 0.3s;
        }

        .finger-item.open {
            background: rgba(0,255,136,0.3);
            border-color: #00ff88;
            box-shadow: 0 0 15px rgba(0,255,136,0.3);
        }

        .finger-item.closed {
            background: rgba(255,68,68,0.3);
            border-color: #ff4444;
        }

        .finger-name {
            font-size: 12px;
            font-weight: bold;
            margin-bottom: 5px;
        }

        .finger-status-text {
            font-size: 11px;
        }

        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.8);
            backdrop-filter: blur(5px);
        }

        .modal-content {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin: 10% auto;
            padding: 40px;
            border-radius: 20px;
            width: 90%;
            max-width: 600px;
            box-shadow: 0 10px 50px rgba(0,0,0,0.5);
            border: 3px solid rgba(255,255,255,0.3);
        }

        .modal-title {
            text-align: center;
            color: white;
            font-size: 28px;
            margin-bottom: 30px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }

        .language-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 15px;
            margin-bottom: 30px;
        }

        .lang-btn {
            background: rgba(255,255,255,0.9);
            border: none;
            padding: 15px;
            border-radius: 15px;
            cursor: pointer;
            transition: all 0.3s;
            font-weight: bold;
            color: #2c5aa0;
            box-shadow: 0 4px 10px rgba(0,0,0,0.2);
        }

        .lang-btn:hover {
            transform: scale(1.05);
            background: white;
            box-shadow: 0 6px 15px rgba(0,0,0,0.3);
        }

        .name-input {
            width: 100%;
            padding: 15px;
            border-radius: 10px;
            border: 2px solid rgba(255,255,255,0.3);
            font-size: 16px;
            margin-bottom: 20px;
            background: rgba(255,255,255,0.9);
        }

        .start-btn {
            width: 100%;
            padding: 15px;
            background: linear-gradient(135deg, #00ff88 0%, #00cc6a 100%);
            border: none;
            border-radius: 10px;
            color: white;
            font-size: 18px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s;
            box-shadow: 0 4px 15px rgba(0,255,136,0.3);
        }

        .start-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0,255,136,0.4);
        }

        @media (max-width: 768px) {
            .language-grid {
                grid-template-columns: repeat(2, 1fr);
            }
            
            .header-title {
                font-size: 18px;
            }
            
            .finger-status {
                grid-template-columns: repeat(3, 1fr);
            }
        }
    </style>
</head>
<body>
    <div class="school-background">
        <div class="grid-pattern"></div>
    </div>

    <div class="header-bar">
        <div class="header-title">🤟 Pengenalan Bahasa Isyarat Multi-Bahasa</div>
        <div class="header-info">
            <div class="info-badge" id="languageDisplay">🇮🇩 Indonesia</div>
            <div class="info-badge" id="userDisplay">👤 User</div>
        </div>
    </div>

    <div class="container">
        <div class="video-container">
            <video id="videoElement" autoplay playsinline></video>
            <canvas id="canvasElement" class="canvas-overlay"></canvas>
            
            <div class="detection-panel">
                <div class="detected-text" id="detectedText">Tunjukkan gesture tangan...</div>
                <div class="finger-status" id="fingerStatus"></div>
            </div>
        </div>
    </div>

    <div class="footer-bar">
        <button class="control-btn" onclick="changeLanguage()">🌍 Ganti Bahasa</button>
        <button class="control-btn" onclick="toggleCamera()">📸 Pause/Resume</button>
        <button class="control-btn" onclick="resetApp()">🔄 Reset</button>
    </div>

    <!-- Modal Pilih Bahasa -->
    <div id="languageModal" class="modal">
        <div class="modal-content">
            <h2 class="modal-title">🌍 Pilih Bahasa & Nama</h2>
            <div class="language-grid">
                <button class="lang-btn" onclick="selectLanguage('id', 'Indonesia', '🇮🇩')">🇮🇩 Indonesia</button>
                <button class="lang-btn" onclick="selectLanguage('en', 'English', '🇺🇸')">🇺🇸 English</button>
                <button class="lang-btn" onclick="selectLanguage('ja', 'Japanese', '🇯🇵')">🇯🇵 Japanese</button>
                <button class="lang-btn" onclick="selectLanguage('es', 'Spanish', '🇪🇸')">🇪🇸 Spanish</button>
                <button class="lang-btn" onclick="selectLanguage('jw', 'Javanese', '🏴')">🏴 Javanese</button>
                <button class="lang-btn" onclick="selectLanguage('su', 'Sundanese', '🏴')">🏴 Sundanese</button>
                <button class="lang-btn" onclick="selectLanguage('it', 'Italian', '🇮🇹')">🇮🇹 Italian</button>
                <button class="lang-btn" onclick="selectLanguage('zh-CN', 'Chinese', '🇨🇳')">🇨🇳 Chinese</button>
                <button class="lang-btn" onclick="selectLanguage('th', 'Thai', '🇹🇭')">🇹🇭 Thai</button>
                <button class="lang-btn" onclick="selectLanguage('ar', 'Arabic', '🇸🇦')">🇸🇦 Arabic</button>
                <button class="lang-btn" onclick="selectLanguage('ko', 'Korean', '🇰🇷')">🇰🇷 Korean</button>
                <button class="lang-btn" onclick="selectLanguage('hi', 'Hindi', '🇮🇳')">🇮🇳 Hindi</button>
            </div>
            <input type="text" id="nameInput" class="name-input" placeholder="Masukkan nama Anda..." value="Teman Hebat">
            <button class="start-btn" onclick="startApp()">🚀 Mulai Aplikasi</button>
        </div>
    </div>

    <script>
        let currentLanguage = 'id';
        let currentMode = 'indonesia';
        let currentFlag = '🇮🇩';
        let userName = 'Teman Hebat';
        let hands;
        let camera;
        let lastText = '';
        let lastSpeakTime = 0;
        let isPaused = false;

        const fingerNames = ['Jempol', 'Telunjuk', 'Tengah', 'Manis', 'Kelingking'];

        // Tampilkan modal saat load
        window.onload = function() {
            document.getElementById('languageModal').style.display = 'block';
        };

        function selectLanguage(lang, mode, flag) {
            currentLanguage = lang;
            currentMode = mode.toLowerCase();
            currentFlag = flag;
            document.querySelectorAll('.lang-btn').forEach(btn => {
                btn.style.background = 'rgba(255,255,255,0.9)';
            });
            event.target.style.background = 'linear-gradient(135deg, #00ff88 0%, #00cc6a 100%)';
            event.target.style.color = 'white';
        }

        function startApp() {
            userName = document.getElementById('nameInput').value || 'Teman Hebat';
            document.getElementById('languageModal').style.display = 'none';
            document.getElementById('languageDisplay').textContent = `${currentFlag} ${currentMode.charAt(0).toUpperCase() + currentMode.slice(1)}`;
            document.getElementById('userDisplay').textContent = `👤 ${userName}`;
            initializeCamera();
        }

        function changeLanguage() {
            document.getElementById('languageModal').style.display = 'block';
        }

        function toggleCamera() {
            isPaused = !isPaused;
        }

        function resetApp() {
            location.reload();
        }

        async function initializeCamera() {
            const videoElement = document.getElementById('videoElement');
            const canvasElement = document.getElementById('canvasElement');
            const canvasCtx = canvasElement.getContext('2d');

            hands = new Hands({
                locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}`
            });

            hands.setOptions({
                maxNumHands: 1,
                modelComplexity: 1,
                minDetectionConfidence: 0.7,
                minTrackingConfidence: 0.5
            });

            hands.onResults(onResults);

            camera = new Camera(videoElement, {
                onFrame: async () => {
                    if (!isPaused) {
                        await hands.send({image: videoElement});
                    }
                },
                width: 960,
                height: 540
            });

            camera.start();

            function onResults(results) {
                canvasElement.width = videoElement.videoWidth;
                canvasElement.height = videoElement.videoHeight;

                canvasCtx.save();
                canvasCtx.clearRect(0, 0, canvasElement.width, canvasElement.height);

                if (results.multiHandLandmarks) {
                    for (const landmarks of results.multiHandLandmarks) {
                        drawConnectors(canvasCtx, landmarks, HAND_CONNECTIONS, {color: '#00FF88', lineWidth: 4});
                        drawLandmarks(canvasCtx, landmarks, {color: '#FF4444', lineWidth: 2, radius: 5});

                        const fingers = getFingerStates(landmarks);
                        const text = classifyGesture(fingers);
                        
                        displayFingerStatus(fingers);
                        displayDetectedText(text);
                        speakText(text);
                    }
                } else {
                    document.getElementById('detectedText').textContent = 'Tunjukkan gesture tangan...';
                    document.getElementById('fingerStatus').innerHTML = '';
                }

                canvasCtx.restore();
            }
        }

        function getFingerStates(landmarks) {
            const fingers = [];
            
            // Thumb
            if (landmarks[4].x < landmarks[3].x) {
                fingers.push(1);
            } else {
                fingers.push(0);
            }
            
            // Other fingers
            [8, 12, 16, 20].forEach(tip => {
                if (landmarks[tip].y < landmarks[tip - 2].y) {
                    fingers.push(1);
                } else {
                    fingers.push(0);
                }
            });
            
            return fingers;
        }

        function displayFingerStatus(fingers) {
            const container = document.getElementById('fingerStatus');
            container.innerHTML = '';
            
            fingers.forEach((state, index) => {
                const div = document.createElement('div');
                div.className = `finger-item ${state === 1 ? 'open' : 'closed'}`;
                div.innerHTML = `
                    <div class="finger-name">${fingerNames[index]}</div>
                    <div class="finger-status-text">${state === 1 ? '✋ Terbuka' : '✊ Tertutup'}</div>
                `;
                container.appendChild(div);
            });
        }

        function displayDetectedText(text) {
            const textElement = document.getElementById('detectedText');
            if (text !== '-') {
                textElement.textContent = `✨ ${text}`;
                textElement.style.color = '#00ff88';
            } else {
                textElement.textContent = '❌ Gesture tidak dikenali';
                textElement.style.color = '#ff4444';
            }
        }

        function speakText(text) {
            if (text !== lastText && text !== '-') {
                const now = Date.now();
                if (now - lastSpeakTime > 3000) {
                    const utterance = new SpeechSynthesisUtterance(text);
                    utterance.lang = currentLanguage;
                    utterance.rate = 0.9;
                    speechSynthesis.speak(utterance);
                    lastSpeakTime = now;
                    lastText = text;
                }
            }
        }

        function classifyGesture(fingers) {
            const patterns = getLanguagePatterns();
            const key = fingers.join(',');
            return patterns[key] || '-';
        }

        function getLanguagePatterns() {
            const patterns = {
                'indonesia': {
                    '1,0,0,0,1': `Nama saya ${userName}`,
                    '1,1,1,1,1': 'Halo',
                    '1,1,1,0,0': 'Saya',
                    '0,1,0,1,0': 'Apa kabar',
                    '0,0,1,1,1': 'Terima kasih',
                    '1,1,0,0,1': 'Sampai jumpa',
                    '1,0,1,1,0': 'Selamat pagi',
                    '0,1,1,0,1': 'Selamat malam',
                    '1,0,1,0,0': 'Aku senang bertemu kamu',
                    '0,1,1,1,0': 'Semangat terus!',
                    '0,0,0,0,1': 'Tolong',
                    '1,0,0,0,0': 'Ya',
                    '0,1,0,0,0': 'Tidak',
                    '0,0,1,0,0': 'Maaf',
                    '0,0,0,1,0': 'Saya lapar'
                },
                'english': {
                    '1,0,0,0,1': `My name is ${userName}`,
                    '1,1,1,1,1': 'Hello',
                    '1,1,1,0,0': 'I am',
                    '0,1,0,1,0': 'How are you',
                    '0,0,1,1,1': 'Thank you',
                    '1,1,0,0,1': 'Goodbye',
                    '1,0,1,1,0': 'Good morning',
                    '0,1,1,0,1': 'Good night',
                    '1,0,1,0,0': 'Nice to meet you',
                    '0,1,1,1,0': 'Keep going!',
                    '0,0,0,0,1': 'Help',
                    '1,0,0,0,0': 'Yes',
                    '0,1,0,0,0': 'No',
                    '0,0,1,0,0': 'Sorry',
                    '0,0,0,1,0': 'I am hungry'
                },
                'japanese': {
                    '1,0,0,0,1': `わたしのなまえは ${userName} です`,
                    '1,1,1,1,1': 'こんにちは',
                    '1,1,1,0,0': 'わたし',
                    '0,1,0,1,0': 'おげんきですか',
                    '0,0,1,1,1': 'ありがとう',
                    '1,1,0,0,1': 'さようなら',
                    '1,0,1,1,0': 'おはよう',
                    '0,1,1,0,1': 'おやすみ',
                    '1,0,1,0,0': 'はじめまして',
                    '0,1,1,1,0': 'がんばって',
                    '0,0,0,0,1': 'たすけて',
                    '1,0,0,0,0': 'はい',
                    '0,1,0,0,0': 'いいえ',
                    '0,0,1,0,0': 'ごめんなさい',
                    '0,0,0,1,0': 'おなかがすきました'
                },
                'spanish': {
                    '1,0,0,0,1': `Mi nombre es ${userName}`,
                    '1,1,1,1,1': 'Hola',
                    '1,1,1,0,0': 'Yo soy',
                    '0,1,0,1,0': 'Cómo estás',
                    '0,0,1,1,1': 'Gracias',
                    '1,1,0,0,1': 'Adiós',
                    '1,0,1,1,0': 'Buenos días',
                    '0,1,1,0,1': 'Buenas noches',
                    '1,0,1,0,0': 'Encantado de conocerte',
                    '0,1,1,1,0': 'Sigue adelante',
                    '0,0,0,0,1': 'Ayuda',
                    '1,0,0,0,0': 'Sí',
                    '0,1,0,0,0': 'No',
                    '0,0,1,0,0': 'Lo siento',
                    '0,0,0,1,0': 'Tengo hambre'
                }
            };
            
            return patterns[currentMode] || patterns['indonesia'];
        }
    </script>
</body>
</html>