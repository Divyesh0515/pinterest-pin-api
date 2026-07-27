from flask import Flask, request, jsonify
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
import base64
import textwrap

app = Flask(__name__)

@app.route('/create-pin', methods=['POST'])
def create_pin():
    data = request.json
    image_url = data.get('image_url')
    pin_text = data.get('pin_text', 'Sleep Better Tonight')
    website = data.get('website', 'getyoursleepguide.online')
    
    # Download image from Fal.ai
    img_response = requests.get(image_url, timeout=30)
    img = Image.open(BytesIO(img_response.content)).convert("RGBA")
    img = img.resize((1000, 1500), Image.LANCZOS)
    
    # Dark overlay at bottom
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw_overlay = ImageDraw.Draw(overlay)
    for i in range(600):
        alpha = int((i / 600) * 220)
        draw_overlay.rectangle([(0, 900 + i), (1000, 901 + i)], fill=(0, 0, 0, alpha))
    draw_overlay.rectangle([(0, 0), (1000, 130)], fill=(0, 0, 0, 150))
    img = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(img)
    
    # Fonts
    try:
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 90)
        font_sub = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 42)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 34)
    except:
        font_title = ImageFont.load_default()
        font_sub = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # Website top
    draw.text((500, 70), website, font=font_small, fill=(200, 210, 255, 220), anchor="mm")
    
    # Pin text - wrap if long
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
        # Shadow
        draw.text((502, y+3), line, font=font_title, fill=(0, 0, 0, 150), anchor="mm")
        # Text
        draw.text((500, y), line, font=font_title, fill=(255, 255, 255, 255), anchor="mm")
        y += 110
    
    # Subtitle
    draw.text((500, y + 30), "Click to read the full story", font=font_sub, fill=(255, 220, 120, 230), anchor="mm")
    
    # CTA Button
    draw.rounded_rectangle([(100, 1380), (900, 1470)], radius=50, fill=(220, 38, 38, 245))
    draw.text((500, 1425), "READ FULL STORY →", font=font_small, fill=(255, 255, 255, 255), anchor="mm")
    
    # Save to bytes
    img = img.convert("RGB")
    buffer = BytesIO()
    img.save(buffer, format="JPEG", quality=95)
    buffer.seek(0)
    
    # Return base64
    img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return jsonify({"image_base64": img_base64, "status": "success"})

@app.route('/', methods=['GET'])
def health():
    return jsonify({"status": "Pinterest Pin API running!"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
