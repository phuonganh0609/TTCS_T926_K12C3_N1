package com.ttcs.tenant.profile;

import com.ttcs.tenant.user.User;
import jakarta.persistence.*;
import java.time.LocalDate;
import java.time.Instant;

/**
 * Hồ sơ cá nhân khách thuê (S1-06).
 * Port từ model KhachThue (Django/main).
 */
@Entity
@Table(name = "khach_thue")
public class KhachThue {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @OneToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "user_id", nullable = false, unique = true)
    private User user;

    @Column(name = "ho_ten", nullable = false, length = 100)
    private String hoTen;

    @Column(name = "ngay_sinh", nullable = false)
    private LocalDate ngaySinh;

    @Column(name = "so_giay_to", nullable = false, length = 12)
    private String soGiayTo;

    @Column(name = "que_quan", nullable = false, length = 255)
    private String queQuan;

    @Column(name = "nghe_nghiep", nullable = false, length = 150)
    private String ngheNghiep;

    @Column(name = "anh_giay_to_truoc", length = 255)
    private String anhGiayToTruoc;

    @Column(name = "anh_giay_to_sau", length = 255)
    private String anhGiayToSau;

    @Column(name = "ngay_tao", nullable = false, updatable = false)
    private Instant ngayTao;

    protected KhachThue() {}

    public KhachThue(User user, String hoTen, LocalDate ngaySinh, String soGiayTo, String queQuan, String ngheNghiep) {
        this.user = user;
        this.hoTen = hoTen;
        this.ngaySinh = ngaySinh;
        this.soGiayTo = soGiayTo;
        this.queQuan = queQuan;
        this.ngheNghiep = ngheNghiep;
        this.ngayTao = Instant.now();
    }

    // Getters & Setters
    public Long getId() { return id; }
    public User getUser() { return user; }
    public String getHoTen() { return hoTen; }
    public void setHoTen(String hoTen) { this.hoTen = hoTen; }
    public LocalDate getNgaySinh() { return ngaySinh; }
    public void setNgaySinh(LocalDate ngaySinh) { this.ngaySinh = ngaySinh; }
    public String getSoGiayTo() { return soGiayTo; }
    public void setSoGiayTo(String soGiayTo) { this.soGiayTo = soGiayTo; }
    public String getQueQuan() { return queQuan; }
    public void setQueQuan(String queQuan) { this.queQuan = queQuan; }
    public String getNgheNghiep() { return ngheNghiep; }
    public void setNgheNghiep(String ngheNghiep) { this.ngheNghiep = ngheNghiep; }
    public String getAnhGiayToTruoc() { return anhGiayToTruoc; }
    public void setAnhGiayToTruoc(String anhGiayToTruoc) { this.anhGiayToTruoc = anhGiayToTruoc; }
    public String getAnhGiayToSau() { return anhGiayToSau; }
    public void setAnhGiayToSau(String anhGiayToSau) { this.anhGiayToSau = anhGiayToSau; }
    public Instant getNgayTao() { return ngayTao; }
}
