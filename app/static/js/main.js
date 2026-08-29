/**
 * ShopSmart AI - Main Application Javascript
 */
document.addEventListener('DOMContentLoaded', function () {
    // Auto-dismiss alert banners after 5 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Wishlist Toggle Buttons
    const wishlistBtns = document.querySelectorAll('.btn-wishlist-toggle');
    wishlistBtns.forEach(btn => {
        btn.addEventListener('click', function (e) {
            e.preventDefault();
            const productId = this.getAttribute('data-product-id');
            const icon = this.querySelector('i');

            fetch('/wishlist/toggle', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: `product_id=${productId}`
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    if (data.added) {
                        icon.classList.remove('far');
                        icon.classList.add('fas', 'text-danger');
                    } else {
                        icon.classList.remove('fas', 'text-danger');
                        icon.classList.add('far');
                    }
                    const badge = document.getElementById('wishlist-badge');
                    if (badge) {
                        let cnt = parseInt(badge.innerText || '0');
                        badge.innerText = data.added ? cnt + 1 : Math.max(0, cnt - 1);
                    }
                }
            })
            .catch(err => {
                window.location.href = '/login';
            });
        });
    });
});
