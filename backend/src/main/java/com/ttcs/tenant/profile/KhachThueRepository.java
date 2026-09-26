package com.ttcs.tenant.profile;

import org.springframework.data.jpa.repository.JpaRepository;
import java.util.Optional;

public interface KhachThueRepository extends JpaRepository<KhachThue, Long> {
    Optional<KhachThue> findByUserId(Long userId);
    boolean existsByUserId(Long userId);
}
