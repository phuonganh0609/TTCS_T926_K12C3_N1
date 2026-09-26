package com.ttcs.tenant.auth;

import com.ttcs.tenant.error.DuplicateFieldException;
import com.ttcs.tenant.user.Role;
import com.ttcs.tenant.user.User;
import com.ttcs.tenant.user.UserRepository;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.security.crypto.password.PasswordEncoder;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class AuthServiceUnitTest {
    @Mock
    private UserRepository userRepository;

    @Mock
    private PasswordEncoder passwordEncoder;

    @Mock
    private JwtService jwtService;

    @InjectMocks
    private AuthService authService;

    @Test
    void registerHashesPasswordAndAssignsTenantRole() {
        RegisterRequest request = new RegisterRequest(
                "  Nguyen Van A  ", "0901234567", "USER@EXAMPLE.COM", "StrongPass123"
        );
        User savedUser = new User("Nguyen Van A", "0901234567", "user@example.com", "bcrypt-hash", Role.TENANT);

        when(userRepository.existsByPhone("0901234567")).thenReturn(false);
        when(userRepository.existsByEmailIgnoreCase("user@example.com")).thenReturn(false);
        when(passwordEncoder.encode("StrongPass123")).thenReturn("bcrypt-hash");
        when(userRepository.save(any(User.class))).thenReturn(savedUser);
        when(jwtService.createAccessToken(savedUser)).thenReturn("access-token");
        when(jwtService.createRefreshToken(savedUser)).thenReturn("refresh-token");
        when(jwtService.getAccessTokenSeconds()).thenReturn(1800L);

        RegisterResponse response = authService.register(request);

        ArgumentCaptor<User> userCaptor = ArgumentCaptor.forClass(User.class);
        verify(userRepository).save(userCaptor.capture());
        assertEquals("Nguyen Van A", userCaptor.getValue().getFullName());
        assertEquals("user@example.com", userCaptor.getValue().getEmail());
        assertEquals("bcrypt-hash", userCaptor.getValue().getPasswordHash());
        assertEquals(Role.TENANT, userCaptor.getValue().getRole());
        assertEquals("access-token", response.accessToken());
        assertEquals("refresh-token", response.refreshToken());
    }

    @Test
    void registerRejectsDuplicatePhoneBeforeSaving() {
        RegisterRequest request = new RegisterRequest(
                "Nguyen Van B", "0901234567", "new@example.com", "StrongPass123"
        );
        when(userRepository.existsByPhone("0901234567")).thenReturn(true);
        when(userRepository.existsByEmailIgnoreCase("new@example.com")).thenReturn(false);

        DuplicateFieldException exception = assertThrows(
                DuplicateFieldException.class,
                () -> authService.register(request)
        );

        assertEquals("Số điện thoại này đã được sử dụng.", exception.getFieldErrors().get("phone"));
        verify(userRepository, never()).save(any(User.class));
    }
}
