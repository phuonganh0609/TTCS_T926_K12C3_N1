package com.ttcs.tenant.user;

import jakarta.persistence.*;
import java.time.Instant;

/**
 * Danh sách access token bị thu hồi sau khi đăng xuất (blacklist).
 * Port từ model ThuHoiAccessToken (Django/main).
 */
@Entity
@Table(name = "thu_hoi_access_token", indexes = @Index(name = "idx_tat_jti", columnList = "jti", unique = true))
public class RevokedAccessToken {

    @Id
    @Column(name = "jti", nullable = false, length = 64)
    private String jti;

    @Column(name = "ngay_het_han", nullable = false)
    private Instant ngayHetHan;

    @Column(name = "ngay_thu_hoi", nullable = false, updatable = false)
    private Instant ngayThuHoi;

    protected RevokedAccessToken() {}

    public RevokedAccessToken(String jti, Instant ngayHetHan) {
        this.jti = jti;
        this.ngayHetHan = ngayHetHan;
        this.ngayThuHoi = Instant.now();
    }

    public String getJti() { return jti; }
    public Instant getNgayHetHan() { return ngayHetHan; }
    public Instant getNgayThuHoi() { return ngayThuHoi; }
}
