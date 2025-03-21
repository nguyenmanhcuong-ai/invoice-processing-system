// Hiệu ứng khi tải trang
document.addEventListener('DOMContentLoaded', function() {
    // Hiệu ứng fade-in cho nội dung
    const content = document.querySelector('.container');
    if (content) {
        content.style.opacity = 0;
        content.style.transition = 'opacity 0.5s ease';
        
        setTimeout(() => {
            content.style.opacity = 1;
        }, 100);
    }
    
    // Hiệu ứng cho file upload
    const fileInput = document.getElementById('invoice_image');
    if (fileInput) {
        const fileLabel = document.querySelector('label[for="invoice_image"]');
        const originalText = fileLabel.textContent;
        
        fileInput.addEventListener('change', function() {
            if (this.files.length > 0) {
                const fileName = this.files[0].name;
                fileLabel.textContent = `Ảnh đã chọn: ${fileName}`;
                
                // Hiển thị ảnh preview
                const reader = new FileReader();
                reader.onload = function(e) {
                    let previewContainer = document.getElementById('image-preview');
                    if (!previewContainer) {
                        previewContainer = document.createElement('div');
                        previewContainer.id = 'image-preview';
                        previewContainer.className = 'mt-3 border rounded p-2 text-center';
                        fileInput.parentNode.appendChild(previewContainer);
                    }
                    
                    previewContainer.innerHTML = `
                        <p class="mb-1">Xem trước:</p>
                        <img src="${e.target.result}" class="img-fluid" style="max-height: 200px;" alt="Preview">
                    `;
                };
                reader.readAsDataURL(this.files[0]);
            } else {
                fileLabel.textContent = originalText;
                const previewContainer = document.getElementById('image-preview');
                if (previewContainer) {
                    previewContainer.remove();
                }
            }
        });
    }
    
    // Xử lý alerts tự động đóng
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.classList.remove('show');
            setTimeout(() => {
                alert.remove();
            }, 500);
        }, 5000);
    });
});

// Hiệu ứng loading khi submit form
document.addEventListener('submit', function(e) {
    if (e.target.matches('form[action*="upload_file"]')) {
        // Tạo overlay loading
        const loadingOverlay = document.createElement('div');
        loadingOverlay.className = 'loading-overlay';
        loadingOverlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.5);
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            z-index: 9999;
        `;
        
        loadingOverlay.innerHTML = `
            <div class="spinner-border text-light" role="status" style="width: 3rem; height: 3rem;">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="text-light mt-3">Đang xử lý hóa đơn, vui lòng đợi...</p>
        `;
        
        document.body.appendChild(loadingOverlay);
    }
});

// Xử lý tooltip và popover
document.addEventListener('DOMContentLoaded', function() {
    // Khởi tạo tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Khởi tạo popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
});