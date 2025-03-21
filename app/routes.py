from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
import os
import secrets
from werkzeug.utils import secure_filename
from app.utils.image_processor import process_invoice_image
from app.utils.ocr_engine import process_invoice_with_ocr
import json

# Khai báo Blueprint
main_bp = Blueprint('main', __name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Thư mục chứa routes.py (app/)
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/upload', methods=['POST'])
def upload_file():
    if 'invoice_image' not in request.files:
        flash('Không tìm thấy file', 'error')
        return redirect(request.url)
    
    file = request.files['invoice_image']
    
    if file.filename == '':
        flash('Không có file nào được chọn', 'error')
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        random_hex = secrets.token_hex(8)
        filename_base, file_ext = os.path.splitext(filename)
        safe_filename = f"{filename_base}_{random_hex}{file_ext}"
        
        input_path = os.path.join(UPLOAD_FOLDER, safe_filename)
        file.save(input_path)
        
        result = process_invoice_image(input_path, UPLOAD_FOLDER, f"{filename_base}_{random_hex}")
        
        ocr_enabled = request.form.get('ocr_enabled') == 'on'
        ocr_results = None
        
        if ocr_enabled:
            ocr_results = process_invoice_with_ocr(result['processed_image'])
            ocr_json_path = os.path.join(UPLOAD_FOLDER, f"{filename_base}_{random_hex}_ocr.json")
            with open(ocr_json_path, 'w', encoding='utf-8') as f:
                json.dump(ocr_results, f, ensure_ascii=False, indent=4)
                
            result['ocr_json'] = ocr_json_path
            result['ocr_results'] = ocr_results
        
        return render_template('result.html', result=result, ocr_results=ocr_results)
    
    flash('File không được phép', 'error')
    return redirect(request.url)

@main_bp.route('/download/<path:filename>')
def download_file(filename):
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    return send_file(filepath, as_attachment=True)

@main_bp.route('/view/<path:filename>')
def view_file(filename):
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    return send_file(filepath)
