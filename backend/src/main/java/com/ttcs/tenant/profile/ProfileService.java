package com.ttcs.tenant.profile;

import com.ttcs.tenant.user.User;
import com.ttcs.tenant.user.UserRepository;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

import javax.imageio.ImageIO;
import java.awt.Graphics2D;
import java.awt.RenderingHints;
import java.awt.image.BufferedImage;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Optional;
import java.util.UUID;

@Service
public class ProfileService {

    private final KhachThueRepository khachThueRepository;
    private final UserRepository userRepository;
    private final Path uploadStoragePath;

    public ProfileService(
            KhachThueRepository khachThueRepository,
            UserRepository userRepository,
            @Value("${app.upload.dir:private_media/giay-to}") String uploadDir
    ) {
        this.khachThueRepository = khachThueRepository;
        this.userRepository = userRepository;
        this.uploadStoragePath = Paths.get(uploadDir).toAbsolutePath().normalize();
        try {
            Files.createDirectories(this.uploadStoragePath);
        } catch (IOException e) {
            throw new RuntimeException("Không thể khởi tạo thư mục lưu trữ ảnh giấy tờ.", e);
        }
    }

    // ── Get Profile ───────────────────────────────────────────────────────────

    @Transactional(readOnly = true)
    public Optional<ProfileDTO.ProfileResponse> getProfileByUserId(Long userId) {
        return khachThueRepository.findByUserId(userId).map(this::toResponse);
    }

    // ── Save or Update Profile ────────────────────────────────────────────────

    @Transactional
    public ProfileDTO.ProfileResponse saveOrUpdateProfile(
            Long userId,
            ProfileDTO.ProfileRequest request,
            MultipartFile anhTruoc,
            MultipartFile anhSau
    ) {
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new IllegalArgumentException("Người dùng không tồn tại."));

        // Validation
        validateProfileRequest(request);

        KhachThue profile = khachThueRepository.findByUserId(userId)
                .orElseGet(() -> new KhachThue(
                        user,
                        request.hoTen().trim(),
                        request.ngaySinh(),
                        request.soGiayTo().trim(),
                        request.queQuan().trim(),
                        request.ngheNghiep().trim()
                ));

        profile.setHoTen(request.hoTen().trim());
        profile.setNgaySinh(request.ngaySinh());
        if (request.soGiayTo() != null && !request.soGiayTo().isBlank()) {
            profile.setSoGiayTo(request.soGiayTo().trim());
        }
        profile.setQueQuan(request.queQuan().trim());
        profile.setNgheNghiep(request.ngheNghiep().trim());

        // Process images
        if (anhTruoc != null && !anhTruoc.isEmpty()) {
            String pathTruoc = saveAndProcessImage(anhTruoc, "truoc");
            profile.setAnhGiayToTruoc(pathTruoc);
        }

        if (anhSau != null && !anhSau.isEmpty()) {
            String pathSau = saveAndProcessImage(anhSau, "sau");
            profile.setAnhGiayToSau(pathSau);
        }

        KhachThue saved = khachThueRepository.save(profile);
        return toResponse(saved);
    }

    // ── Identity Masking ─────────────────────────────────────────────────────

    /**
     * Che số căn cước (S1-06): 9 số → *****6789, 12 số → ********6789.
     */
    public String maskIdentity(String number) {
        if (number == null || number.isBlank()) return "";
        int len = number.length();
        if (len <= 4) return number;
        return "*".repeat(len - 4) + number.substring(len - 4);
    }

    // ── Private Helpers ───────────────────────────────────────────────────────

    private void validateProfileRequest(ProfileDTO.ProfileRequest request) {
        if (request.hoTen() == null || request.hoTen().isBlank()) {
            throw new IllegalArgumentException("Họ tên là bắt buộc.");
        }
        if (request.ngaySinh() == null) {
            throw new IllegalArgumentException("Ngày sinh là bắt buộc.");
        }
        if (request.soGiayTo() != null && !request.soGiayTo().isBlank()) {
            String s = request.soGiayTo().trim();
            if (!s.matches("^(?:\\d{9}|\\d{12})$")) {
                throw new IllegalArgumentException("Số căn cước phải gồm 9 hoặc 12 chữ số.");
            }
        }
    }

    private String saveAndProcessImage(MultipartFile file, String prefix) {
        if (file.getSize() > 5 * 1024 * 1024) {
            throw new IllegalArgumentException("Mỗi ảnh không được vượt quá 5MB.");
        }
        String originalName = file.getOriginalFilename();
        String ext = (originalName != null && originalName.contains("."))
                ? originalName.substring(originalName.lastIndexOf(".")).toLowerCase()
                : ".jpg";

        if (!ext.equals(".jpg") && !ext.equals(".jpeg") && !ext.equals(".png")) {
            throw new IllegalArgumentException("Chỉ chấp nhận ảnh dạng JPG hoặc PNG.");
        }

        try {
            BufferedImage image = ImageIO.read(file.getInputStream());
            if (image == null) {
                throw new IllegalArgumentException("File tải lên không phải định dạng ảnh hợp lệ.");
            }

            // Resize nếu rộng hơn 1600px
            if (image.getWidth() > 1600) {
                int targetWidth = 1600;
                int targetHeight = (int) (((double) image.getHeight() / image.getWidth()) * targetWidth);
                BufferedImage resized = new BufferedImage(targetWidth, targetHeight, BufferedImage.TYPE_INT_RGB);
                Graphics2D g2d = resized.createGraphics();
                g2d.setRenderingHint(RenderingHints.KEY_INTERPOLATION, RenderingHints.VALUE_INTERPOLATION_BILINEAR);
                g2d.drawImage(image, 0, 0, targetWidth, targetHeight, null);
                g2d.dispose();
                image = resized;
            }

            String filename = prefix + "_" + UUID.randomUUID() + ext;
            Path targetPath = uploadStoragePath.resolve(filename);
            String formatName = ext.equals(".png") ? "png" : "jpg";
            ImageIO.write(image, formatName, targetPath.toFile());

            return filename;
        } catch (IOException e) {
            throw new RuntimeException("Không thể xử lý và lưu ảnh giấy tờ.", e);
        }
    }

    private ProfileDTO.ProfileResponse toResponse(KhachThue khachThue) {
        return new ProfileDTO.ProfileResponse(
                khachThue.getId(),
                khachThue.getUser().getId(),
                khachThue.getHoTen(),
                khachThue.getNgaySinh(),
                maskIdentity(khachThue.getSoGiayTo()),
                khachThue.getQueQuan(),
                khachThue.getNgheNghiep(),
                khachThue.getAnhGiayToTruoc() != null,
                khachThue.getAnhGiayToSau() != null
        );
    }
}
