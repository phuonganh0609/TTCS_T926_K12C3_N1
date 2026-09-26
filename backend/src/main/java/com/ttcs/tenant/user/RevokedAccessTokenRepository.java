package com.ttcs.tenant.user;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;

import java.time.Instant;

public interface RevokedAccessTokenRepository extends JpaRepository<RevokedAccessToken, String> {

    boolean existsByJti(String jti);

    /** Dọn dẹp blacklist token đã hết hạn. */
    @Modifying
    @Query("DELETE FROM RevokedAccessToken t WHERE t.ngayHetHan < :before")
    int deleteExpiredBefore(Instant before);
}
