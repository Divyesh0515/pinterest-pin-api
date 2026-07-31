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

BASE_DIR = os.path.dirname(__file__)
FONT_EXTRABOLD = os.path.join(BASE_DIR, 'Poppins-ExtraBold.ttf')
FONT_BOLD      = os.path.join(BASE_DIR, 'Poppins-Bold.ttf')

def draw_text_with_stroke(draw, pos, text, font, fill=(255,255,255,255), stroke=6, stroke_fill=(0,0,0,255), anchor="mm"):
    x, y = pos
    for dx in range(-stroke, stroke+1):
        for dy in range(-stroke, stroke+1):
            if dx != 0 or dy != 0:
                draw.text((x+dx, y+dy), text, font=font, fill=stroke_fill, anchor=anchor)
    draw.text((x, y), text, font=font, fill=fill, anchor=anchor)

@app.route('/create-pin', methods=['POST'])
def create_pin():
    data = request.json
    image_url = data.get('image_url', '').strip()
    pin_text  = data.get('pin_text', 'Sleep Better Tonight').strip()
    website   = data.get('website', 'getyoursleepguide.online').strip()

    if not image_url:
        return jsonify({"error": "image_url is required"}), 400

    try:
        img_response = requests.get(image_url, timeout=30)
        img_response.raise_for_status()
        img = Image.open(BytesIO(img_response.content)).convert("RGBA")
    except Exception as e:
        return jsonify({"error": f"Failed to fetch image: {str(e)}"}), 400

    img = img.resize((1000, 1500), Image.LANCZOS)

    # Dark gradient overlay
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw_overlay = ImageDraw.Draw(overlay)
    for i in range(700):
        alpha = int((i / 700) * 235)
        draw_overlay.rectangle([(0, 800 + i), (1000, 801 + i)], fill=(0, 0, 0, alpha))
    draw_overlay.rectangle([(0, 0), (1000, 115)], fill=(0, 0, 0, 190))
    img = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(img)

    # Dynamic font size
    word_count = len(pin_text.split())
    if word_count <= 3:
        title_size = 100
        wrap_width = 12
    elif word_count <= 5:
        title_size = 88
        wrap_width = 14
    elif word_count <= 8:
        title_size = 74
        wrap_width = 16
    else:
        title_size = 62
        wrap_width = 18

    try:
        font_title   = ImageFont.truetype(FONT_EXTRABOLD, title_size)
        font_website = ImageFont.truetype(FONT_BOLD, 38)
        font_sub     = ImageFont.truetype(FONT_BOLD, 42)
        font_btn     = ImageFont.truetype(FONT_EXTRABOLD, 40)
    except Exception as e:
        return jsonify({"error": f"Font load failed: {str(e)}"}), 500

    # Website top bar
    draw_text_with_stroke(draw, (500, 60), website, font_website,
                          fill=(255, 255, 255, 255), stroke=3)

    # Pin title
    lines = textwrap.wrap(pin_text, width=wrap_width)
    line_height = title_size + 50  # ← +50 for more line spacing
    total_height = len(lines) * line_height
    y_start = 970 - (total_height // 2)

    for line in lines:
        draw_text_with_stroke(draw, (500, y_start), line, font_title,
                              fill=(255, 255, 255, 255), stroke=6,
                              stroke_fill=(0, 0, 0, 255))
        y_start += line_height

    # Subtitle
    draw_text_with_stroke(draw, (500, y_start + 30),
                          "Click to read the full story", font_sub,
                          fill=(255, 220, 100, 240), stroke=3,
                          stroke_fill=(0, 0, 0, 220))

    # Red button
    draw.rounded_rectangle([(80, 1385), (920, 1478)], radius=50, fill=(220, 38, 38, 255))
    draw.text((500, 1430), "READ FULL STORY", font=font_btn,
              fill=(255, 255, 255, 255), anchor="mm")

    # Save
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
    if not os.path.exists(filepath):
        return jsonify({"error": "Image not found"}), 404
    return send_file(filepath, mimetype='image/jpeg')


@app.route('/', methods=['GET'])
def health():
    return jsonify({"status": "Pinterest Pin API running!"})


@app.route('/dashboard')
def dashboard():
    return send_file(os.path.join(os.path.dirname(__file__), 'dashboard.html'))


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
