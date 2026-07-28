from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
import textwrap
import os
import uuid

app = Flask(__name__)
CORS(app)

UPLOAD_DIR = "/tmp/pins"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.route('/create-pin', methods=['POST'])
def create_pin():
    data = request.json
    image_url = data.get('image_url')
    pin_text = data.get('pin_text', 'Sleep Better Tonight')
    website = data.get('website', 'getyoursleepguide.online')
    
    if not image_url:
        return jsonify({"error": "image_url is required"}), 400
    
    img_response = requests.get(image_url, timeout=30)
    img = Image.open(BytesIO(img_response.content)).convert("RGBA")
    img = img.resize((1000, 1500), Image.LANCZOS)
    
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw_overlay = ImageDraw.Draw(overlay)
    for i in range(600):
        alpha = int((i / 600) * 220)
        draw_overlay.rectangle([(0, 900 + i), (1000, 901 + i)], fill=(0, 0, 0, alpha))
    draw_overlay.rectangle([(0, 0), (1000, 130)], fill=(0, 0, 0, 150))
    img = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(img)
    
    try:
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 90)
        font_sub = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 42)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 34)
    except:
        font_title = ImageFont.load_default()
        font_sub = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    draw.text((500, 70), website, font=font_small, fill=(200, 210, 255, 220), anchor="mm")
    
    words = pin_text.split()
    if len(words) <= 3:
        lines = [pin_text]
    elif len(words) <= 5:
        mid = len(words) // 2
        lines = [' '.join(words[:mid]), ' '.join(words[mid:])]
    else:
        lines = textwrap.wrap(pin_text, width=15)
    
    y = 980
    for line in lines:
        draw.text((502, y+3), line, font=font_title, fill=(0, 0, 0, 150), anchor="mm")
        draw.text((500, y), line, font=font_title, fill=(255, 255, 255, 255), anchor="mm")
        y += 110
    
    draw.text((500, y + 30), "Click to read the full story", font=font_sub, fill=(255, 220, 120, 230), anchor="mm")
    draw.rounded_rectangle([(100, 1380), (900, 1470)], radius=50, fill=(220, 38, 38, 245))
    draw.text((500, 1425), "READ FULL STORY →", font=font_small, fill=(255, 255, 255, 255), anchor="mm")
    
    filename = f"{uuid.uuid4()}.jpg"
    filepath = os.path.join(UPLOAD_DIR, filename)
    img = img.convert("RGB")
    img.save(filepath, format="JPEG", quality=95)
    
    base_url = request.host_url.rstrip('/')
    image_public_url = f"{base_url}/pin-image/{filename}"
    
    return jsonify({"image_url": image_public_url, "status": "success"})

@app.route('/pin-image/<filename>', methods=['GET'])
def serve_image(filename):
    filepath = os.path.join(UPLOAD_DIR, filename)
    return send_file(filepath, mimetype='image/jpeg')

@app.route('/', methods=['GET'])
def health():
    return jsonify({"status": "Pinterest Pin API running!"})

@app.route('/dashboard')
def dashboard():
    return send_file(os.path.join(os.path.dirname(__file__), 'dashboard.html'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
