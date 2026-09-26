package com.ttcs.tenant.auth;

import com.fasterxml.jackson.annotation.JsonProperty;

public record TokenRefreshResponse(
        @JsonProperty("access_token")  String accessToken,
        @JsonProperty("token_type")    String tokenType,
        @JsonProperty("expires_in")    long expiresIn
) {}
