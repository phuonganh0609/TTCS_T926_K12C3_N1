package com.ttcs.tenant.user;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;

import java.time.Instant;
import java.util.Optional;

public interface RefreshTokenRepository extends JpaRepository<RefreshToken, Long> {

    Optional<RefreshToken> findByTokenId(String tokenId);

    /** Thu hồi toàn bộ phiên chưa hết hạn của một user (khi đăng xuất). */
    @Modifying
    @Query("UPDATE RefreshToken r SET r.dahuHoi = true WHERE r.user.id = :userId AND r.dahuHoi = false")
    int revokeAllByUserId(Long userId);

    /** Dọn dẹp token hết hạn (có thể chạy định kỳ). */
    @Modifying
    @Query("DELETE FROM RefreshToken r WHERE r.ngayHetHan < :before")
    int deleteExpiredBefore(Instant before);
}
