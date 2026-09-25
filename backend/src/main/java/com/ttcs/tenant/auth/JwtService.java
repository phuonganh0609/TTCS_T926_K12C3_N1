package com.ttcs.tenant.auth;

import com.ttcs.tenant.user.User;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.Date;
import java.util.UUID;

@Service
public class JwtService {
    private final SecretKey signingKey;
    private final long accessTokenMinutes;
    private final long refreshTokenDays;

    public JwtService(
            @Value("${app.jwt.secret}") String secret,
            @Value("${app.jwt.access-token-minutes:30}") long accessTokenMinutes,
            @Value("${app.jwt.refresh-token-days:7}") long refreshTokenDays
    ) {
        this.signingKey = Keys.hmacShaKeyFor(secret.getBytes(StandardCharsets.UTF_8));
        this.accessTokenMinutes = accessTokenMinutes;
        this.refreshTokenDays = refreshTokenDays;
    }

    public String createAccessToken(User user) {
        return createToken(user, "access", accessTokenMinutes * 60);
    }

    public String createRefreshToken(User user) {
        return createToken(user, "refresh", refreshTokenDays * 24 * 60 * 60);
    }

    public long getAccessTokenSeconds() {
        return accessTokenMinutes * 60;
    }

    private String createToken(User user, String tokenType, long lifetimeSeconds) {
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
