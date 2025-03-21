import os
from dotenv import load_dotenv

# Nạp biến môi trường từ file .env
load_dotenv()

class Config:
    """Cấu hình cơ bản cho ứng dụng Flask"""
    # Khóa bí mật cho ứng dụng
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard-to-guess-string'
    
    # Cấu hình upload
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # giới hạn kích thước file 16MB
    UPLOAD_FOLDER = os.path.join('app', 'static', 'uploads')
    
    # Cấu hình OCR
    TESSERACT_CMD = os.environ.get('TESSERACT_CMD') or 'tesseract'
    
    # Ngôn ngữ mặc định cho OCR
    DEFAULT_OCR_LANG = os.environ.get('DEFAULT_OCR_LANG') or 'vie'