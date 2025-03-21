import pytesseract
from PIL import Image
import os
import re
import cv2
import numpy as np

# Cấu hình đường dẫn Tesseract trên Windows
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def preprocess_for_ocr(image_path):
    """
    Tiền xử lý ảnh để tối ưu hóa cho OCR
    
    Args:
        image_path: Đường dẫn đến ảnh cần xử lý
        
    Returns:
        numpy.ndarray: Ảnh đã được xử lý
    """
    # Đọc ảnh
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Không thể đọc file ảnh: {image_path}")
    
    # Resize ảnh để tăng độ phân giải (giúp OCR đọc chữ nhỏ tốt hơn)
    scale_factor = 1.5
    height, width = img.shape[:2]
    img = cv2.resize(img, (int(width * scale_factor), int(height * scale_factor)), interpolation=cv2.INTER_LINEAR)
    
    # Chuyển sang ảnh xám
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Khử nhiễu nâng cao
    denoised = cv2.fastNlMeansDenoising(gray, h=15, templateWindowSize=7, searchWindowSize=21)
    
    # Tăng cường tương phản sử dụng CLAHE
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(denoised)
    
    # Làm sắc nét ảnh
    sharpening_kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
    sharpened = cv2.filter2D(enhanced, -1, sharpening_kernel)
    
    # Ngưỡng hóa thích ứng với tham số tối ưu
    binary = cv2.adaptiveThreshold(
        sharpened, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY, 15, 5
    )
    
    # Loại bỏ nhiễu nhỏ bằng morphological operations
    kernel = np.ones((3, 3), np.uint8)
    cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=1)
    
    return cleaned

def perform_ocr(image_path, lang='vie'):
    """
    Thực hiện OCR trên ảnh hóa đơn
    
    Args:
        image_path: Đường dẫn đến ảnh cần OCR
        lang: Ngôn ngữ OCR (mặc định: tiếng Việt)
        
    Returns:
        str: Văn bản trích xuất được
    """
    # Tiền xử lý ảnh
    processed_image = preprocess_for_ocr(image_path)
    
    # Cấu hình tùy chỉnh cho Tesseract để cải thiện độ chính xác
    custom_config = r'--oem 3 --psm 6'
    text = pytesseract.image_to_string(processed_image, lang=lang, config=custom_config)
    
    return text.strip()

