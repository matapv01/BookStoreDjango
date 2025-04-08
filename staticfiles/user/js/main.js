// Xử lý sự kiện khi tài liệu đã sẵn sàng
document.addEventListener('DOMContentLoaded', function() {
    // Xử lý đóng thông báo alert
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        const closeButton = alert.querySelector('.btn-close');
        if (closeButton) {
            closeButton.addEventListener('click', function() {
                alert.remove();
            });
        }
    });

    // Xử lý cập nhật số lượng trong giỏ hàng
    const quantityInputs = document.querySelectorAll('.cart-quantity');
    quantityInputs.forEach(function(input) {
        input.addEventListener('change', function() {
            const form = this.closest('form');
            if (form) {
                form.submit();
            }
        });
    });
});
