package com.ttcs.tenant.auth;

import com.ttcs.tenant.user.Role;
import com.ttcs.tenant.user.User;
import com.ttcs.tenant.user.UserRepository;
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
}
