package com.ttcs.tenant.user;

import jakarta.persistence.*;
import java.time.Instant;

/**
 * Phiên đăng nhập — lưu refresh token vào DB để quản lý và thu hồi (S1-02).
 * Port từ model PhienDangNhap (Django/main).
 */
@Entity
@Table(name = "phien_dang_nhap", indexes = @Index(name = "idx_pdn_token_id", columnList = "token_id", unique = true))
public class RefreshToken {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    /** UUID của JWT refresh token — chính là "jti" trong payload. */
    @Column(name = "token_id", nullable = false, unique = true, length = 64)
    private String tokenId;

    @Column(name = "ngay_tao", nullable = false, updatable = false)
    private Instant ngayTao;

    @Column(name = "ngay_het_han", nullable = false)
    private Instant ngayHetHan;

    @Column(name = "da_thu_hoi", nullable = false)
    private boolean dahuHoi = false;

    protected RefreshToken() {}

    public RefreshToken(User user, String tokenId, Instant ngayHetHan) {
        this.user = user;
        this.tokenId = tokenId;
        this.ngayTao = Instant.now();
        this.ngayHetHan = ngayHetHan;
    }

    public boolean isValid() {
        return !dahuHoi && ngayHetHan.isAfter(Instant.now());
    }

    public void revoke() { this.dahuHoi = true; }

    // Getters
    public Long getId() { return id; }
    public User getUser() { return user; }
    public String getTokenId() { return tokenId; }
    public Instant getNgayTao() { return ngayTao; }
    public Instant getNgayHetHan() { return ngayHetHan; }
    public boolean isDahuHoi() { return dahuHoi; }
}
