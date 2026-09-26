package com.ttcs.tenant.auth;

import com.ttcs.tenant.user.Role;
import com.ttcs.tenant.user.User;
import com.ttcs.tenant.user.UserRepository;
import com.ttcs.tenant.error.DuplicateFieldException;
import com.ttcs.tenant.error.InvalidCredentialsException;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Locale;
import java.util.LinkedHashMap;
import java.util.Map;

@Service
public class AuthService {
    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;
    private final JwtService jwtService;

    public AuthService(UserRepository userRepository, PasswordEncoder passwordEncoder, JwtService jwtService) {
        this.userRepository = userRepository;
        this.passwordEncoder = passwordEncoder;
        this.jwtService = jwtService;
    }

    @Transactional
    public RegisterResponse register(RegisterRequest request) {
        String email = request.email().trim().toLowerCase(Locale.ROOT);
        Map<String, String> duplicateFields = new LinkedHashMap<>();
        if (userRepository.existsByPhone(request.phone().trim())) {
            duplicateFields.put("phone", "Số điện thoại này đã được sử dụng.");
        }
        if (userRepository.existsByEmailIgnoreCase(email)) {
            duplicateFields.put("email", "Email này đã được sử dụng.");
        }
        if (!duplicateFields.isEmpty()) {
            throw new DuplicateFieldException(duplicateFields);
        }

        User user = new User(
                request.fullName().trim(),
                request.phone().trim(),
                email,
                passwordEncoder.encode(request.password()),
                Role.TENANT
        );
        User savedUser = userRepository.save(user);
        return new RegisterResponse(
                jwtService.createAccessToken(savedUser),
                jwtService.createRefreshToken(savedUser),
                "Bearer",
                jwtService.getAccessTokenSeconds(),
                new RegisterResponse.UserResponse(
                        savedUser.getId(), savedUser.getFullName(), savedUser.getPhone(), savedUser.getEmail(), savedUser.getRole()
                )
        );
    }

    @Transactional(readOnly = true)
    public RegisterResponse login(LoginRequest request) {
        String identifier = request.identifier().trim();
        User user = identifier.contains("@")
                ? userRepository.findByEmailIgnoreCase(identifier).orElse(null)
                : userRepository.findByPhone(identifier).orElse(null);
        if (user == null || !passwordEncoder.matches(request.password(), user.getPasswordHash())) {
            throw new InvalidCredentialsException();
        }

        return new RegisterResponse(
                jwtService.createAccessToken(user),
                jwtService.createRefreshToken(user),
                "Bearer",
                jwtService.getAccessTokenSeconds(),
                new RegisterResponse.UserResponse(user.getId(), user.getFullName(), user.getPhone(), user.getEmail(), user.getRole())
        );
    }
}
