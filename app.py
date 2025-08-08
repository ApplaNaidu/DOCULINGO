import os
from flask import Flask, render_template, request, send_file
from PIL import Image
from googletrans import Translator
import pytesseract
from pdf2image import convert_from_path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont

app = Flask(__name__)
translator = Translator()
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 🧠 Poppler path for PDF to image conversion
POPPLER_PATH = r"C:\Users\appal\Downloads\Release-24.08.0-0\poppler-24.08.0\Library\bin"

@app.route('/')
def index():
    return render_template('index.html', original=None, translated=None, preview_url=None, txt_ready=False)

@app.route('/upload', methods=['POST'])
def upload():
    if 'form' not in request.files:
        return 'No file part'

    file = request.files['form']
    if file.filename == '':
        return 'No selected file'

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(filepath)

    ext = os.path.splitext(file.filename)[1].lower()
    extracted_text = ""
    preview_url = f"/uploads/{file.filename}"

    if ext == ".pdf":
        try:
            images = convert_from_path(filepath, poppler_path=POPPLER_PATH)
            preview_image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'preview.jpg')
            images[0].save(preview_image_path, 'JPEG')
            preview_url = f"/uploads/preview.jpg"
            for image in images:
                extracted_text += pytesseract.image_to_string(image, lang='eng') + "\n"
        except Exception as e:
            return f"PDF conversion failed: {str(e)}"
    else:
        try:
            image = Image.open(filepath)
            extracted_text = pytesseract.image_to_string(image, lang='eng')
        except Exception as e:
            return f"Image error: {str(e)}"

    # 🌐 Translate to Telugu
    telugu_text = translator.translate(extracted_text, dest='te').text

    # 📄 Save TXT output
    txt_path = os.path.join(app.config['UPLOAD_FOLDER'], 'translation.txt')
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(telugu_text)

    return render_template('index.html', original=extracted_text, translated=telugu_text, preview_url=preview_url, txt_ready=True)

@app.route('/download/txt')
def download_txt():
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], 'translation.txt'), as_attachment=True)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename))

if __name__ == '__main__':
    app.run(debug=True)
