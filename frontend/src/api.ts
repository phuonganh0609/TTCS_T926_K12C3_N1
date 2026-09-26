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

interface ErrorResponse {
  message?: string;
  fieldErrors?: Record<string, string>;
}

export async function registerTenant(form: RegisterForm): Promise<RegisterResponse> {
  const response = await fetch(`${import.meta.env.VITE_API_URL ?? 'http://localhost:8080'}/api/auth/register`, {
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
  const response = await fetch(`${import.meta.env.VITE_API_URL ?? 'http://localhost:8080'}/api/auth/login`, {
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
