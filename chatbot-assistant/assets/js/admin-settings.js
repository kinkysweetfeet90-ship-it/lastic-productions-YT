jQuery(document).ready(function($) {
    const $serviceSelect = $('#ai_service');
    const $openaiKeyWrapper = $('tr:has(#openai_key)');
    const $localUrlWrapper = $('tr:has(#local_url)');
    const $fetchBtn = $('#cba-fetch-models');
    const $modelSelect = $('#cba-model-select');
    const $spinner = $('#cba-model-spinner');

    function toggleFields() {
        const selected = $serviceSelect.val();
        if (selected === 'openai') {
            $openaiKeyWrapper.show();
            $localUrlWrapper.hide();
        } else {
            $openaiKeyWrapper.hide();
            $localUrlWrapper.show();
        }
    }

    $serviceSelect.on('change', toggleFields);
    toggleFields();

    $fetchBtn.on('click', function() {
        $spinner.addClass('is-active');
        $(this).prop('disabled', true);

        $.ajax({
            url: cba_admin_ajax.ajax_url,
            method: 'POST',
            data: {
                action: 'cba_fetch_models',
                nonce: cba_admin_ajax.nonce,
                service: $serviceSelect.val(),
                url: $('#local_url').val(),
                api_key: $('#openai_key').val()
            },
            success: function(response) {
                $spinner.removeClass('is-active');
                $fetchBtn.prop('disabled', false);

                if (response.success) {
                    $modelSelect.empty();
                    response.data.forEach(m => {
                        $modelSelect.append($('<option>').val(m).text(m));
                    });
                } else {
                    alert('Error: ' + response.data.message);
                }
            },
            error: function() {
                $spinner.removeClass('is-active');
                $fetchBtn.prop('disabled', false);
                alert('Connection failed. Please check your AI endpoint.');
            }
        });
    });
});
