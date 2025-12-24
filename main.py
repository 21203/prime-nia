import os
import threading
import time
import schedule
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from voice_io import VoiceIO
from telegram_bridge import send_telegram_message, handle_telegram_command
from notifications import morning_briefing

load_dotenv()
LAPTOP_IP = os.getenv("LAPTOP_IP", "127.0.0.1")

# === Webhook Server ===
app = Flask(__name__)

@app.route('/alert', methods=['POST'])
def phone_alert():
    try:
        data = request.get_json()
        if data.get("type") == "battery":
            level = data.get("level", "??")
            msg = f"🔋 Phone battery: {level}%"
            if int(level) < 20:
                msg += " — please charge soon!"
            send_telegram_message(msg)
            return jsonify({"status": "ok"}), 200
        elif data.get("type") == "power":
            state = "🔌 Plugged in" if data.get("connected") else "⚡ Unplugged"
            send_telegram_message(state)
            return jsonify({"status": "ok"}), 200
    except Exception as e:
        print("Alert error:", e)
    return jsonify({"status": "ignored"}), 200

# Background services
threading.Thread(target=lambda: app.run(host="0.0.0.0", port=5000), daemon=True).start()
threading.Thread(target=lambda: [schedule.every().day.at("08:00").do(morning_briefing), 
                                (lambda: [schedule.run_pending(), time.sleep(30)] while True)], daemon=True).start()

# === Main Loop ===
if __name__ == "__main__":
    send_telegram_message(f"🟢 Nia is online!\n🌐 Webhook: http://{LAPTOP_IP}:5000/alert")
    nia = VoiceIO(wake_word=True, offline=True)
    nia.speak("Nia is awake. Say 'Hey Nia', 'Nia', 'Hello', or 'Can you help me'.")

    while True:
        try:
            command = nia.listen()
            if command:
                print(f"[Voice] Command: {command}")
                handle_telegram_command(command)
        except KeyboardInterrupt:
            nia.speak("Goodbye!")
            break