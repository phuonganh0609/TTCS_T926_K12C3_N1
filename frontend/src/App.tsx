import { FormEvent, useState } from 'react';
import { ArrowRight, CheckCircle2, LockKeyhole, Mail, Phone, UserRound } from 'lucide-react';
import { registerTenant, RegisterForm } from './api';

const initialForm: RegisterForm = {
  fullName: '',
  phone: '',
  email: '',
  password: '',
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

function App() {
  const [form, setForm] = useState<RegisterForm>(initialForm);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [serverError, setServerError] = useState('');
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  const updateField = (field: keyof RegisterForm, value: string) => {
    setForm((current) => ({ ...current, [field]: value }));
    setErrors((current) => ({ ...current, [field]: '' }));
    setServerError('');
  };

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const validationErrors = clientErrors(form);
    setErrors(validationErrors);
    setServerError('');
    setSuccess(false);
    if (Object.keys(validationErrors).length > 0) return;

    setLoading(true);
    try {
      const response = await registerTenant(form);
      localStorage.setItem('accessToken', response.accessToken);
      localStorage.setItem('refreshToken', response.refreshToken);
      setSuccess(true);
      setForm(initialForm);
    } catch (error) {
      const apiError = error as Error & { fieldErrors?: Record<string, string> };
      setServerError(apiError.message);
      setErrors(apiError.fieldErrors ?? {});
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="shell">
      <section className="intro">
        <p className="eyebrow">NỀN TẢNG THUÊ NHÀ</p>
        <h1>Tìm một nơi vừa vặn với nhịp sống của bạn.</h1>
        <p className="intro-copy">Tạo tài khoản khách thuê để lưu tin, gửi yêu cầu và bắt đầu hành trình tìm chỗ ở phù hợp.</p>
        <div className="trust-row">
          <span><CheckCircle2 size={17} /> Miễn phí bắt đầu</span>
          <span><LockKeyhole size={17} /> Mật khẩu được bảo vệ</span>
        </div>
      </section>

      <section className="register-panel" aria-labelledby="register-title">
        <div className="panel-heading">
          <div className="mark"><UserRound size={20} /></div>
          <div>
            <p className="kicker">TẠO TÀI KHOẢN</p>
            <h2 id="register-title">Đăng ký khách thuê</h2>
          </div>
        </div>

        {success && <div className="alert success">Đăng ký thành công. Bạn đã được đăng nhập.</div>}
        {serverError && <div className="alert error">{serverError}</div>}

        <form onSubmit={submit} noValidate>
          <label>
            Họ và tên
            <span className="input-wrap"><UserRound size={18} /><input value={form.fullName} onChange={(event) => updateField('fullName', event.target.value)} placeholder="Nguyễn Văn A" autoComplete="name" /></span>
            {errors.fullName && <small>{errors.fullName}</small>}
          </label>
          <label>
            Số điện thoại
            <span className="input-wrap"><Phone size={18} /><input value={form.phone} onChange={(event) => updateField('phone', event.target.value)} placeholder="0901234567" inputMode="numeric" autoComplete="tel" /></span>
            {errors.phone && <small>{errors.phone}</small>}
          </label>
          <label>
            Email
            <span className="input-wrap"><Mail size={18} /><input type="email" value={form.email} onChange={(event) => updateField('email', event.target.value)} placeholder="ban@example.com" autoComplete="email" /></span>
            {errors.email && <small>{errors.email}</small>}
          </label>
          <label>
            Mật khẩu
            <span className="input-wrap"><LockKeyhole size={18} /><input type="password" value={form.password} onChange={(event) => updateField('password', event.target.value)} placeholder="Tối thiểu 8 ký tự, gồm chữ và số" autoComplete="new-password" /></span>
            {errors.password && <small>{errors.password}</small>}
          </label>
          <button type="submit" disabled={loading}>
            {loading ? 'Đang tạo tài khoản...' : 'Tạo tài khoản'}
            {!loading && <ArrowRight size={18} />}
          </button>
        </form>
        <p className="fine-print">Bằng cách tiếp tục, bạn đồng ý với điều khoản sử dụng của nền tảng.</p>
      </section>
    </main>
  );
}

export default App;
