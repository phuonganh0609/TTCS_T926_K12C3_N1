import { FormEvent, useState } from 'react';
import {
  ArrowRight,
  CheckCircle2,
  Home,
  LockKeyhole,
  LogOut,
  Mail,
  Phone,
  UserCheck,
  UserRound,
} from 'lucide-react';
import { loginTenant, LoginForm, logoutTenant, registerTenant, RegisterForm, RegisterResponse } from './api';
import { HoSo } from './HoSo';

const initialForm: RegisterForm = {
  fullName: '',
  phone: '',
  email: '',
  password: '',
};

const initialLoginForm: LoginForm = {
  identifier: '',
  password: '',
};

const roleLabels: Record<string, string> = {
  TENANT: 'Khách thuê',
  LANDLORD: 'Chủ nhà',
  BUILDING_MANAGER: 'Quản lý tòa nhà',
  ADMIN: 'Quản trị viên',
};

const clientErrors = (form: RegisterForm): Record<string, string> => {
  const errors: Record<string, string> = {};
  if (!form.fullName.trim()) errors.fullName = 'Vui lòng nhập họ tên.';
  if (!/^0\d{9}$/.test(form.phone)) errors.phone = 'Số điện thoại gồm 10 chữ số và bắt đầu bằng 0.';
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) errors.email = 'Email chưa đúng định dạng.';
  if (form.password.length < 8 || !/[A-Za-z]/.test(form.password) || !/\d/.test(form.password)) {
    errors.password = 'Mật khẩu cần ít nhất 8 ký tự, gồm chữ và số.';
  }
  return errors;
};

function getInitials(name: string): string {
  const parts = name.trim().split(/\s+/);
  if (parts.length === 0) return 'U';
  if (parts.length === 1) return parts[0].substring(0, 2).toUpperCase();
  return (parts[parts.length - 2][0] + parts[parts.length - 1][0]).toUpperCase();
}

