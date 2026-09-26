package com.ttcs.tenant.profile;

import java.time.LocalDate;

public class ProfileDTO {

    public record ProfileRequest(
            String hoTen,
            LocalDate ngaySinh,
            String soGiayTo,
            String queQuan,
            String ngheNghiep
    ) {}

    public record ProfileResponse(
            Long id,
            Long userId,
            String hoTen,
            LocalDate ngaySinh,
            String soGiayToMasked,
            String queQuan,
            String ngheNghiep,
            boolean hasAnhTruoc,
            boolean hasAnhSau
    ) {}
}
