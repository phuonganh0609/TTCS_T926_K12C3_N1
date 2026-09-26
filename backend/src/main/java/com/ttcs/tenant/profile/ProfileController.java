package com.ttcs.tenant.profile;

import com.ttcs.tenant.auth.JwtService;
import com.ttcs.tenant.user.User;
import com.ttcs.tenant.user.UserRepository;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.time.LocalDate;

@RestController
@RequestMapping("/api/profile")
public class ProfileController {

    private final ProfileService profileService;
    private final JwtService jwtService;
    private final UserRepository userRepository;

    public ProfileController(ProfileService profileService, JwtService jwtService, UserRepository userRepository) {
        this.profileService = profileService;
        this.jwtService = jwtService;
        this.userRepository = userRepository;
    }

    /**
     * GET /api/profile/me
     * Lấy thông tin hồ sơ cá nhân khách thuê hiện tại.
     */
    @GetMapping("/me")
    public ResponseEntity<ProfileDTO.ProfileResponse> getMyProfile(HttpServletRequest request) {
        User currentUser = authenticate(request);
        return profileService.getProfileByUserId(currentUser.getId())
                .map(ResponseEntity::ok)
                .orElseGet(() -> ResponseEntity.notFound().build());
    }

    /**
     * POST /api/profile/me (multipart/form-data)
     * Tạo hoặc cập nhật hồ sơ cá nhân và upload ảnh giấy tờ.
     */
    @PostMapping(value = "/me", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<ProfileDTO.ProfileResponse> saveOrUpdateMyProfile(
            HttpServletRequest request,
            @RequestParam("hoTen") String hoTen,
            @RequestParam("ngaySinh") String ngaySinhStr,
            @RequestParam(value = "soGiayTo", required = false) String soGiayTo,
            @RequestParam("queQuan") String queQuan,
            @RequestParam("ngheNghiep") String ngheNghiep,
            @RequestParam(value = "anhGiayToTruoc", required = false) MultipartFile anhTruoc,
            @RequestParam(value = "anhGiayToSau", required = false) MultipartFile anhSau
    ) {
        User currentUser = authenticate(request);
        LocalDate ngaySinh = LocalDate.parse(ngaySinhStr);

        ProfileDTO.ProfileRequest profileReq = new ProfileDTO.ProfileRequest(
                hoTen, ngaySinh, soGiayTo, queQuan, ngheNghiep
        );

        ProfileDTO.ProfileResponse response = profileService.saveOrUpdateProfile(
                currentUser.getId(), profileReq, anhTruoc, anhSau
        );

        return ResponseEntity.ok(response);
    }

    // ── Authentication Helper ─────────────────────────────────────────────────

    private User authenticate(HttpServletRequest request) {
        String authHeader = request.getHeader("Authorization");
        if (authHeader == null || !authHeader.startsWith("Bearer ")) {
            throw new IllegalArgumentException("Vui lòng đăng nhập để thực hiện thao tác này.");
        }
        String token = authHeader.substring(7).trim();
        long userId = jwtService.verifyAccessToken(token, null);
        if (userId <= 0) {
            throw new IllegalArgumentException("Phiên đăng nhập không hợp lệ hoặc đã hết hạn.");
        }
        return userRepository.findById(userId)
                .orElseThrow(() -> new IllegalArgumentException("Tài khoản người dùng không tồn tại."));
    }
}
