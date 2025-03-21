import cv2
import numpy as np
import os
from pdf2image import convert_from_path
import img2pdf
from PIL import Image

def enhance_receipt_to_scan_quality(image_path, output_image_path, dpi=300):
    """
    Xử lý ảnh hóa đơn chụp từ điện thoại thành ảnh chất lượng như scan PDF
    
    Args:
        image_path: Đường dẫn đến ảnh gốc
        output_image_path: Đường dẫn để lưu ảnh đã xử lý
        dpi: Độ phân giải mong muốn (mặc định là 300 dpi cho chất lượng scan)
    
    Returns:
        Đường dẫn đến ảnh đã xử lý
    """
    # Đọc ảnh
    img = cv2.imread(image_path)
    if img is None:
        raise Exception(f"Không thể đọc ảnh từ {image_path}")
    
    # 1. Tiền xử lý - Chỉnh sửa kích thước và định hình lại
    # Tăng độ phân giải nếu cần (giả sử 300 dpi là tiêu chuẩn scan)
    height, width = img.shape[:2]
    scale_factor = 1
    if width < 2000:  # Hóa đơn scan thường có độ phân giải cao
        scale_factor = 2500 / width
        img = cv2.resize(img, None, fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_CUBIC)
    
    # 2. Tự động hiệu chỉnh góc nghiêng (deskew)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Làm mờ và tìm cạnh
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150, apertureSize=3)
    
    # Tìm đường thẳng để xác định góc nghiêng
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, 100, minLineLength=100, maxLineGap=10)
    angles = []
    
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            if x2 - x1 != 0:  # Tránh chia cho 0
                angle = np.arctan((y2 - y1) / (x2 - x1)) * 180 / np.pi
                angles.append(angle)
        
        if angles:
            # Lọc bỏ các góc quá khác biệt
            from scipy import stats
            angle_mode = stats.mode(np.array(angles), keepdims=True)[0][0]
            
            # Chỉ xoay nếu góc nghiêng đáng kể (>0.5 độ)
            if abs(angle_mode) > 0.5:
                h, w = img.shape[:2]
                center = (w // 2, h // 2)
                rotation_matrix = cv2.getRotationMatrix2D(center, angle_mode, 1.0)
                img = cv2.warpAffine(img, rotation_matrix, (w, h), 
                                    flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 3. Tăng cường chất lượng
    # Khử nhiễu mạnh hơn
    denoised = cv2.fastNlMeansDenoising(gray, None, h=15, templateWindowSize=7, searchWindowSize=21)
    
    # Tăng cường tương phản sử dụng CLAHE
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    enhanced = clahe.apply(denoised)
    
    # 4. Xử lý bóng và làm nổi bật văn bản
    # Áp dụng Morphology để cải thiện văn bản
    kernel = np.ones((1, 1), np.uint8)
    enhanced = cv2.morphologyEx(enhanced, cv2.MORPH_CLOSE, kernel)
    
    # 5. Thêm bước làm nổi bật cạnh để văn bản rõ ràng hơn
    edge_enhanced = cv2.Laplacian(enhanced, cv2.CV_8U, ksize=3)
    sharpened = cv2.addWeighted(enhanced, 1.5, edge_enhanced, -0.5, 0)
    
    # 6. Ngưỡng hóa thích ứng - tối ưu cho văn bản hóa đơn
    # Sử dụng Otsu's thresholding kết hợp với adaptive thresholding
    _, otsu_threshold = cv2.threshold(sharpened, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)
    adaptive_threshold = cv2.adaptiveThreshold(
        sharpened, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY, 15, 5
    )
    
    # Kết hợp hai ngưỡng
    combined = cv2.bitwise_and(otsu_threshold, adaptive_threshold)
    
    # 7. Áp dụng bộ lọc đặc biệt cho kiểu scan
    # Giảm nhiễu đặc trưng của scan bằng closing
    kernel = np.ones((2, 2), np.uint8)
    scan_like = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, kernel)
    
    # 8. Hiệu chỉnh cuối cùng - thêm hiệu ứng giống scan
    # Làm mịn viền văn bản
    final_img = cv2.GaussianBlur(scan_like, (3, 3), 0)
    
    # 9. Tăng cường văn bản lần cuối
    final_img = cv2.morphologyEx(final_img, cv2.MORPH_CLOSE, np.ones((1, 1), np.uint8))
    
    # 10. Thêm nền trắng đặc trưng của giấy scan
    # Tạo nền trắng và đặt văn bản lên
    white_bg = np.ones_like(final_img) * 255
    final_img = cv2.bitwise_and(white_bg, final_img)
    
    # Lưu ảnh đã xử lý
    cv2.imwrite(output_image_path, final_img)
    
    return output_image_path

def convert_image_to_pdf(image_path, pdf_path):
    """
    Chuyển đổi ảnh đã xử lý thành file PDF chất lượng cao
    
    Args:
        image_path: Đường dẫn đến ảnh đã xử lý
        pdf_path: Đường dẫn để lưu file PDF
        
    Returns:
        Đường dẫn đến file PDF
    """
    # Mở ảnh với Pillow
    image = Image.open(image_path)
    
    # Chuyển ảnh thành PDF với độ phân giải cao
    pdf_bytes = img2pdf.convert(
        image_path, 
        dpi=300, 
        x_scale=1,
        y_scale=1
    )
    
    # Lưu PDF
    with open(pdf_path, "wb") as file:
        file.write(pdf_bytes)
    
    return pdf_path

def process_invoice_image(input_path, output_folder, filename_base):
    """
    Xử lý ảnh hóa đơn và chuyển đổi thành PDF chất lượng cao
    
    Args:
        input_path: Đường dẫn đến ảnh hóa đơn gốc
        output_folder: Thư mục để lưu kết quả
        filename_base: Tên cơ sở cho các file đầu ra
        
    Returns:
        dict: Thông tin về các file đã tạo
    """
    # Tạo tên file đầu ra
    processed_image_path = os.path.join(output_folder, f"{filename_base}_processed.png")
    pdf_path = os.path.join(output_folder, f"{filename_base}.pdf")
    
    # Xử lý ảnh
    enhanced_image = enhance_receipt_to_scan_quality(input_path, processed_image_path)
    
    # Chuyển đổi sang PDF
    pdf_file = convert_image_to_pdf(enhanced_image, pdf_path)
    
    return {
        "processed_image": processed_image_path,
        "pdf_file": pdf_file,
        "original_image": input_path
    }