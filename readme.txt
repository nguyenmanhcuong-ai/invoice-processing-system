Tôi sẽ hướng dẫn bạn xây dựng một hệ thống xử lý ảnh hóa đơn với khả năng tải lên, chuyển đổi thành ảnh rõ nét và trích xuất nội dung thông qua OCR. Dưới đây là kế hoạch chi tiết cho dự án.
invoice-processing-system/
├── app/
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css
│   │   ├── js/
│   │   │   └── main.js
│   │   └── uploads/
│   │       └── .gitkeep
│   ├── templates/
│   │   ├── base.html
│   │   ├── index.html
│   │   └── result.html
│   ├── __init__.py
│   ├── config.py
│   ├── routes.py
│   └── utils/
│       ├── __init__.py
│       ├── image_processor.py
│       └── ocr_engine.py
├── requirements.txt
├── .env
├── .gitignore
└── run.py

Các công nghệ sử dụng
1.	Backend: 
	Python (Flask)
	OpenCV (xử lý ảnh)
	Tesseract OCR (trích xuất văn bản)
	Pillow (thao tác ảnh)
2.	Frontend: 
	HTML/CSS
	JavaScript
	Bootstrap (giao diện người dùng)

