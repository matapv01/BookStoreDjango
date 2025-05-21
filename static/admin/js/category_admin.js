document.addEventListener('DOMContentLoaded', function() {
    const imageInput = document.querySelector('input[name="image_file"]');
    if (imageInput) {
        // Tạo container cho preview
        const previewContainer = document.createElement('div');
        previewContainer.id = 'image-preview-container';
        previewContainer.style.cssText = `
            margin-top: 15px;
            padding: 15px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            display: none;
        `;

        // Tạo element hiển thị preview
        const previewImage = document.createElement('img');
        previewImage.id = 'preview-image';
        previewImage.style.cssText = `
            max-width: 300px;
            width: 100%;
            height: auto;
            border-radius: 8px;
            display: block;
            margin: 10px 0;
        `;

        // Tạo label cho preview
        const previewLabel = document.createElement('p');
        previewLabel.innerHTML = '<strong>Xem trước ảnh:</strong>';
        previewLabel.style.marginBottom = '10px';

        // Thêm các elements vào container
        previewContainer.appendChild(previewLabel);
        previewContainer.appendChild(previewImage);

        // Thêm container vào sau input
        imageInput.parentNode.insertBefore(previewContainer, imageInput.nextSibling);

        // Xử lý sự kiện khi chọn file
        imageInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    previewImage.src = e.target.result;
                    previewContainer.style.display = 'block';
                };
                reader.readAsDataURL(file);
            } else {
                previewContainer.style.display = 'none';
            }
        });

        // Thêm style cho input file
        imageInput.style.cssText = `
            display: block;
            width: 100%;
            padding: 10px;
            margin: 10px 0;
            border: 2px dashed #ccc;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s ease;
        `;

        imageInput.addEventListener('mouseover', function() {
            this.style.borderColor = '#007bff';
        });

        imageInput.addEventListener('mouseout', function() {
            this.style.borderColor = '#ccc';
        });
    }
}); 