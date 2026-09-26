package com.ttcs.tenant.user;

import jakarta.persistence.*;
import java.time.Instant;

@Entity
@Table(name = "users", uniqueConstraints = {
        @UniqueConstraint(name = "uk_users_phone", columnNames = "phone"),
        @UniqueConstraint(name = "uk_users_email", columnNames = "email")
})
public class User {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "full_name", nullable = false, length = 100)
    private String fullName;

    @Column(nullable = false, length = 10)
    private String phone;

    @Column(nullable = false, length = 254)
    private String email;

    @Column(name = "password_hash", nullable = false, length = 255)
    private String passwordHash;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 30)
    private Role role;

    /** Số lần đăng nhập sai liên tiếp (S1-02). */
    @Column(name = "so_lan_sai", nullable = false)
    private int soLanSai = 0;

    /** Thời điểm lần sai gần nhất — dùng để reset nếu qua 15 phút. */
    @Column(name = "lan_sai_cuoi")
    private Instant lanSaiCuoi;

    /** Tài khoản bị khóa cho đến thời điểm này (null = không bị khóa). */
    @Column(name = "khoa_den")
    private Instant khoaDen;

    /** Thời điểm đăng xuất gần nhất — dùng để vô hiệu hóa access token cũ. */
    @Column(name = "thoi_diem_dang_xuat")
    private Instant thoiDiemDangXuat;

    protected User() {
    }

    public User(String fullName, String phone, String email, String passwordHash, Role role) {
        this.fullName = fullName;
        this.phone = phone;
        this.email = email;
        this.passwordHash = passwordHash;
        this.role = role;
    }

    // ── Getters ──────────────────────────────────────────────────────────────
    public Long getId() { return id; }
    public String getFullName() { return fullName; }
    public String getPhone() { return phone; }
    public String getEmail() { return email; }
    public String getPasswordHash() { return passwordHash; }
    public Role getRole() { return role; }
    public int getSoLanSai() { return soLanSai; }
    public Instant getLanSaiCuoi() { return lanSaiCuoi; }
    public Instant getKhoaDen() { return khoaDen; }
    public Instant getThoiDiemDangXuat() { return thoiDiemDangXuat; }

    // ── Setters ───────────────────────────────────────────────────────────────
    public void setSoLanSai(int soLanSai) { this.soLanSai = soLanSai; }
    public void setLanSaiCuoi(Instant lanSaiCuoi) { this.lanSaiCuoi = lanSaiCuoi; }
    public void setKhoaDen(Instant khoaDen) { this.khoaDen = khoaDen; }
    public void setThoiDiemDangXuat(Instant thoiDiemDangXuat) { this.thoiDiemDangXuat = thoiDiemDangXuat; }

    // ── Business helpers ──────────────────────────────────────────────────────

    /** Kiểm tra tài khoản có đang trong thời gian bị tạm khóa không. */
    public boolean isLocked() {
        return khoaDen != null && khoaDen.isAfter(Instant.now());
    }

    /** Số giây còn lại bị khóa (0 nếu không bị khóa). */
    public long getRemainingLockSeconds() {
        if (!isLocked()) return 0;
        return Math.max(0, khoaDen.getEpochSecond() - Instant.now().getEpochSecond());
    }

    /**
     * Ghi nhận một lần đăng nhập sai.
     * Nếu đạt 5 lần trong vòng 15 phút → khóa 15 phút.
     */
    public void recordLoginFailure() {
        Instant now = Instant.now();
        if (lanSaiCuoi != null && now.getEpochSecond() - lanSaiCuoi.getEpochSecond() > 15 * 60) {
            soLanSai = 1;
        } else {
            soLanSai++;
        }
        lanSaiCuoi = now;
        if (soLanSai >= 5) {
            khoaDen = now.plusSeconds(15 * 60);
        }
    }

    /** Đặt lại số lần sai khi đăng nhập thành công. */
    public void resetLoginFailures() {
        soLanSai = 0;
        khoaDen = null;
        lanSaiCuoi = null;
    }
}
