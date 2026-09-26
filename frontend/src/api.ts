export interface RegisterForm {
  fullName: string;
  phone: string;
  email: string;
  password: string;
}

export interface LoginForm {
  identifier: string;
  password: string;
}

export interface RegisterResponse {
  accessToken: string;
  refreshToken: string;
  tokenType: string;
  expiresIn: number;
  user: {
    id: number;
    fullName: string;
    phone: string;
    email: string;
    role: string;
  };
}

export interface ProfileData {
  id?: number;
  userId?: number;
  hoTen: string;
  ngaySinh: string;
  soGiayToMasked?: string;
  soGiayTo?: string;
  queQuan: string;
  ngheNghiep: string;
  hasAnhTruoc?: boolean;
  hasAnhSau?: boolean;
}

interface ErrorResponse {
  message?: string;
  fieldErrors?: Record<string, string>;
}

const API_BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8080';

export async function registerTenant(form: RegisterForm): Promise<RegisterResponse> {
  const response = await fetch(`${API_BASE}/api/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(form),
  });

  if (!response.ok) {
    const error = (await response.json()) as ErrorResponse;
    const validationError = new Error(error.message ?? 'Đăng ký không thành công.') as Error & {
      fieldErrors?: Record<string, string>;
    };
    validationError.fieldErrors = error.fieldErrors;
    throw validationError;
  }

  return (await response.json()) as RegisterResponse;
}

export async function loginTenant(form: LoginForm): Promise<RegisterResponse> {
  const response = await fetch(`${API_BASE}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(form),
  });

  if (!response.ok) {
    const error = (await response.json()) as ErrorResponse;
    throw new Error(error.message ?? 'Đăng nhập không thành công.');
  }

  return (await response.json()) as RegisterResponse;
}

export async function logoutTenant(token: string, userId?: number): Promise<void> {
  await fetch(`${API_BASE}/api/auth/logout`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ userId }),
  });
}

export async function getMyProfile(token: string): Promise<ProfileData | null> {
  const response = await fetch(`${API_BASE}/api/profile/me`, {
    headers: { Authorization: `Bearer ${token}` },
  });

  if (response.status === 404) return null;
  if (!response.ok) throw new Error('Không thể tải hồ sơ cá nhân.');

  return (await response.json()) as ProfileData;
}

export async function updateMyProfile(token: string, formData: FormData): Promise<ProfileData> {
  const response = await fetch(`${API_BASE}/api/profile/me`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: formData,
  });

  if (!response.ok) {
    const error = (await response.json()) as ErrorResponse;
    throw new Error(error.message ?? 'Không thể cập nhật hồ sơ cá nhân.');
  }

  return (await response.json()) as ProfileData;
}