function App() {
  const [form, setForm] = useState<RegisterForm>(initialForm);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [serverError, setServerError] = useState('');
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);
  const [dashboardUser, setDashboardUser] = useState<RegisterResponse['user'] | null>(null);
  const [accessToken, setAccessToken] = useState<string>(() => localStorage.getItem('accessToken') ?? '');
  const [view, setView] = useState<'dashboard' | 'profile'>('dashboard');
  const [mode, setMode] = useState<'register' | 'login'>('register');
  const [loginForm, setLoginForm] = useState<LoginForm>(initialLoginForm);

  const updateField = (field: keyof RegisterForm, value: string) => {
    setForm((current) => ({ ...current, [field]: value }));
    setErrors((current) => ({ ...current, [field]: '' }));
    setServerError('');
  };

  const updateLoginField = (field: keyof LoginForm, value: string) => {
    setLoginForm((current) => ({ ...current, [field]: value }));
    setErrors((current) => ({ ...current, [field]: '' }));
    setServerError('');
  };

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const validationErrors = mode === 'register'
      ? clientErrors(form)
      : {
          ...(loginForm.identifier.trim() ? {} : { identifier: 'Vui lòng nhập email hoặc số điện thoại.' }),
          ...(loginForm.password ? {} : { password: 'Vui lòng nhập mật khẩu.' }),
        };
    setErrors(validationErrors);
    setServerError('');
    setSuccess(false);
    if (Object.keys(validationErrors).length > 0) return;

    setLoading(true);
    try {
      const response = mode === 'register' ? await registerTenant(form) : await loginTenant(loginForm);
      localStorage.setItem('accessToken', response.accessToken);
      localStorage.setItem('refreshToken', response.refreshToken);
      setAccessToken(response.accessToken);
      setSuccess(mode === 'register');
      setForm(initialForm);
      setLoginForm(initialLoginForm);
      window.history.replaceState({}, '', '/trang-chu');
      window.setTimeout(() => setDashboardUser(response.user), 400);
    } catch (error) {
      const apiError = error as Error & { fieldErrors?: Record<string, string> };
      setServerError(apiError.message);
      setErrors(apiError.fieldErrors ?? {});
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    if (accessToken) {
      await logoutTenant(accessToken, dashboardUser?.id);
    }
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    setAccessToken('');
    setDashboardUser(null);
    setView('dashboard');
    window.history.replaceState({}, '', '/');
  };

  // ──────────────────────────────────────────────────────────────────────────
  // LOGGED IN DASHBOARD VIEW (Designed to match exact user prompt spec)
  // ──────────────────────────────────────────────────────────────────────────
  if (dashboardUser) {
    return (
      <div className="dashboard-app-wrapper">
        {/* Top Header Navbar */}
        <header className="dashboard-header">
          <div className="header-container">
            <div className="header-brand" onClick={() => setView('dashboard')}>
              <div className="brand-logo-mark">
                <Home size={20} />
              </div>
              <span className="brand-text">Hệ Thống Cho Thuê</span>
            </div>

            <div className="header-user">
              <div className="user-details">
                <span className="user-name">{dashboardUser.fullName}</span>
                <span className="user-role-badge">{roleLabels[dashboardUser.role] ?? dashboardUser.role}</span>
              </div>
              <div className="user-avatar-circle">{getInitials(dashboardUser.fullName)}</div>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="dashboard-page-container">
          {view === 'profile' ? (
            <HoSo token={accessToken} onBack={() => setView('dashboard')} />
          ) : (
            <>
              {/* Welcome Title Banner */}
              <section className="welcome-section">
                <p className="status-kicker">ĐĂNG NHẬP THÀNH CÔNG</p>
                <h1 className="welcome-title">Chào mừng, {dashboardUser.fullName} 👋</h1>
                <p className="welcome-subtitle">
                  Tài khoản khách thuê của bạn đã sẵn sàng để bắt đầu tìm căn phòng phù hợp.
                </p>
              </section>

              {/* Account Info Card (Modern Rounded Card) */}
              <section className="info-card-panel">
                <h3 className="card-kicker-title">THÔNG TIN TÀI KHOẢN</h3>

                <div className="account-info-grid">
                  <div className="info-cell">
                    <span className="info-cell-label">Email</span>
                    <strong className="info-cell-val">{dashboardUser.email}</strong>
                  </div>
                  <div className="info-cell">
                    <span className="info-cell-label">Số điện thoại</span>
                    <strong className="info-cell-val">{dashboardUser.phone}</strong>
                  </div>
                  <div className="info-cell">
                    <span className="info-cell-label">Vai trò</span>
                    <strong className="info-cell-val">{roleLabels[dashboardUser.role] ?? dashboardUser.role}</strong>
                  </div>
                </div>

                {/* Exact 2 action buttons from Image 2 */}
                <div className="action-buttons-group">
                  <button type="button" className="btn-action-primary" onClick={() => setView('profile')}>
                    <UserCheck size={18} /> Hồ sơ cá nhân (S1-06)
                  </button>
                  <button type="button" className="btn-action-secondary" onClick={handleLogout}>
                    <LogOut size={18} /> Đăng xuất
                  </button>
                </div>
              </section>
            </>
          )}
        </main>
      </div>
    );
  }

  // ──────────────────────────────────────────────────────────────────────────
  // LOGIN / REGISTER VIEW (Kept clean and unchanged)
  // ──────────────────────────────────────────────────────────────────────────
  return (
    <main className="shell">
      <section className="intro">
        <p className="eyebrow">HỆ THỐNG CHO THUÊ PHÒNG TRỌ VÀ CĂN HỘ</p>
        <h1>Tìm một nơi vừa vặn với nhịp sống của bạn.</h1>
        <p className="intro-copy">
          Đăng ký tài khoản khách thuê để tìm phòng trọ, căn hộ và gửi yêu cầu thuê ngay khi thấy tin phù hợp.
        </p>
        <div className="trust-row">
          <span><CheckCircle2 size={17} /> Miễn phí bắt đầu</span>
          <span><LockKeyhole size={17} /> Mật khẩu được bảo vệ</span>
        </div>
      </section>

      <section className="register-panel" aria-labelledby="register-title">
        <div className="panel-heading">
          <div className="mark"><UserRound size={20} /></div>
          <div>
            <p className="kicker">{mode === 'register' ? 'TẠO TÀI KHOẢN' : 'CHÀO MỪNG TRỞ LẠI'}</p>
            <h2 id="register-title">{mode === 'register' ? 'Đăng ký khách thuê' : 'Đăng nhập'}</h2>
          </div>
        </div>

        {success && <div className="alert success">Đăng ký thành công. Bạn đã được đăng nhập.</div>}
        {serverError && <div className="alert error">{serverError}</div>}

        <form onSubmit={submit} noValidate>
          {mode === 'login' ? (
            <>
              <label>
                Email hoặc số điện thoại
                <span className="input-wrap">
                  <Mail size={18} />
                  <input
                    value={loginForm.identifier}
                    onChange={(event) => updateLoginField('identifier', event.target.value)}
                    placeholder="email@example.com hoặc 0901234567"
                    autoComplete="username"
                  />
                </span>
                {errors.identifier && <small>{errors.identifier}</small>}
              </label>
              <label>
                Mật khẩu
                <span className="input-wrap">
                  <LockKeyhole size={18} />
                  <input
                    type="password"
                    value={loginForm.password}
                    onChange={(event) => updateLoginField('password', event.target.value)}
                    placeholder="Nhập mật khẩu"
                    autoComplete="current-password"
                  />
                </span>
                {errors.password && <small>{errors.password}</small>}
              </label>
            </>
          ) : (
            <>
              <label>
                Họ và tên
                <span className="input-wrap">
                  <UserRound size={18} />
                  <input
                    value={form.fullName}
                    onChange={(event) => updateField('fullName', event.target.value)}
                    placeholder="Nguyễn Văn A"
                    autoComplete="name"
                  />
                </span>
                {errors.fullName && <small>{errors.fullName}</small>}
              </label>
              <label>
                Số điện thoại
                <span className="input-wrap">
                  <Phone size={18} />
                  <input
                    value={form.phone}
                    onChange={(event) => updateField('phone', event.target.value)}
                    placeholder="0901234567"
                    inputMode="numeric"
                    autoComplete="tel"
                  />
                </span>
                {errors.phone && <small>{errors.phone}</small>}
              </label>
              <label>
                Email
                <span className="input-wrap">
                  <Mail size={18} />
                  <input
                    type="email"
                    value={form.email}
                    onChange={(event) => updateField('email', event.target.value)}
                    placeholder="ban@example.com"
                    autoComplete="email"
                  />
                </span>
                {errors.email && <small>{errors.email}</small>}
              </label>
              <label>
                Mật khẩu
                <span className="input-wrap">
                  <LockKeyhole size={18} />
                  <input
                    type="password"
                    value={form.password}
                    onChange={(event) => updateField('password', event.target.value)}
                    placeholder="Tối thiểu 8 ký tự, gồm chữ và số"
                    autoComplete="new-password"
                  />
                </span>
                {errors.password && <small>{errors.password}</small>}
              </label>
            </>
          )}
          <button type="submit" disabled={loading}>
            {loading ? 'Đang xử lý...' : mode === 'register' ? 'Tạo tài khoản' : 'Đăng nhập'}
            {!loading && <ArrowRight size={18} />}
          </button>
        </form>
        <p className="fine-print">
          {mode === 'register' ? 'Bằng cách tiếp tục, bạn đồng ý với điều khoản sử dụng của nền tảng.' : 'Chưa có tài khoản?'}{' '}
          <button
            type="button"
            className="link-button"
            onClick={() => {
              setMode(mode === 'register' ? 'login' : 'register');
              setErrors({});
              setServerError('');
            }}
          >
            {mode === 'register' ? 'Đăng nhập' : 'Đăng ký ngay'}
          </button>
        </p>
      </section>
    </main>
  );
}

export default App;
