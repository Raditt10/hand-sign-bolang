<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="icon" href="assets/LOGO SMKN 13 BDG.JPG" type="image/jpg">
    <title>Sign Language with Auto Word Builder</title>
    <script src="https://cdn.jsdelivr.net/npm/@mediapipe/hands/hands.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/@mediapipe/camera_utils/camera_utils.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/@mediapipe/drawing_utils/drawing_utils.js"></script>
    </style>
</head>
<body>
    <div class="school-background">
        <div class="grid-pattern"></div>
    </div>

    <div class="header-bar">
        <div style="display:flex; align-items:center; gap:12px;">
            <img src="assets/LOGO SMKN 13 BDG.JPG" alt="LOGO SMKN 13 BDG" class="school-logo" onerror="this.style.display='none'">
            <div class="header-title">🤟 Sign Language Auto Word Builder</div>
        </div>
        <div class="header-info">
            <div class="info-badge" id="userDisplay">👤 User</div>
        </div>
    </div>

    <div class="container">
        <div class="video-container">
            <video id="videoElement" autoplay playsinline></video>
            <canvas id="canvasElement" class="canvas-overlay"></canvas>
            
            <!-- Word Predictor Box -->
            <div class="word-box">
                <div class="word-title">📝 Current Word</div>
                <div class="current-word-display" id="currentWordDisplay">[typing...]</div>
                
                <div class="word-title" style="margin-top:15px;">💡 Predictions</div>
                <div class="predictions-list" id="predictionsList">
                    <div style="color:#888;font-size:13px;text-align:center;padding:10px;">Start typing...</div>
                </div>
            </div>

            <!-- Detected Letter Box -->
            <div class="letter-display" id="letterDisplay">
                <div class="letter-label">DETECTED</div>
                <div class="letter-text" id="detectedLetter">-</div>
            </div>

            <!-- Sentence Box -->
            <div class="sentence-box">
                <div class="sentence-title">📖 Sentence</div>
                <div class="sentence-display" id="sentenceDisplay">[empty]</div>
            </div>
        </div>
    </div>

    <div class="footer-bar">
        <button class="control-btn" onclick="completeWord()">✅ Complete Word (Space)</button>
        <button class="control-btn" onclick="autoComplete()">⚡ Auto-Complete (Tab)</button>
        <button class="control-btn" onclick="deleteLetter()">⬅️ Delete Letter</button>
        <button class="control-btn" onclick="deleteWord()">🗑️ Delete Word</button>
        <button class="control-btn" onclick="speakSentence()">🔊 Speak (Enter)</button>
        <button class="control-btn" onclick="clearAll()">🆑 Clear All</button>
        <button class="control-btn" onclick="toggleCamera()">📸 Pause</button>
    </div>

    <!-- Modal Welcome -->
    <div id="welcomeModal" class="modal">
        <div class="modal-content">
            <h2 class="modal-title">🤟 Welcome to Auto Word Builder!</h2>
            <p class="modal-subtitle">Advanced Sign Language Recognition with Word Prediction & Sentence Builder</p>
            
            <div class="controls-info">
                <strong>🎮 Keyboard Controls:</strong>
                <div>• <strong>SPACE</strong>: Complete current word & add to sentence</div>
                <div>• <strong>TAB</strong>: Auto-complete with top prediction</div>
                <div>• <strong>1-5</strong>: Select specific prediction</div>
                <div>• <strong>BACKSPACE</strong>: Delete last letter</div>
                <div>• <strong>DELETE</strong>: Delete last word from sentence</div>
                <div>• <strong>ENTER</strong>: Speak complete sentence</div>
                <div>• <strong>C</strong>: Clear everything</div>
            </div>
            
            <input type="text" id="nameInput" class="name-input" placeholder="Enter your name..." value="Student">
            <button class="start-btn" onclick="startApp()">🚀 Start Learning</button>
        </div>
    </div>

    <script>
        // ========================================
        // 📚 Common Words Dictionary
        // ========================================
        const COMMON_WORDS = [
            "HELLO", "HI", "THANKS", "THANK", "YOU", "PLEASE", "SORRY", "YES", "NO",
            "HELP", "GOOD", "BAD", "MORNING", "AFTERNOON", "EVENING", "NIGHT",
            "BYE", "GOODBYE", "WELCOME", "FINE", "GREAT", "NICE", "MEET",
            "NAME", "MY", "YOUR", "IS", "ARE", "AM", "WHAT", "WHO", "WHERE",
            "WHEN", "WHY", "HOW", "CAN", "COULD", "WOULD", "SHOULD",
            "LOVE", "LIKE", "WANT", "NEED", "HAVE", "HAS", "DO", "DOES",
            "GO", "COME", "SEE", "LOOK", "HEAR", "SPEAK", "TALK", "SAY",
            "EAT", "DRINK", "SLEEP", "WORK", "PLAY", "STUDY", "LEARN",
            "HAPPY", "SAD", "ANGRY", "TIRED", "HUNGRY", "THIRSTY",
            "HOT", "COLD", "BIG", "SMALL", "FAST", "SLOW", "NEW", "OLD"
        ];

        // ========================================
        // 🧠 Word Predictor Class
        // ========================================
        class WordPredictor {
            constructor(dictionary) {
                this.dictionary = dictionary.sort();
                this.currentWord = [];
                this.predictedWords = [];
            }

            addLetter(letter) {
                if (/[A-Z]/.test(letter)) {
                    this.currentWord.push(letter.toUpperCase());
                    this.updatePredictions();
                }
            }

            removeLetter() {
                if (this.currentWord.length > 0) {
                    this.currentWord.pop();
                    this.updatePredictions();
                }
            }

            updatePredictions() {
                const current = this.currentWord.join('');
                if (!current) {
                    this.predictedWords = [];
                    return;
                }

                // Find words that start with current letters
                let matches = this.dictionary.filter(word => word.startsWith(current));

                // If no exact matches, find similar words
                if (matches.length === 0 && current.length > 2) {
                    matches = this.findSimilarWords(current);
                }

                this.predictedWords = matches.slice(0, 5);
            }

            findSimilarWords(target) {
                return this.dictionary
                    .map(word => ({
                        word: word,
                        similarity: this.calculateSimilarity(target, word)
                    }))
                    .filter(item => item.similarity > 0.6)
                    .sort((a, b) => b.similarity - a.similarity)
                    .map(item => item.word)
                    .slice(0, 5);
            }

            calculateSimilarity(s1, s2) {
                const longer = s1.length > s2.length ? s1 : s2;
                const shorter = s1.length > s2.length ? s2 : s1;
                if (longer.length === 0) return 1.0;
                return (longer.length - this.editDistance(longer, shorter)) / longer.length;
            }

            editDistance(s1, s2) {
                const costs = [];
                for (let i = 0; i <= s1.length; i++) {
                    let lastValue = i;
                    for (let j = 0; j <= s2.length; j++) {
                        if (i === 0) {
                            costs[j] = j;
                        } else if (j > 0) {
                            let newValue = costs[j - 1];
                            if (s1.charAt(i - 1) !== s2.charAt(j - 1)) {
                                newValue = Math.min(Math.min(newValue, lastValue), costs[j]) + 1;
                            }
                            costs[j - 1] = lastValue;
                            lastValue = newValue;
                        }
                    }
                    if (i > 0) costs[s2.length] = lastValue;
                }
                return costs[s2.length];
            }

            getCurrentWord() {
                return this.currentWord.join('');
            }

            getPredictions() {
                return this.predictedWords;
            }

            completeWord(word = null) {
                if (word) {
                    this.currentWord = word.split('');
                } else if (this.predictedWords.length > 0) {
                    this.currentWord = this.predictedWords[0].split('');
                }
                this.updatePredictions();
                return this.getCurrentWord();
            }

            clear() {
                this.currentWord = [];
                this.predictedWords = [];
            }
        }

        // ========================================
        // 📝 Sentence Builder Class
        // ========================================
        class SentenceBuilder {
            constructor() {
                this.words = [];
                this.currentSentence = "";
            }

            addWord(word) {
                if (word.trim()) {
                    this.words.push(word.toUpperCase());
                    this.buildSentence();
                }
            }

            buildSentence() {
                if (this.words.length === 0) {
                    this.currentSentence = "";
                    return;
                }

                let sentence = this.words.join(' ');
                sentence = sentence.charAt(0) + sentence.slice(1).toLowerCase();

                const lastWord = this.words[this.words.length - 1].toUpperCase();
                const questionWords = ["WHAT", "WHO", "WHERE", "WHEN", "WHY", "HOW", "CAN", "COULD", "WOULD", "SHOULD"];
                
                if (questionWords.includes(this.words[0].toUpperCase())) {
                    if (!sentence.endsWith('?')) sentence += '?';
                } else if (["HELLO", "HI", "BYE", "GOODBYE", "THANKS", "SORRY"].includes(lastWord)) {
                    if (!sentence.endsWith('!')) sentence += '!';
                } else {
                    if (!sentence.endsWith('.')) sentence += '.';
                }

                this.currentSentence = sentence;
            }

            getSentence() {
                return this.currentSentence;
            }

            removeLastWord() {
                if (this.words.length > 0) {
                    this.words.pop();
                    this.buildSentence();
                }
            }

            clear() {
                this.words = [];
                this.currentSentence = "";
            }
        }

        // ========================================
        // 🎯 Global Variables
        // ========================================
        let userName = 'Student';
        let hands;
        let camera;
        let lastLetter = '';
        let lastDetectedLetter = '';
        let letterConfirmTime = 0;
        let letterConfirmDuration = 1500;
        let lastSpeakTime = 0;
        let isPaused = false;

        const wordPredictor = new WordPredictor(COMMON_WORDS);
        const sentenceBuilder = new SentenceBuilder();

        // ========================================
        // 🚀 Initialization
        // ========================================
        window.onload = function() {
            document.getElementById('welcomeModal').style.display = 'block';
            setupKeyboardControls();
        };

        function startApp() {
            userName = document.getElementById('nameInput').value || 'Student';
            document.getElementById('welcomeModal').style.display = 'none';
            document.getElementById('userDisplay').textContent = `👤 ${userName}`;
            initializeCamera();
        }

        // ========================================
        // ⌨️ Keyboard Controls
        // ========================================
        function setupKeyboardControls() {
            document.addEventListener('keydown', (e) => {
                switch(e.key) {
                    case ' ':
                        e.preventDefault();
                        completeWord();
                        break;
                    case 'Tab':
                        e.preventDefault();
                        autoComplete();
                        break;
                    case 'Backspace':
                        e.preventDefault();
                        deleteLetter();
                        break;
                    case 'Delete':
                        e.preventDefault();
                        deleteWord();
                        break;
                    case 'Enter':
                        e.preventDefault();
                        speakSentence();
                        break;
                    case 'c':
                    case 'C':
                        clearAll();
                        break;
                    case '1':
                    case '2':
                    case '3':
                    case '4':
                    case '5':
                        selectPrediction(parseInt(e.key) - 1);
                        break;
                }
            });
        }

        // ========================================
        // 🎬 Control Functions
        // ========================================
        function completeWord() {
            const word = wordPredictor.getCurrentWord();
            if (word) {
                sentenceBuilder.addWord(word);
                console.log(`✅ Word added: ${word}`);
                speakText(word);
                wordPredictor.clear();
                updateUI();
            }
        }

        function autoComplete() {
            if (wordPredictor.getPredictions().length > 0) {
                const completed = wordPredictor.completeWord();
                console.log(`🎯 Auto-completed: ${completed}`);
                updateUI();
            }
        }

        function deleteLetter() {
            wordPredictor.removeLetter();
            console.log('🗑️ Letter deleted');
            updateUI();
        }

        function deleteWord() {
            sentenceBuilder.removeLastWord();
            console.log('🗑️ Word deleted');
            updateUI();
        }

        function speakSentence() {
            const sentence = sentenceBuilder.getSentence();
            if (sentence) {
                console.log(`📢 Speaking: ${sentence}`);
                speakText(sentence);
                saveSentence(sentence);
            }
        }

        function clearAll() {
            wordPredictor.clear();
            sentenceBuilder.clear();
            console.log('🗑️ All cleared');
            updateUI();
        }

        function toggleCamera() {
            isPaused = !isPaused;
        }

        function selectPrediction(index) {
            const predictions = wordPredictor.getPredictions();
            if (index >= 0 && index < predictions.length) {
                const selected = predictions[index];
                wordPredictor.completeWord(selected);
                console.log(`✨ Prediction selected: ${selected}`);
                updateUI();
            }
        }

        // ========================================
        // 🗣️ Text-to-Speech
        // ========================================
        function speakText(text) {
            if (text !== lastLetter && text !== '-') {
                const now = Date.now();
                if (now - lastSpeakTime > 1500) {
                    const utterance = new SpeechSynthesisUtterance(text);
                    utterance.lang = 'en-US';
                    utterance.rate = 0.9;
                    speechSynthesis.speak(utterance);
                    lastSpeakTime = now;
                    lastLetter = text;
                }
            }
        }

        // ========================================
        // 💾 Save Sentence
        // ========================================
        function saveSentence(sentence) {
            const timestamp = new Date().toLocaleString();
            const entry = `${timestamp} - ${userName}: ${sentence}\n`;
            
            // Try to download as text file
            try {
                const blob = new Blob([entry], { type: 'text/plain' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'sentences.txt';
                a.click();
                URL.revokeObjectURL(url);
                console.log('💾 Sentence saved');
            } catch (e) {
                console.log('💾 Sentence:', entry);
            }
        }

      // ========================================
        // 🎨 UI Update
        // ========================================
        function updateUI() {
            // Update current word
            const currentWord = wordPredictor.getCurrentWord();
            document.getElementById('currentWordDisplay').textContent = currentWord || '[typing...]';

            // Update predictions
            const predictions = wordPredictor.getPredictions();
            const predList = document.getElementById('predictionsList');
            
            if (predictions.length > 0) {
                predList.innerHTML = predictions.map((pred, i) => 
                    `<div class="prediction-item ${i === 0 ? 'top' : ''}" onclick="selectPrediction(${i})">${i + 1}. ${pred}</div>`
                ).join('');
            } else {
                predList.innerHTML = '<div style="color:#888;font-size:13px;text-align:center;padding:10px;">Start typing...</div>';
            }

            // Update sentence
            document.getElementById('sentenceDisplay').textContent = sentenceBuilder.getSentence() || '[empty]';
        }

        // ========================================
        // 📷 Camera Initialization
        // ========================================
        function initializeCamera() {
            const videoElement = document.getElementById('videoElement');
            const canvasElement = document.getElementById('canvasElement');
            const canvasCtx = canvasElement.getContext('2d');

            hands = new Hands({
                locateFile: (file) => {
                    return `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}`;
                }
            });

            hands.setOptions({
                maxNumHands: 2,
                modelComplexity: 1,
                minDetectionConfidence: 0.5,
                minTrackingConfidence: 0.5
            });

            hands.onResults(onResults);

            camera = new Camera(videoElement, {
                onFrame: async () => {
                    if (!isPaused) {
                        await hands.send({ image: videoElement });
                    }
                },
                width: 1280,
                height: 720
            });
            
            camera.start();
            console.log('📷 Camera initialized');
        }

        // ========================================
        // 🤖 Hand Detection Results
        // ========================================
        function onResults(results) {
            const videoElement = document.getElementById('videoElement');
            const canvasElement = document.getElementById('canvasElement');
            const canvasCtx = canvasElement.getContext('2d');

            canvasElement.width = videoElement.videoWidth;
            canvasElement.height = videoElement.videoHeight;

            canvasCtx.save();
            canvasCtx.clearRect(0, 0, canvasElement.width, canvasElement.height);

            if (results.multiHandLandmarks && results.multiHandLandmarks.length > 0) {
                for (const landmarks of results.multiHandLandmarks) {
                    drawConnectors(canvasCtx, landmarks, HAND_CONNECTIONS, {
                        color: '#00ff88',
                        lineWidth: 3
                    });
                    drawLandmarks(canvasCtx, landmarks, {
                        color: '#ff4444',
                        lineWidth: 1,
                        radius: 3
                    });
                }

                const letter = recognizeLetter(results.multiHandLandmarks[0]);
                updateLetterDisplay(letter);
            } else {
                updateLetterDisplay('-');
            }

            canvasCtx.restore();
        }

        // ========================================
        // 🔤 Letter Recognition
        // ========================================
        function recognizeLetter(landmarks) {
            if (!landmarks || landmarks.length < 21) return '-';

            const fingers = {
                thumb: isFingerExtended(landmarks, 4, 3, 2),
                index: isFingerExtended(landmarks, 8, 7, 6),
                middle: isFingerExtended(landmarks, 12, 11, 10),
                ring: isFingerExtended(landmarks, 16, 15, 14),
                pinky: isFingerExtended(landmarks, 20, 19, 18)
            };

            const extendedCount = Object.values(fingers).filter(x => x).length;

            // A - Fist with thumb on side
            if (!fingers.thumb && !fingers.index && !fingers.middle && !fingers.ring && !fingers.pinky) {
                return 'A';
            }

            // B - All fingers extended except thumb
            if (!fingers.thumb && fingers.index && fingers.middle && fingers.ring && fingers.pinky) {
                return 'B';
            }

            // C - Curved hand
            if (isCurvedHand(landmarks)) {
                return 'C';
            }

            // D - Index up, thumb touching middle
            if (!fingers.thumb && fingers.index && !fingers.middle && !fingers.ring && !fingers.pinky) {
                return 'D';
            }

            // E - All fingers curled
            if (allFingersCurled(landmarks)) {
                return 'E';
            }

            // F - Three fingers up, thumb and index forming circle
            if (fingers.middle && fingers.ring && fingers.pinky && !fingers.index) {
                return 'F';
            }

            // I - Pinky extended only
            if (!fingers.thumb && !fingers.index && !fingers.middle && !fingers.ring && fingers.pinky) {
                return 'I';
            }

            // L - Thumb and index forming L shape
            if (fingers.thumb && fingers.index && !fingers.middle && !fingers.ring && !fingers.pinky) {
                const angle = getAngleBetweenFingers(landmarks, 4, 8);
                if (angle > 70 && angle < 110) return 'L';
            }

            // O - All fingers forming circle
            if (isCircleShape(landmarks)) {
                return 'O';
            }

            // U - Index and middle up, close together
            if (!fingers.thumb && fingers.index && fingers.middle && !fingers.ring && !fingers.pinky) {
                return 'U';
            }

            // V - Index and middle up, spread apart
            if (!fingers.thumb && fingers.index && fingers.middle && !fingers.ring && !fingers.pinky) {
                const spread = getFingerSpread(landmarks, 8, 12);
                if (spread > 0.1) return 'V';
                return 'U';
            }

            // W - Three fingers up
            if (!fingers.thumb && fingers.index && fingers.middle && fingers.ring && !fingers.pinky) {
                return 'W';
            }

            // Y - Thumb and pinky extended
            if (fingers.thumb && !fingers.index && !fingers.middle && !fingers.ring && fingers.pinky) {
                return 'Y';
            }

            // Five fingers extended
            if (extendedCount === 5) {
                return '5';
            }

            return '-';
        }

        // ========================================
        // 🧮 Helper Functions for Recognition
        // ========================================
        function isFingerExtended(landmarks, tip, pip, mcp) {
            const tipY = landmarks[tip].y;
            const pipY = landmarks[pip].y;
            const mcpY = landmarks[mcp].y;
            return tipY < pipY && pipY < mcpY;
        }

        function isCurvedHand(landmarks) {
            const wrist = landmarks[0];
            const fingertips = [4, 8, 12, 16, 20];
            let avgDistance = 0;
            
            fingertips.forEach(tip => {
                const dist = Math.sqrt(
                    Math.pow(landmarks[tip].x - wrist.x, 2) +
                    Math.pow(landmarks[tip].y - wrist.y, 2)
                );
                avgDistance += dist;
            });
            
            avgDistance /= fingertips.length;
            return avgDistance > 0.15 && avgDistance < 0.25;
        }

        function allFingersCurled(landmarks) {
            const wrist = landmarks[0];
            const fingertips = [8, 12, 16, 20];
            
            for (let tip of fingertips) {
                const dist = Math.sqrt(
                    Math.pow(landmarks[tip].x - wrist.x, 2) +
                    Math.pow(landmarks[tip].y - wrist.y, 2)
                );
                if (dist > 0.15) return false;
            }
            return true;
        }

        function isCircleShape(landmarks) {
            const thumb = landmarks[4];
            const index = landmarks[8];
            const dist = Math.sqrt(
                Math.pow(thumb.x - index.x, 2) +
                Math.pow(thumb.y - index.y, 2)
            );
            return dist < 0.05;
        }

        function getAngleBetweenFingers(landmarks, finger1, finger2) {
            const wrist = landmarks[0];
            const f1 = landmarks[finger1];
            const f2 = landmarks[finger2];
            
            const angle1 = Math.atan2(f1.y - wrist.y, f1.x - wrist.x);
            const angle2 = Math.atan2(f2.y - wrist.y, f2.x - wrist.x);
            
            return Math.abs(angle1 - angle2) * (180 / Math.PI);
        }

        function getFingerSpread(landmarks, finger1, finger2) {
            return Math.sqrt(
                Math.pow(landmarks[finger1].x - landmarks[finger2].x, 2) +
                Math.pow(landmarks[finger1].y - landmarks[finger2].y, 2)
            );
        }

        // ========================================
        // 🎯 Letter Display Update
        // ========================================
        function updateLetterDisplay(letter) {
            const display = document.getElementById('letterDisplay');
            const letterText = document.getElementById('detectedLetter');

            if (letter === '-') {
                display.classList.add('no-detect');
                letterText.textContent = '-';
                lastDetectedLetter = '';
                letterConfirmTime = 0;
                return;
            }

            display.classList.remove('no-detect');
            letterText.textContent = letter;

            // Confirm letter after holding for duration
            if (letter === lastDetectedLetter) {
                const now = Date.now();
                if (now - letterConfirmTime >= letterConfirmDuration) {
                    wordPredictor.addLetter(letter);
                    console.log(`✅ Letter confirmed: ${letter}`);
                    updateUI();
                    letterConfirmTime = now + 500; // Cooldown
                }
            } else {
                lastDetectedLetter = letter;
                letterConfirmTime = Date.now();
            }
        }
    </script>
</body>
</html>
