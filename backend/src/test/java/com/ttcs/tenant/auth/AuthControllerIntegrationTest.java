package com.ttcs.tenant.auth;

import com.ttcs.tenant.user.Role;
import com.ttcs.tenant.user.User;
import com.ttcs.tenant.user.UserRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;

import static org.hamcrest.Matchers.containsString;
import static org.hamcrest.Matchers.not;
import static org.hamcrest.Matchers.notNullValue;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
class AuthControllerIntegrationTest {
    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private UserRepository userRepository;

    @BeforeEach
    void clearUsers() {
      userRepository.deleteAll();
    }

    @Test
    void validRegistrationCreatesTenantAndReturnsTokens() throws Exception {
        String password = "StrongPass123";

        mockMvc.perform(post("/api/auth/register")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {
                                  "fullName": "Nguyen Van A",
                                  "phone": "0901234567",
                                  "email": "tenant@example.com",
                                  "password": "%s"
                                }
                                """.formatted(password)))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.accessToken", notNullValue()))
                .andExpect(jsonPath("$.refreshToken", notNullValue()))
                .andExpect(jsonPath("$.user.role").value(Role.TENANT.name()));

        User user = userRepository.findAll().get(0);
        org.junit.jupiter.api.Assertions.assertNotEquals(password, user.getPasswordHash());
        org.junit.jupiter.api.Assertions.assertTrue(user.getPasswordHash().startsWith("$2"));
    }

    @Test
    void invalidPhoneAndWeakPasswordReturnFieldErrors() throws Exception {
        mockMvc.perform(post("/api/auth/register")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {
                                  "fullName": "Invalid User",
                                  "phone": "1234567890",
                                  "email": "invalid@example.com",
                                  "password": "12345678"
                                }
                                """))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.code").value("VALIDATION_ERROR"))
                .andExpect(jsonPath("$.fieldErrors.phone", containsString("Số điện thoại")))
                .andExpect(jsonPath("$.fieldErrors.password", containsString("chữ cái")));
    }

    @Test
    void validPasswordIsNeverReturnedInResponse() throws Exception {
        mockMvc.perform(post("/api/auth/register")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {
                                  "fullName": "Secure User",
                                  "phone": "0912345678",
                                  "email": "secure@example.com",
                                  "password": "SecretPass123"
                                }
                                """))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$", not(containsString("SecretPass123"))));
    }

    @Test
    void duplicatePhoneReturnsConflictForPhoneField() throws Exception {
        userRepository.save(new User("Existing Phone", "0901111111", "phone@example.com", "hash", Role.TENANT));

        mockMvc.perform(post("/api/auth/register")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {
                                  "fullName": "New Phone",
                                  "phone": "0901111111",
                                  "email": "new-phone@example.com",
                                  "password": "StrongPass123"
                                }
                                """))
                .andExpect(status().isConflict())
                .andExpect(jsonPath("$.code").value("DUPLICATE_FIELD"))
                .andExpect(jsonPath("$.fieldErrors.phone", containsString("Số điện thoại")))
                .andExpect(jsonPath("$.fieldErrors.email").doesNotExist());
    }

    @Test
    void duplicateEmailReturnsConflictForEmailField() throws Exception {
        userRepository.save(new User("Existing Email", "0902222222", "email@example.com", "hash", Role.TENANT));

        mockMvc.perform(post("/api/auth/register")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {
                                  "fullName": "New Email",
                                  "phone": "0903333333",
                                  "email": "EMAIL@example.com",
                                  "password": "StrongPass123"
                                }
                                """))
                .andExpect(status().isConflict())
                .andExpect(jsonPath("$.code").value("DUPLICATE_FIELD"))
                .andExpect(jsonPath("$.fieldErrors.email", containsString("Email")))
                .andExpect(jsonPath("$.fieldErrors.phone").doesNotExist());
    }

    @Test
    void duplicatePhoneAndEmailReturnBothFieldErrorsWithoutCreatingUser() throws Exception {
        userRepository.save(new User("Existing Both", "0904444444", "both@example.com", "hash", Role.TENANT));

        mockMvc.perform(post("/api/auth/register")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {
                                  "fullName": "New Both",
                                  "phone": "0904444444",
                                  "email": "both@example.com",
                                  "password": "StrongPass123"
                                }
                                """))
                .andExpect(status().isConflict())
                .andExpect(jsonPath("$.code").value("DUPLICATE_FIELD"))
                .andExpect(jsonPath("$.fieldErrors.phone", containsString("Số điện thoại")))
                .andExpect(jsonPath("$.fieldErrors.email", containsString("Email")));

        org.junit.jupiter.api.Assertions.assertEquals(1, userRepository.count());
    }
}
