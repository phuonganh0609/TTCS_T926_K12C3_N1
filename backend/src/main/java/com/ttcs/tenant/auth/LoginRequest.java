package com.ttcs.tenant.auth;

import jakarta.validation.constraints.NotBlank;

public record LoginRequest(
        @NotBlank(message = "Email hoặc số điện thoại là bắt buộc")
        String identifier,
        @NotBlank(message = "Mật khẩu là bắt buộc")
        String password
) {
}
