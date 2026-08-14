jQuery(document).ready(function($) {
    const $container = $('#cba-chat-container');
    const $toggle = $('#cba-chat-toggle');
    const $close = $('#cba-chat-close');
    const $input = $('#cba-chat-input');
    const $send = $('#cba-chat-send');
    const $messages = $('#cba-chat-messages');
    
    let chatHistory = [];

    // Toggle Chat Window
    $toggle.on('click', function() {
        $container.addClass('cba-open').removeClass('cba-closed');
        $input.focus();
    });

    $close.on('click', function() {
        $container.addClass('cba-closed').removeClass('cba-open');
    });

    // Send Message
    function sendMessage() {
        const message = $input.val().trim();
        if (!message) return;

        // Add user message to UI
        appendMessage('user', message);
        $input.val('');
        
        // Show typing indicator
        const $typing = $('<div class="cba-message cba-bot cba-typing">Typing...</div>');
        $messages.append($typing);
        scrollToBottom();

        // AJAX Request
        $.ajax({
            url: cba_ajax.ajax_url,
            method: 'POST',
            data: {
                action: 'cba_send_message',
                nonce: cba_ajax.nonce,
                message: message,
                history: JSON.stringify(chatHistory)
            },
            success: function(response) {
                $typing.remove();
                if (response.success) {
                    const reply = response.data.message;
                    appendMessage('bot', reply);
                    chatHistory.push({ role: 'user', content: message });
                    chatHistory.push({ role: 'assistant', content: reply });
                    
                    // Keep history manageable
                    if (chatHistory.length > 20) chatHistory.splice(0, 2);
                } else {
                    appendMessage('bot', 'Error: ' + (response.data.message || 'Unknown error'));
                }
            },
            error: function() {
                $typing.remove();
                appendMessage('bot', 'Failed to connect to assistant. Please try again later.');
            }
        });
    }

    function appendMessage(role, content) {
        const $msg = $('<div class="cba-message"></div>').addClass('cba-' + role).text(content);
        $messages.append($msg);
        scrollToBottom();
    }

    function scrollToBottom() {
        $messages.scrollTop($messages[0].scrollHeight);
    }

    $send.on('click', sendMessage);
    $input.on('keypress', function(e) {
        if (e.which === 13) sendMessage();
    });
});
