package com.ttcs.tenant.error;

public class InvalidCredentialsException extends RuntimeException {
    public InvalidCredentialsException() {
        super("Email/số điện thoại hoặc mật khẩu không đúng.");
    }
}
