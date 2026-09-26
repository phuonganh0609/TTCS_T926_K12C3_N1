package com.ttcs.tenant.auth;

/** Ném khi refresh token hoặc access token không hợp lệ / đã hết hạn. */
public class InvalidTokenException extends RuntimeException {
    public InvalidTokenException(String message) {
        super(message);
    }
}
