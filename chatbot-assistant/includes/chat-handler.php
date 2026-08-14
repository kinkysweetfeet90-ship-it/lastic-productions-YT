<?php
/**
 * AJAX Handler for Chatbot Assistant
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

class CBA_Chat_Handler {

	public function __construct() {
		add_action( 'wp_ajax_cba_send_message', array( $this, 'handle_message' ) );
		add_action( 'wp_ajax_nopriv_cba_send_message', array( $this, 'handle_message' ) );
		
        // For Admin Settings (model fetching)
        add_action( 'wp_ajax_cba_fetch_models', array( $this, 'fetch_models' ) );
	}

	public function handle_message() {
		check_ajax_referer( 'cba_chat_nonce', 'nonce' );

		$message = isset( $_POST['message'] ) ? sanitize_text_field( $_POST['message'] ) : '';
		$history = isset( $_POST['history'] ) ? json_decode( stripslashes( $_POST['history'] ), true ) : array();

		if ( empty( $message ) ) {
			wp_send_json_error( array( 'message' => 'No message provided' ) );
		}

		$settings = get_option( 'cba_settings', array() );
		$service  = isset( $settings['ai_service'] ) ? $settings['ai_service'] : 'openai';
		$model    = isset( $settings['selected_model'] ) ? $settings['selected_model'] : '';
		
		$response = '';

		if ( $service === 'openai' ) {
			$response = $this->call_openai( $message, $history, $settings );
		} else {
			$response = $this->call_local_ai( $message, $history, $settings );
		}

		if ( is_wp_error( $response ) ) {
			wp_send_json_error( array( 'message' => $response->get_error_message() ) );
		}

		wp_send_json_success( array( 'message' => $response ) );
	}

	private function call_openai( $message, $history, $settings ) {
		$api_key = isset( $settings['openai_key'] ) ? $settings['openai_key'] : '';
		if ( empty( $api_key ) ) {
			return new WP_Error( 'no_api_key', 'OpenAI API key not provided' );
		}

		$model = isset( $settings['selected_model'] ) ? $settings['selected_model'] : 'gpt-3.5-turbo';
		
		$messages = array();
		// System prompt could go here if needed
		foreach ( $history as $h ) {
			$messages[] = array( 'role' => $h['role'], 'content' => $h['content'] );
		}
		$messages[] = array( 'role' => 'user', 'content' => $message );

		$response = wp_remote_post( 'https://api.openai.com/v1/chat/completions', array(
			'headers' => array(
				'Authorization' => 'Bearer ' . $api_key,
				'Content-Type'  => 'application/json',
			),
			'body'    => json_encode( array(
				'model'    => $model,
				'messages' => $messages,
			) ),
			'timeout' => 30,
		) );

		if ( is_wp_error( $response ) ) {
			return $response;
		}

		$body = json_decode( wp_remote_retrieve_body( $response ), true );
		return isset( $body['choices'][0]['message']['content'] ) ? $body['choices'][0]['message']['content'] : 'Sorry, I couldn\'t get a response.';
	}

	private function call_local_ai( $message, $history, $settings ) {
		$url = isset( $settings['local_url'] ) ? $settings['local_url'] : 'http://localhost:11434';
		$service = $settings['ai_service']; // 'ollama' or 'lm-studio'
        $model = isset( $settings['selected_model'] ) ? $settings['selected_model'] : 'llama2';
		
		$endpoint = '';
		$payload  = array();

		if ( $service === 'ollama' ) {
			$endpoint = trailingslashit( $url ) . 'api/chat';
			$messages = array();
			foreach ( $history as $h ) {
				$messages[] = array( 'role' => $h['role'], 'content' => $h['content'] );
			}
			$messages[] = array( 'role' => 'user', 'content' => $message );
			
			$payload = array(
				'model'  => $model,
				'messages' => $messages,
				'stream' => false,
			);
		} else if ( $service === 'lm-studio' ) {
			$endpoint = trailingslashit( $url ) . 'v1/chat/completions';
			$messages = array();
			foreach ( $history as $h ) {
				$messages[] = array( 'role' => $h['role'], 'content' => $h['content'] );
			}
			$messages[] = array( 'role' => 'user', 'content' => $message );

			$payload = array(
				'model'    => $model,
				'messages' => $messages,
			);
		}

		$response = wp_remote_post( $endpoint, array(
			'headers' => array( 'Content-Type' => 'application/json' ),
			'body'    => json_encode( $payload ),
			'timeout' => 45,
		) );

		if ( is_wp_error( $response ) ) {
			return $response;
		}

		$body = json_decode( wp_remote_retrieve_body( $response ), true );
		
		if ( $service === 'ollama' ) {
			return $body['message']['content'];
		} else {
			return $body['choices'][0]['message']['content'];
		}
	}

    public function fetch_models() {
		check_ajax_referer( 'cba_admin_nonce', 'nonce' );

        $service = $_POST['service'];
        $url = $_POST['url'];
        $api_key = $_POST['api_key'];

        $models = array();

        if ($service === 'openai') {
            $response = wp_remote_get('https://api.openai.com/v1/models', array(
                'headers' => array( 'Authorization' => 'Bearer ' . $api_key )
            ));
            if (!is_wp_error($response)) {
                $body = json_decode(wp_remote_retrieve_body($response), true);
                foreach($body['data'] as $m) $models[] = $m['id'];
            }
        } else if ($service === 'ollama') {
            $response = wp_remote_get(trailingslashit($url) . 'api/tags');
            if (!is_wp_error($response)) {
                $body = json_decode(wp_remote_retrieve_body($response), true);
                foreach($body['models'] as $m) $models[] = $m['name'];
            }
        } else if ($service === 'lm-studio') {
            $response = wp_remote_get(trailingslashit($url) . 'v1/models');
            if (!is_wp_error($response)) {
                $body = json_decode(wp_remote_retrieve_body($response), true);
                foreach($body['data'] as $m) $models[] = $m['id'];
            }
        }

        wp_send_json_success($models);
    }
}
