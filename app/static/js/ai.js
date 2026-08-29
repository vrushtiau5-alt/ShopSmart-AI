/**
 * ShopSmart AI - Chatbot Assistant Engine
 * Features single-request debouncing, suggestion pill handler, and dynamic card rendering.
 */
document.addEventListener('DOMContentLoaded', function () {
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const chatMessages = document.getElementById('chat-messages');
    const sendBtn = document.getElementById('send-btn');
    const suggestionPills = document.querySelectorAll('.suggestion-pill');

    let isProcessing = false;

    if (!chatForm || !userInput || !chatMessages) return;

    // Handle Form Submit
    chatForm.addEventListener('submit', function (e) {
        e.preventDefault();
        const query = userInput.value.trim();
        if (query && !isProcessing) {
            sendMessage(query);
        }
    });

    // Handle Suggestion Pill Clicks with strict single-request prevention
    suggestionPills.forEach(pill => {
        pill.addEventListener('click', function () {
            if (isProcessing) return;
            const text = this.getAttribute('data-query') || this.innerText.trim();
            if (text) {
                userInput.value = text;
                sendMessage(text);
            }
        });
    });

    function sendMessage(text) {
        if (isProcessing) return;
        isProcessing = true;

        // UI Loading state
        userInput.value = '';
        userInput.disabled = true;
        sendBtn.disabled = true;
        sendBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';

        // 1. Append User Message
        appendMessage(text, 'user');

        // 2. Append Loading Indicator
        const loadingId = 'loading-' + Date.now();
        appendLoadingIndicator(loadingId);

        // 3. Send single AJAX POST request
        fetch('/api/ai/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({ message: text })
        })
        .then(response => response.json())
        .then(data => {
            removeLoadingIndicator(loadingId);
            if (data.success) {
                appendMessage(data.message, 'assistant', data.products);
            } else {
                appendMessage(data.message || 'An error occurred. Please try again.', 'assistant');
            }
        })
        .catch(err => {
            removeLoadingIndicator(loadingId);
            appendMessage('Network connection error. Please try again.', 'assistant');
        })
        .finally(() => {
            isProcessing = false;
            userInput.disabled = false;
            sendBtn.disabled = false;
            sendBtn.innerHTML = '<i class="fas fa-paper-plane"></i>';
            userInput.focus();
        });
    }

    function appendMessage(text, sender, products = []) {
        const row = document.createElement('div');
        row.className = `message-row ${sender}-row`;

        const avatar = document.createElement('div');
        avatar.className = `avatar avatar-${sender === 'user' ? 'user' : 'ai'}`;
        avatar.innerHTML = sender === 'user' ? '<i class="fas fa-user"></i>' : '<i class="fas fa-robot"></i>';

        const bubble = document.createElement('div');
        bubble.className = 'message-bubble';
        bubble.innerHTML = `<div>${escapeHtml(text)}</div>`;

        // Render product cards if available
        if (products && products.length > 0) {
            const grid = document.createElement('div');
            grid.className = 'ai-product-grid';

            products.forEach(p => {
                const card = document.createElement('div');
                card.className = 'ai-mini-card';
                const imgUrl = p.image_url || 'https://via.placeholder.com/200?text=No+Image';
                card.innerHTML = `
                    <img src="${imgUrl}" alt="${escapeHtml(p.title)}" style="width:100%; height:120px; object-fit:contain; background:#fff; border-radius:6px; padding:4px;" onerror="this.onerror=null;this.src='https://via.placeholder.com/200?text=Product+Image';">
                    <div class="fw-bold text-truncate mt-1" style="font-size: 0.85rem;" title="${escapeHtml(p.title)}">${escapeHtml(p.title)}</div>
                    <div class="text-primary fw-bold" style="font-size: 0.9rem;">₹${p.price ? p.price.toFixed(2) : 'N/A'}</div>
                    <div class="text-muted" style="font-size: 0.75rem;">⭐ ${p.rating} (${p.reviews_count})</div>
                    <div class="mt-2 d-grid">
                        <a href="/product/${p.id}" class="btn btn-sm btn-outline-primary py-1" style="font-size: 0.75rem;">View Details</a>
                    </div>
                `;
                grid.appendChild(card);
            });
            bubble.appendChild(grid);
        }

        row.appendChild(avatar);
        row.appendChild(bubble);
        chatMessages.appendChild(row);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function appendLoadingIndicator(id) {
        const row = document.createElement('div');
        row.className = 'message-row assistant-row';
        row.id = id;
        row.innerHTML = `
            <div class="avatar avatar-ai"><i class="fas fa-robot"></i></div>
            <div class="message-bubble text-muted">
                <i class="fas fa-circle-notch fa-spin me-2"></i> Analyzing your request...
            </div>
        `;
        chatMessages.appendChild(row);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function removeLoadingIndicator(id) {
        const el = document.getElementById(id);
        if (el) el.remove();
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.innerText = text;
        return div.innerHTML;
    }
});
