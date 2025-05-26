document.addEventListener('DOMContentLoaded', function() {
    // Chỉ log một lần khi trang load
    console.log('Order detail page loaded');
    
    const paymentStatusForm = document.getElementById('paymentStatusForm');
    const updatePaymentStatusBtn = document.getElementById('updatePaymentStatusBtn');
    const paymentStatusBadge = document.querySelector('.badge[data-payment-status]');
    
    // Get CSRF token from cookie
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    
    if (paymentStatusForm) {
        console.log('Payment status form found:', paymentStatusForm.action);
        
        paymentStatusForm.addEventListener('submit', function(e) {
            e.preventDefault();
            console.log('Form submitted to:', this.action);
            
            // Disable button and show loading state
            updatePaymentStatusBtn.disabled = true;
            updatePaymentStatusBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Đang cập nhật...';
            
            const formData = new FormData(this);
            const csrftoken = getCookie('csrftoken');
            
            console.log('Sending request with data:', Object.fromEntries(formData));
            
            fetch(this.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'same-origin'
            })
            .then(response => {
                console.log('Response status:', response.status);
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('Response data:', data);
                if (data.success) {
                    // Update UI without reloading
                    if (paymentStatusBadge) {
                        console.log('Updating badge to:', data.payment_status);
                        paymentStatusBadge.textContent = data.payment_status;
                        paymentStatusBadge.className = `badge ${data.payment_status === 'Đã thanh toán' ? 'bg-success' : 'bg-warning'}`;
                        paymentStatusBadge.setAttribute('data-payment-status', data.payment_status);
                    }
                    
                    // Close modal if it exists
                    const modal = bootstrap.Modal.getInstance(document.getElementById('updatePaymentStatusModal'));
                    if (modal) {
                        modal.hide();
                    }
                    
                    // Show success message
                    alert('Cập nhật trạng thái thanh toán thành công!');
                } else {
                    // Show error message
                    alert(data.message || 'Có lỗi xảy ra khi cập nhật trạng thái thanh toán');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Có lỗi xảy ra khi cập nhật trạng thái thanh toán');
            })
            .finally(() => {
                // Reset button state
                updatePaymentStatusBtn.disabled = false;
                updatePaymentStatusBtn.innerHTML = 'Cập nhật';
            });
        });
    } else {
        console.log('Payment status form not found');
    }
}); 