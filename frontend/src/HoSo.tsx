import { FormEvent, useEffect, useState } from 'react';
import { ArrowLeft, Camera, Check, FileText, Save, ShieldCheck, UserCheck } from 'lucide-react';
import { getMyProfile, ProfileData, updateMyProfile } from './api';

interface HoSoProps {
  token: string;
  onBack: () => void;
}

export function HoSo({ token, onBack }: HoSoProps) {
  const [profile, setProfile] = useState<ProfileData | null>(null);
  const [hoTen, setHoTen] = useState('');
  const [ngaySinh, setNgaySinh] = useState('2000-01-01');
  const [soGiayTo, setSoGiayTo] = useState('');
  const [queQuan, setQueQuan] = useState('');
  const [ngheNghiep, setNgheNghiep] = useState('');
  const [anhTruoc, setAnhTruoc] = useState<File | null>(null);
  const [anhSau, setAnhSau] = useState<File | null>(null);

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    async function load() {
      try {
        setLoading(true);
        const data = await getMyProfile(token);
        if (data) {
          setProfile(data);
          setHoTen(data.hoTen);
          setNgaySinh(data.ngaySinh);
          setQueQuan(data.queQuan);
          setNgheNghiep(data.ngheNghiep);
        }
      } catch (err) {
        setError((err as Error).message);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [token]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setMessage('');
    setError('');

    if (!hoTen.trim() || !ngaySinh || !queQuan.trim() || !ngheNghiep.trim()) {
      setError('Vui lòng điền đầy đủ các thông tin bắt buộc.');
      return;
    }

    if (soGiayTo.trim() && !/^(?:\d{9}|\d{12})$/.test(soGiayTo.trim())) {
      setError('Số căn cước phải gồm 9 hoặc 12 chữ số.');
      return;
    }

    setSaving(true);
    try {
      const formData = new FormData();
      formData.append('hoTen', hoTen.trim());
      formData.append('ngaySinh', ngaySinh);
      if (soGiayTo.trim()) formData.append('soGiayTo', soGiayTo.trim());
      formData.append('queQuan', queQuan.trim());
      formData.append('ngheNghiep', ngheNghiep.trim());
      if (anhTruoc) formData.append('anhGiayToTruoc', anhTruoc);
      if (anhSau) formData.append('anhGiayToSau', anhSau);

      const updated = await updateMyProfile(token, formData);
      setProfile(updated);
      setSoGiayTo('');
      setAnhTruoc(null);
      setAnhSau(null);
      setMessage('Lưu thông tin hồ sơ cá nhân thành công!');
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="info-card-panel">
        <p>Đang tải thông tin hồ sơ...</p>
      </div>
    );
  }

  return (
    <div className="info-card-panel">
      <div className="card-header">
        <h3 className="card-kicker-title" style={{ margin: 0, display: 'flex', alignItems: 'center', gap: 8 }}>
          <UserCheck size={20} /> HỒ SƠ CÁ NHÂN KHÁCH THUÊ (S1-06)
        </h3>
        <button type="button" className="btn-action-secondary" style={{ padding: '8px 14px', width: 'auto' }} onClick={onBack}>
          <ArrowLeft size={16} /> Quay lại
        </button>
      </div>

      {message && <div className="alert success"><Check size={18} /> {message}</div>}
      {error && <div className="alert error">{error}</div>}

      <form onSubmit={handleSubmit} className="profile-form">
        <div className="form-grid">
          <label>
            Họ và tên <span className="req">*</span>
            <input value={hoTen} onChange={(e) => setHoTen(e.target.value)} placeholder="Nguyễn Văn A" required />
          </label>

          <label>
            Ngày sinh <span className="req">*</span>
            <input type="date" value={ngaySinh} onChange={(e) => setNgaySinh(e.target.value)} required />
          </label>

          <label>
            Số Căn cước (CCCD)
            {profile?.soGiayToMasked && (
              <span className="masked-info">
                <ShieldCheck size={15} /> Số đã lưu: <strong>{profile.soGiayToMasked}</strong>
              </span>
            )}
            <input
              value={soGiayTo}
              onChange={(e) => setSoGiayTo(e.target.value)}
              placeholder={profile?.soGiayToMasked ? 'Để trống nếu không thay đổi' : '9 hoặc 12 chữ số'}
            />
            <small className="hint">Nhập 9 hoặc 12 chữ số, giữ số 0 ở đầu. Số cũ đã được bảo mật che.</small>
          </label>

          <label>
            Quê quán <span className="req">*</span>
            <input value={queQuan} onChange={(e) => setQueQuan(e.target.value)} placeholder="Hà Nội / Nam Định / ..." required />
          </label>

          <label>
            Nghề nghiệp <span className="req">*</span>
            <input value={ngheNghiep} onChange={(e) => setNgheNghiep(e.target.value)} placeholder="Kỹ sư / Lập trình viên / ..." required />
          </label>
        </div>

        <hr className="divider" />

        <h4 style={{ margin: '12px 0 8px', color: '#0f172a', fontSize: '0.98rem', display: 'flex', alignItems: 'center', gap: 8 }}>
          <FileText size={18} /> Ảnh giấy tờ căn cước (Tối đa 5MB / ảnh, JPG hoặc PNG)
        </h4>

        <div className="image-grid">
          <div className="image-box">
            <label>Mặt trước CCCD {profile?.hasAnhTruoc && <span className="badge-ok">✓ Đã có ảnh</span>}</label>
            <input type="file" accept="image/jpeg,image/png" onChange={(e) => setAnhTruoc(e.target.files?.[0] ?? null)} />
            {anhTruoc && <small className="file-name"><Camera size={14} /> Chọn: {anhTruoc.name}</small>}
          </div>

          <div className="image-box">
            <label>Mặt sau CCCD {profile?.hasAnhSau && <span className="badge-ok">✓ Đã có ảnh</span>}</label>
            <input type="file" accept="image/jpeg,image/png" onChange={(e) => setAnhSau(e.target.files?.[0] ?? null)} />
            {anhSau && <small className="file-name"><Camera size={14} /> Chọn: {anhSau.name}</small>}
          </div>
        </div>

        <div className="actions" style={{ marginTop: 16 }}>
          <button type="submit" className="btn-action-primary" style={{ width: 'auto' }} disabled={saving}>
            <Save size={18} /> {saving ? 'Đang lưu...' : 'Lưu hồ sơ cá nhân'}
          </button>
        </div>
      </form>
    </div>
  );
}
