package com.ttcs.tenant.auth;

/** Ném khi tài khoản bị tạm khóa do nhập sai mật khẩu nhiều lần. */
public class AccountLockedException extends RuntimeException {
    private final long lockSecondsRemaining;

    public AccountLockedException(String message, long lockSecondsRemaining) {
        super(message);
        this.lockSecondsRemaining = lockSecondsRemaining;
    }

    public long getLockSecondsRemaining() { return lockSecondsRemaining; }
}
