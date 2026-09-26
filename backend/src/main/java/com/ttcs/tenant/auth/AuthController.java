package com.ttcs.tenant.auth;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/auth")
public class AuthController {
    private final AuthService authService;

    public AuthController(AuthService authService) {
        this.authService = authService;
    }

    @PostMapping("/register")
    @ResponseStatus(HttpStatus.CREATED)
    public RegisterResponse register(@Valid @RequestBody RegisterRequest request) {
        return authService.register(request);
    }

    @PostMapping("/login")
    public RegisterResponse login(@Valid @RequestBody LoginRequest request) {
        return authService.login(request);
    }

    /**
     * POST /api/auth/logout
     * Vô hiệu hóa access token và thu hồi toàn bộ refresh token của user.
     * Gửi: Authorization: Bearer <accessToken> + body { "userId": ... }
     */
    @PostMapping("/logout")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void logout(HttpServletRequest request, @RequestBody(required = false) LogoutRequest body) {
        String accessToken = extractBearerToken(request);
        Long userId = (body != null) ? body.userId() : null;
        authService.logout(accessToken, userId);
    }

    /**
     * POST /api/auth/refresh
     * Đổi refresh token lấy access token mới.
     * Body: { "refreshToken": "..." }
     */
    @PostMapping("/refresh")
    public TokenRefreshResponse refresh(@RequestBody RefreshRequest request) {
        return authService.refresh(request.refreshToken());
    }

    // ── Helpers ───────────────────────────────────────────────────────────────

    private String extractBearerToken(HttpServletRequest request) {
        String header = request.getHeader("Authorization");
        if (header != null && header.startsWith("Bearer ")) {
            return header.substring(7).trim();
        }
        return null;
    }
}
