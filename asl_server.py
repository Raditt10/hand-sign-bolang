from flask import Flask, Response, jsonify, request
from flask_cors import CORS
import threading
import time
import cv2
import os

# Import detection helpers from asl.py
import asl

app = Flask(__name__)
CORS(app)

capture_thread = None
capture_running = False
capture_lock = threading.Lock()
latest_frame = None
latest_label = "-"

def capture_loop():
    global capture_running, latest_frame, latest_label
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[asl_server] Error: Cannot open camera")
        capture_running = False
        return

    while capture_running:
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.01)
            continue

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = asl.hands.process(rgb)

        text = "-"
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                asl.mp_draw.draw_landmarks(frame, hand_landmarks, asl.mp_hands.HAND_CONNECTIONS)
                fingers = asl.get_finger_states(hand_landmarks)
                text = asl.classify_letter(fingers)

                # draw finger status
                finger_names = ["Jempol", "Telunjuk", "Tengah", "Manis", "Kelingking"]
                for i, (name, state) in enumerate(zip(finger_names, fingers)):
                    color = (0, 255, 0) if state == 1 else (0, 0, 255)
                    cv2.putText(frame, f"{name}: {'Terbuka' if state == 1 else 'Tertutup'}",
                               (20, 150 + i*30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        # overlay label
        if text != "-":
            cv2.putText(frame, f"Terdeteksi: {text}", (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 3)
        else:
            cv2.putText(frame, "Gesture tidak dikenali", (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

        # update globals
        latest_label = text

        # encode to JPEG
        ret2, buffer = cv2.imencode('.jpg', frame)
        if not ret2:
            continue
        frame_bytes = buffer.tobytes()

        with capture_lock:
            latest_frame = frame_bytes

        # small sleep to avoid pegging CPU
        time.sleep(0.02)

    cap.release()
    print("[asl_server] capture loop exited")

@app.route('/start', methods=['POST', 'GET'])
def start_stream():
    global capture_thread, capture_running
    if capture_running:
        return jsonify({"status": "already_running"})
    capture_running = True
    capture_thread = threading.Thread(target=capture_loop, daemon=True)
    capture_thread.start()
    return jsonify({"status": "started"})

@app.route('/stop', methods=['POST', 'GET'])
def stop_stream():
    global capture_running, capture_thread
    if not capture_running:
        return jsonify({"status": "not_running"})
    capture_running = False
    # wait briefly for thread to stop
    if capture_thread is not None:
        capture_thread.join(timeout=2.0)
    return jsonify({"status": "stopped"})

@app.route('/video_feed')
def video_feed():
    def generate():
        while True:
            if not capture_running:
                time.sleep(0.1)
                continue
            with capture_lock:
                frame = latest_frame
            if frame is None:
                time.sleep(0.01)
                continue
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/label')
def label():
    global latest_label
    return jsonify({"label": latest_label})


@app.route('/health')
def health():
    return jsonify({"status": "ok"})

@app.route('/set_name', methods=['POST'])
def set_name():
    name = request.form.get('name') or request.args.get('name')
    if name:
        asl.user_name = name
        return jsonify({"status": "ok", "name": name})
    return jsonify({"status": "error", "reason": "missing name"}), 400

@app.route('/set_language', methods=['POST'])
def set_language():
    # Expect mode like 'indonesia','english','japanese', etc.
    mode = request.form.get('mode') or request.args.get('mode')
    if mode:
        asl.mode = mode
        return jsonify({"status": "ok", "mode": mode})
    return jsonify({"status": "error", "reason": "missing mode"}), 400

if __name__ == '__main__':
    # default mode
    asl.mode = 'english'
    app.run(host='0.0.0.0', port=5000, threaded=True)
