package com.ttcs.tenant.error;

import java.util.Map;

public class DuplicateFieldException extends RuntimeException {
    private final Map<String, String> fieldErrors;

    public DuplicateFieldException(Map<String, String> fieldErrors) {
        super("Email hoặc số điện thoại đã được sử dụng.");
        this.fieldErrors = fieldErrors;
    }

    public Map<String, String> getFieldErrors() {
        return fieldErrors;
    }
}
