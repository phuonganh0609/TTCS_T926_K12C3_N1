package com.ttcs.tenant.auth;

import com.ttcs.tenant.user.RefreshToken;
import com.ttcs.tenant.user.RefreshTokenRepository;
import com.ttcs.tenant.user.RevokedAccessToken;
import com.ttcs.tenant.user.RevokedAccessTokenRepository;
import com.ttcs.tenant.user.User;
import io.jsonwebtoken.Claims;
import io.jsonwebtoken.JwtException;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.Date;
import java.util.Optional;
import java.util.UUID;

@Service
public class JwtService {
    private final SecretKey signingKey;
    private final long accessTokenMinutes;
    private final long refreshTokenDays;
    private final RefreshTokenRepository refreshTokenRepository;
    private final RevokedAccessTokenRepository revokedRepository;

    public JwtService(
            @Value("${app.jwt.secret}") String secret,
            @Value("${app.jwt.access-token-minutes:30}") long accessTokenMinutes,
            @Value("${app.jwt.refresh-token-days:7}") long refreshTokenDays,
            RefreshTokenRepository refreshTokenRepository,
            RevokedAccessTokenRepository revokedRepository
    ) {
        this.signingKey = Keys.hmacShaKeyFor(secret.getBytes(StandardCharsets.UTF_8));
        this.accessTokenMinutes = accessTokenMinutes;
        this.refreshTokenDays = refreshTokenDays;
        this.refreshTokenRepository = refreshTokenRepository;
        this.revokedRepository = revokedRepository;
    }

    // ── Token generation ──────────────────────────────────────────────────────

    public String createAccessToken(User user) {
        return buildToken(user, "access", accessTokenMinutes * 60);
    }

    /**
     * Tạo refresh token VÀ lưu vào DB (PhienDangNhap).
     */
    @Transactional
    public String createRefreshToken(User user) {
        long lifetimeSecs = refreshTokenDays * 24 * 60 * 60;
        Instant now = Instant.now();
        String jti = UUID.randomUUID().toString();

        String token = Jwts.builder()
                .subject(user.getId().toString())
                .id(jti)
                .claim("tokenType", "refresh")
                .issuedAt(Date.from(now))
                .expiration(Date.from(now.plusSeconds(lifetimeSecs)))
                .signWith(signingKey)
                .compact();

        refreshTokenRepository.save(new RefreshToken(user, jti, now.plusSeconds(lifetimeSecs)));
        return token;
    }

    public long getAccessTokenSeconds() { return accessTokenMinutes * 60; }

    // ── Token verification ────────────────────────────────────────────────────

    /**
     * Parse claims từ bất kỳ token nào; trả Optional.empty() nếu không hợp lệ.
     */
    public Optional<Claims> parseClaims(String token) {
        try {
            return Optional.of(Jwts.parser()
                    .verifyWith(signingKey)
                    .build()
                    .parseSignedClaims(token)
                    .getPayload());
        } catch (JwtException | IllegalArgumentException e) {
            return Optional.empty();
        }
    }

    /**
     * Xác minh access token: hợp lệ, đúng type, không bị blacklist, phát sau logout.
     * Trả về user ID hoặc -1 nếu không hợp lệ.
     */
    public long verifyAccessToken(String token, User user) {
        return parseClaims(token).map(claims -> {
            if (!"access".equals(claims.get("tokenType"))) return -1L;
            String jti = claims.getId();
            if (revokedRepository.existsByJti(jti)) return -1L;
            // Token phát trước lần logout gần nhất → không hợp lệ
            if (user != null && user.getThoiDiemDangXuat() != null) {
                Instant iat = claims.getIssuedAt().toInstant();
                if (!iat.isAfter(user.getThoiDiemDangXuat())) return -1L;
            }
            return Long.parseLong(claims.getSubject());
        }).orElse(-1L);
    }

    // ── Refresh rotation ──────────────────────────────────────────────────────

    /**
     * Đổi refresh token còn hạn lấy access token mới.
     * Port từ hàm refresh_access_token (Django/tokens.py).
     */
    @Transactional
    public String rotateRefreshToken(String refreshTokenString) {
        Claims claims = parseClaims(refreshTokenString)
                .orElseThrow(() -> new InvalidTokenException("Refresh token không hợp lệ hoặc đã hết hạn."));

        if (!"refresh".equals(claims.get("tokenType"))) {
            throw new InvalidTokenException("Token không phải refresh token.");
        }

        String jti = claims.getId();
        RefreshToken storedToken = refreshTokenRepository.findByTokenId(jti)
                .orElseThrow(() -> new InvalidTokenException("Phiên đăng nhập không tồn tại."));

        if (!storedToken.isValid()) {
            throw new InvalidTokenException("Phiên đăng nhập đã hết hạn hoặc đã bị vô hiệu hóa.");
        }

        return createAccessToken(storedToken.getUser());
    }

    // ── Revocation ────────────────────────────────────────────────────────────

    /**
     * Thu hồi access token (thêm jti vào blacklist).
     */
    @Transactional
    public void revokeAccessToken(String token) {
        parseClaims(token).ifPresent(claims -> {
            String jti = claims.getId();
            Instant exp = claims.getExpiration().toInstant();
            if (!revokedRepository.existsByJti(jti)) {
                revokedRepository.save(new RevokedAccessToken(jti, exp));
            }
        });
    }

    /**
     * Thu hồi tất cả refresh token của user (khi đăng xuất).
     */
    @Transactional
    public void revokeAllRefreshTokens(Long userId) {
        refreshTokenRepository.revokeAllByUserId(userId);
    }

    // ── Private helpers ───────────────────────────────────────────────────────

    private String buildToken(User user, String tokenType, long lifetimeSeconds) {
        Instant now = Instant.now();
        return Jwts.builder()
                .subject(user.getId().toString())
                .id(UUID.randomUUID().toString())
                .claim("email", user.getEmail())
                .claim("role", user.getRole().name())
                .claim("tokenType", tokenType)
                .issuedAt(Date.from(now))
                .expiration(Date.from(now.plusSeconds(lifetimeSeconds)))
                .signWith(signingKey)
                .compact();
    }
}
