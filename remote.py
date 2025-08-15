import RPi.GPIO as GPIO
import time
from flask import Flask, Response, render_template, request
from picamera2 import Picamera2
from libcamera import Transform
import io
from PIL import Image

app = Flask(__name__)

# Motor GPIO Pins: adjust these BCM pin numbers according to your motor driver wiring

motor_pins = [18, 23, 24, 25]
GPIO.setmode(GPIO.BCM)
GPIO.setup(motor_pins, GPIO.OUT, initial=GPIO.LOW)

# Frame generator that starts only when a client is connected

def generate_frames():
    picam2 = Picamera2()
    picam2.configure(
        picam2.create_video_configuration(
            main={"size": (800, 600)},
            transform=Transform(vflip=True, hflip=True) # You can change the vertical and horizontal flip in this line. Remove this line entirely if not needed or set the values as False
        )
    )
    picam2.start()
    time.sleep(2)  # Give time to create pipeline

    try:
        while True:
            frame = picam2.capture_array() # Convert numpy array frame to JPEG format using PIL
            stream = io.BytesIO()
            Image.fromarray(frame).convert('RGB').save(stream, format='JPEG')
            stream.seek(0)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + stream.read() + b'\r\n') # Generate HTML compatible images from the camera pipeline
    except GeneratorExit:
        pass
    finally:
        picam2.stop()
        picam2.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame') # Return each frame

@app.route('/keypress', methods=['POST']) # Gets user input from web interface
def keypress():
    key = request.form['key']
    action = request.form['action']
    print(key, action)

    key_map = {
        "a": (18, 25),
        "w": (23, 25),
        "s": (18, 24),
        "d": (23, 24),
        "ArrowUp": (23, 25),
        "ArrowDown": (18, 24),
        "ArrowRight": (23, 24),
        "ArrowLeft": (18, 25)
    }

    if key in key_map:
        pin1, pin2 = key_map[key]
        GPIO.output(pin1, GPIO.HIGH if action == "down" else GPIO.LOW)
        GPIO.output(pin2, GPIO.HIGH if action == "down" else GPIO.LOW)

    return "OK"

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=80, debug=False) # Change port if you want
    finally:
        GPIO.cleanup() # Clean up GPIO pins on app exit
