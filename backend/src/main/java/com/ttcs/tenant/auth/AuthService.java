package com.ttcs.tenant.auth;

import com.ttcs.tenant.error.InvalidCredentialsException;
import com.ttcs.tenant.user.Role;
import com.ttcs.tenant.user.User;
import com.ttcs.tenant.user.UserRepository;
import com.ttcs.tenant.error.DuplicateFieldException;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Instant;
import java.util.Locale;
import java.util.LinkedHashMap;
import java.util.Map;

@Service
public class AuthService {
    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;
    private final JwtService jwtService;

    public AuthService(UserRepository userRepository, PasswordEncoder passwordEncoder, JwtService jwtService) {
        this.userRepository = userRepository;
        this.passwordEncoder = passwordEncoder;
        this.jwtService = jwtService;
    }

    @Transactional
    public RegisterResponse register(RegisterRequest request) {
        String email = request.email().trim().toLowerCase(Locale.ROOT);
        Map<String, String> duplicateFields = new LinkedHashMap<>();
        if (userRepository.existsByPhone(request.phone().trim())) {
            duplicateFields.put("phone", "Số điện thoại này đã được sử dụng.");
        }
        if (userRepository.existsByEmailIgnoreCase(email)) {
            duplicateFields.put("email", "Email này đã được sử dụng.");
        }
        if (!duplicateFields.isEmpty()) {
            throw new DuplicateFieldException(duplicateFields);
        }

        User user = new User(
                request.fullName().trim(),
                request.phone().trim(),
                email,
                passwordEncoder.encode(request.password()),
                Role.TENANT
        );
        User savedUser = userRepository.save(user);
        return buildResponse(savedUser);
    }

    @Transactional(noRollbackFor = {InvalidCredentialsException.class, AccountLockedException.class})
    public RegisterResponse login(LoginRequest request) {
        String identifier = request.identifier().trim();
        User user = identifier.contains("@")
                ? userRepository.findByEmailIgnoreCase(identifier).orElse(null)
                : userRepository.findByPhone(identifier).orElse(null);

        if (user == null) {
            throw new InvalidCredentialsException();
        }

        // Kiểm tra tài khoản bị khóa (S1-02)
        if (user.isLocked()) {
            long secs = user.getRemainingLockSeconds();
            throw new AccountLockedException(
                    "Tài khoản tạm thời bị khóa do nhập sai mật khẩu 5 lần. Vui lòng thử lại sau " + secs + " giây.", secs);
        }

        if (!passwordEncoder.matches(request.password(), user.getPasswordHash())) {
            user.recordLoginFailure();
            userRepository.save(user);
            if (user.isLocked()) {
                throw new AccountLockedException(
                        "Tài khoản đã bị tạm khóa 15 phút do nhập sai mật khẩu 5 lần liên tiếp.",
                        user.getRemainingLockSeconds());
            }
            throw new InvalidCredentialsException();
        }

        // Đăng nhập thành công → reset số lần sai
        user.resetLoginFailures();
        userRepository.save(user);
        return buildResponse(user);
    }

    /**
     * Đăng xuất: vô hiệu hóa access token, thu hồi mọi refresh token của user.
     * Port từ dang_xuat_view / revoke_tokens (Django/main).
     */
    @Transactional
    public void logout(String accessToken, Long userId) {
        if (accessToken != null) {
            jwtService.revokeAccessToken(accessToken);
        }
        if (userId != null) {
            jwtService.revokeAllRefreshTokens(userId);
            userRepository.findById(userId).ifPresent(u -> {
                u.setThoiDiemDangXuat(Instant.now());
                userRepository.save(u);
            });
        }
    }

    /**
     * Làm mới access token từ refresh token còn hạn.
     * Port từ api_refresh_view (Django/main).
     */
    @Transactional
    public TokenRefreshResponse refresh(String refreshToken) {
        String newAccessToken = jwtService.rotateRefreshToken(refreshToken);
        return new TokenRefreshResponse(newAccessToken, "Bearer", jwtService.getAccessTokenSeconds());
    }

    // ── Private helpers ───────────────────────────────────────────────────────

    private RegisterResponse buildResponse(User user) {
        return new RegisterResponse(
                jwtService.createAccessToken(user),
                jwtService.createRefreshToken(user),
                "Bearer",
                jwtService.getAccessTokenSeconds(),
                new RegisterResponse.UserResponse(
                        user.getId(), user.getFullName(), user.getPhone(), user.getEmail(), user.getRole()
                )
        );
    }
}