def extract_invoice_info(ocr_text):
    """
    Trích xuất thông tin hóa đơn từ văn bản OCR
    
    Args:
        ocr_text: Văn bản trích xuất từ OCR
        
    Returns:
        dict: Thông tin hóa đơn đã trích xuất
    """
    invoice_info = {
        "invoice_number": None,
        "tax_code": None,  # Thêm trường mã số thuế
        "date": None,
        "seller": None,
        "buyer": None,
        "total_amount": None,
        "tax": None,
        "items": []
    }
    
    # Trích xuất số hóa đơn (hỗ trợ dãy số đơn giản hoặc có tiền tố)
    inv_num_match = re.search(r'(Số|Số hóa đơn|So|No|Invoice\s*No\.?|Mã\s*hóa\s*đơn)[:\-\s]*(\d{1,15})', ocr_text, re.IGNORECASE)
    if inv_num_match:
        invoice_info["invoice_number"] = inv_num_match.group(2).strip()
    else:
        # Nếu không tìm thấy tiền tố, thử tìm dãy số độc lập gần đầu văn bản
        lines = ocr_text.split('\n')
        for line in lines[:5]:  # Giới hạn tìm trong 5 dòng đầu
            num_only = re.search(r'^\s*(\d{5,15})\s*$', line)
            if num_only:
                invoice_info["invoice_number"] = num_only.group(1).strip()
                break
    
    # Trích xuất mã số thuế (hỗ trợ dãy số 10-13 chữ số, thường gần "MST" hoặc "Tax Code")
    tax_code_match = re.search(r'(MST|Mã số thuế|Tax\s*Code)[:\-\s]*(\d{10,13})', ocr_text, re.IGNORECASE)
    if tax_code_match:
        invoice_info["tax_code"] = tax_code_match.group(2).strip()
    else:
        # Thử tìm dãy số 10-13 chữ số độc lập
        tax_code_fallback = re.search(r'(?<!\d)\d{10,13}(?!\d)', ocr_text)
        if tax_code_fallback:
            invoice_info["tax_code"] = tax_code_fallback.group(0).strip()
    
    # Trích xuất ngày (hỗ trợ định dạng linh hoạt hơn)
    date_match = re.search(r'(Ngày|Ngay|Date|Ngày phát hành)[^\d]*(\d{1,2})[-/\.\s](\d{1,2})[-/\.\s](\d{4}|\d{2})', ocr_text, re.IGNORECASE)
    if date_match:
        day, month, year = date_match.group(2), date_match.group(3), date_match.group(4)
        invoice_info["date"] = f"{day}/{month}/{year}"
    
    # Trích xuất người bán (hỗ trợ nhiều từ khóa hơn)
    seller_match = re.search(r'(Đơn vị bán hàng|Người bán|Seller|Công ty|Nhà cung cấp|Nhân viên)[^\n]*[:\-\s]*(.*)', ocr_text, re.IGNORECASE)
    if seller_match:
        invoice_info["seller"] = seller_match.group(2).strip()
    else:
        # Thử tìm dòng gần đầu hóa đơn (thường là tên công ty)
        if len(lines) > 1:
            invoice_info["seller"] = lines[0].strip() if lines[0] else None
    
    # Trích xuất người mua
    buyer_match = re.search(r'(Đơn vị mua hàng|Người mua|Buyer|Khách hàng)[^\n]*[:\-\s]*(.*)', ocr_text, re.IGNORECASE)
    if buyer_match:
        invoice_info["buyer"] = buyer_match.group(2).strip()
    
    # Trích xuất tổng tiền (hỗ trợ định dạng tiền tệ Việt Nam)
    amount_match = re.search(r'(Tổng tiền|Tổng cộng|Tong tien|Total|Thành tiền|Tổng tiền thanh toán)[^\d]*([\d\.,]+(?:\s*VND)?)', ocr_text, re.IGNORECASE)
    if amount_match:
        total = amount_match.group(2).replace(',', '').replace('.', '')
        invoice_info["total_amount"] = total.strip()
    
    # Trích xuất thuế (hỗ trợ nhiều định dạng hơn)
    tax_match = re.search(r'(VAT|Thuế|Tax|Thuế GTGT)[^\d]*([\d\.,]+(?:\s*VND)?)', ocr_text, re.IGNORECASE)
    if tax_match:
        tax = tax_match.group(2).replace(',', '').replace('.', '')
        invoice_info["tax"] = tax.strip()
    
    # Trích xuất danh sách mặt hàng (nếu có bảng sản phẩm)
    items_section = re.search(r'(STT|Mô tả|Sản phẩm|Hàng hóa|Dịch vụ).*?(?=Tổng tiền|Tổng cộng|Total|$)', ocr_text, re.DOTALL | re.IGNORECASE)
    if items_section:
        items_text = items_section.group(0)
        item_lines = [line.strip() for line in items_text.split('\n') if line.strip()]
        for line in item_lines[1:]:  # Bỏ dòng tiêu đề
            parts = re.split(r'\s{2,}', line)  # Tách bằng khoảng trắng lớn
            if len(parts) >= 2 and any(char.isdigit() for char in parts[-1]):  # Kiểm tra có số (giá tiền)
                invoice_info["items"].append({
                    "description": parts[1] if len(parts) > 1 else parts[0],
                    "amount": parts[-1]
                })
    
    return invoice_info

def process_invoice_with_ocr(image_path, lang='vie'):
    """
    Xử lý hóa đơn với OCR để lấy thông tin
    
    Args:
        image_path: Đường dẫn đến ảnh hóa đơn
        lang: Ngôn ngữ OCR
        
    Returns:
        dict: Thông tin hóa đơn đã trích xuất
    """
    # Thực hiện OCR
    ocr_text = perform_ocr(image_path, lang)
    
    # Trích xuất thông tin
    invoice_info = extract_invoice_info(ocr_text)
    
    # Thêm văn bản OCR gốc
    invoice_info["raw_text"] = ocr_text
    
    return invoice_info