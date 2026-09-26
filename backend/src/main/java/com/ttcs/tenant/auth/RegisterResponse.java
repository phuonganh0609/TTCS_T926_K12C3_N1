package com.ttcs.tenant.auth;

import com.ttcs.tenant.user.Role;

public record RegisterResponse(
        String accessToken,
        String refreshToken,
        String tokenType,
        long expiresIn,
        UserResponse user
) {
    public record UserResponse(Long id, String fullName, String phone, String email, Role role) {
    }
}
