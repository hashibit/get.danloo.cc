import { useState, useEffect } from 'react';
import { GetServerSideProps } from 'next';
import { serverSideTranslations } from 'next-i18next/serverSideTranslations';
import { useTranslation } from 'next-i18next';
import { authService, User } from '../services/auth';
import { apiRequest } from '../services/api';
import Layout from '../components/Layout';
import { Input } from '../components/Input';
import { Button } from '../components/Button';

interface UserProfile extends User {
  email_verified?: boolean;
  social_accounts?: {
    provider: 'wechat' | 'google' | 'github';
    account_id: string;
    nickname?: string;
    avatar?: string;
    linked_at: string;
  }[];
}

interface UpdatePasswordRequest {
  old_password: string;
  new_password: string;
  confirm_password: string;
}

const ProfilePage = () => {
  const { t } = useTranslation('common');
  const [user, setUser] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'basic' | 'security' | 'social'>('basic');

  const [updatePasswordForm, setUpdatePasswordForm] = useState<UpdatePasswordRequest>({
    old_password: '',
    new_password: '',
    confirm_password: '',
  });
  const [updateEmailForm, setUpdateEmailForm] = useState({ new_email: '', verification_code: '' });
  const [updatePhoneForm, setUpdatePhoneForm] = useState({ new_phone: '', verification_code: '' });

  useEffect(() => {
    loadUserProfile();
  }, []);

  const loadUserProfile = async () => {
    try {
      const response = await authService.getProfile();
      if (response.success && response.data) {
        setUser(response.data as UserProfile);
      }
    } catch (error) {
      console.error('Failed to load user profile:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdatePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (updatePasswordForm.new_password !== updatePasswordForm.confirm_password) {
      alert(t('profile.passwordsNotMatch'));
      return;
    }
    try {
      const response = await apiRequest('/users/me/password', {
        method: 'PUT',
        body: JSON.stringify({ old_password: updatePasswordForm.old_password, new_password: updatePasswordForm.new_password }),
      });
      if (response.success) {
        alert(t('profile.passwordUpdateSuccess'));
        setUpdatePasswordForm({ old_password: '', new_password: '', confirm_password: '' });
      } else {
        alert(t('profile.passwordUpdateFailed') + ': ' + response.error);
      }
    } catch {
      alert(t('profile.passwordUpdateFailed'));
    }
  };

  const handleUpdateEmail = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const response = await apiRequest('/users/me/email', { method: 'PUT', body: JSON.stringify(updateEmailForm) });
      if (response.success) {
        alert(t('profile.emailUpdateSuccess'));
        setUpdateEmailForm({ new_email: '', verification_code: '' });
        loadUserProfile();
      } else {
        alert(t('profile.emailUpdateFailed') + ': ' + response.error);
      }
    } catch {
      alert(t('profile.emailUpdateFailed'));
    }
  };

  const handleUpdatePhone = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const response = await apiRequest('/users/me/phone', { method: 'PUT', body: JSON.stringify(updatePhoneForm) });
      if (response.success) {
        alert(t('profile.phoneUpdateSuccess'));
        setUpdatePhoneForm({ new_phone: '', verification_code: '' });
        loadUserProfile();
      } else {
        alert(t('profile.phoneUpdateFailed') + ': ' + response.error);
      }
    } catch {
      alert(t('profile.phoneUpdateFailed'));
    }
  };

  const handleForgotPassword = async () => {
    if (!user?.email) { alert(t('profile.pleaseBindEmail')); return; }
    try {
      const response = await authService.requestPasswordReset(user.email);
      alert(response.success ? t('profile.resetEmailSent') : t('profile.sendResetEmailFailed'));
    } catch {
      alert(t('profile.sendResetEmailFailed2'));
    }
  };

  const handleUnlinkSocialAccount = async (provider: string) => {
    try {
      const response = await apiRequest(`/users/me/social/${provider}`, { method: 'DELETE' });
      if (response.success) { alert(t('profile.unbindSuccess')); loadUserProfile(); }
      else alert(t('profile.unbindFailed') + ': ' + response.error);
    } catch {
      alert(t('profile.unbindFailed'));
    }
  };

  const handleSendEmailVerificationLink = async () => {
    try {
      const response = await authService.sendEmailVerification();
      alert(response.success ? t('profile.verificationEmailSent') : t('profile.sendVerificationEmailFailed'));
    } catch {
      alert(t('profile.sendVerificationEmailFailed'));
    }
  };

  const sectionStyle: React.CSSProperties = {
    paddingTop: 20, marginTop: 20, borderTop: '1px solid var(--border-dim)',
  };

  const sectionTitle: React.CSSProperties = {
    fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 16,
  };

  if (loading) {
    return (
      <Layout title={`${t('profile.title')} - ${t('brand.name')}`}>
        <div style={{ textAlign: 'center', padding: '40px 0' }}>
          <span style={{ color: 'var(--text-dim)', fontSize: 13 }}>LOADING...</span>
        </div>
      </Layout>
    );
  }

  const tabs: Array<{ key: 'basic' | 'security' | 'social'; label: string }> = [
    { key: 'basic', label: t('profile.basicInfo') },
    { key: 'security', label: t('profile.security') },
    { key: 'social', label: t('profile.social') },
  ];

  return (
    <Layout
      title={`${t('profile.title')} - ${t('brand.name')}`}
      description={t('profile.description')}
    >
      <div style={{ maxWidth: 720 }}>
        {/* Card */}
        <div style={{ backgroundColor: 'var(--bg-surface)', border: '1px solid var(--border-mid)' }}>
          {/* Card header */}
          <div style={{ padding: '14px 22px', borderBottom: '1px solid var(--border-mid)' }}>
            <h2 style={{ color: 'var(--text-primary)', fontSize: 15, fontWeight: 600 }}>{t('profile.title')}</h2>
            <p style={{ color: 'var(--text-dim)', fontSize: 12, marginTop: 2 }}>{t('profile.manageAccount')}</p>
          </div>

          {/* Tabs */}
          <div style={{ display: 'flex', borderBottom: '1px solid var(--border-mid)' }}>
            {tabs.map((tab, i) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                style={{
                  flex: 1, padding: '10px 12px', fontSize: 13, fontWeight: activeTab === tab.key ? 600 : 400,
                  color: activeTab === tab.key ? 'var(--text-primary)' : 'var(--text-dim)',
                  backgroundColor: 'transparent', border: 'none',
                  borderBottom: activeTab === tab.key ? '1px solid var(--text-primary)' : '1px solid transparent',
                  borderRight: i < tabs.length - 1 ? '1px solid var(--border-dim)' : 'none',
                  cursor: 'pointer', marginBottom: -1,
                }}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Tab content */}
          <div style={{ padding: '22px' }}>
            {activeTab === 'basic' && (
              <div>
                <p style={sectionTitle}>{t('profile.basicInfo')}</p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                  <Input label={t('profile.username')} value={user?.username} disabled fullWidth />
                  <div>
                    <Input label={t('profile.email')} value={user?.email || t('profile.notBound')} disabled fullWidth />
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 6 }}>
                      {user?.email && user.email_verified && (
                        <span style={{ fontSize: 11, color: '#4ade80', backgroundColor: '#0a1a0e', border: '1px solid #1a3020', padding: '1px 6px' }}>✓ {t('profile.verified')}</span>
                      )}
                      {user?.email && !user.email_verified && (
                        <>
                          <span style={{ fontSize: 11, color: '#fbbf24', backgroundColor: '#1a1600', border: '1px solid #3a3000', padding: '1px 6px' }}>⚠ {t('profile.notVerified')}</span>
                          <Button size="sm" variant="secondary" onClick={handleSendEmailVerificationLink}>{t('profile.sendVerificationEmail')}</Button>
                        </>
                      )}
                    </div>
                  </div>
                  <div>
                    <Input label={t('profile.phone')} value={user?.phone_number || t('profile.notBound')} disabled fullWidth />
                    {user?.phone_number && user.phone_verified && (
                      <span style={{ fontSize: 11, color: '#4ade80', backgroundColor: '#0a1a0e', border: '1px solid #1a3020', padding: '1px 6px', marginTop: 6, display: 'inline-block' }}>{t('profile.verified')}</span>
                    )}
                  </div>
                  <Input label={t('profile.registeredAt')} value={user?.createdAt ? new Date(user.createdAt).toLocaleDateString() : ''} disabled fullWidth />
                  <Input label={t('profile.alchemyLevel')} value={String(user?.alchemyLevel || '')} disabled fullWidth />
                </div>
              </div>
            )}

            {activeTab === 'security' && (
              <div>
                {/* Password */}
                <p style={sectionTitle}>{t('profile.passwordManagement')}</p>
                <form onSubmit={handleUpdatePassword} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                  <Input type="password" label={t('profile.currentPassword')} value={updatePasswordForm.old_password}
                    onChange={(e) => setUpdatePasswordForm({ ...updatePasswordForm, old_password: e.target.value })} required fullWidth />
                  <Input type="password" label={t('profile.newPassword')} value={updatePasswordForm.new_password}
                    onChange={(e) => setUpdatePasswordForm({ ...updatePasswordForm, new_password: e.target.value })} required fullWidth />
                  <Input type="password" label={t('profile.confirmNewPassword')} value={updatePasswordForm.confirm_password}
                    onChange={(e) => setUpdatePasswordForm({ ...updatePasswordForm, confirm_password: e.target.value })} required fullWidth />
                  <div style={{ display: 'flex', gap: 8 }}>
                    <Button type="submit" variant="primary">{t('profile.updatePassword')}</Button>
                    <Button type="button" variant="ghost" onClick={handleForgotPassword}>{t('profile.forgotPassword')}</Button>
                  </div>
                </form>

                {/* Email */}
                <div style={sectionStyle}>
                  <p style={sectionTitle}>{t('profile.emailManagement')}</p>
                  <form onSubmit={handleUpdateEmail} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                    <Input type="email" label={t('profile.newEmail')} value={updateEmailForm.new_email}
                      onChange={(e) => setUpdateEmailForm({ ...updateEmailForm, new_email: e.target.value })} required fullWidth />
                    <div style={{ display: 'flex', gap: 8, alignItems: 'flex-end' }}>
                      <div style={{ flex: 1 }}>
                        <Input type="text" label={t('profile.verificationCode')} value={updateEmailForm.verification_code}
                          onChange={(e) => setUpdateEmailForm({ ...updateEmailForm, verification_code: e.target.value })} required fullWidth />
                      </div>
                      <Button type="button" variant="secondary"
                        onClick={async () => {
                          if (!updateEmailForm.new_email) { alert(t('profile.pleaseEnterNewEmail')); return; }
                          try {
                            const r = await authService.sendVerificationCode({ phone_number: updateEmailForm.new_email, type: 'email_verification' });
                            alert(r.success ? t('profile.emailCodeSent') : t('profile.sendResetEmailFailed'));
                          } catch { alert(t('profile.sendEmailCodeFailed')); }
                        }}>{t('profile.sendCode')}</Button>
                    </div>
                    <Button type="submit" variant="primary">{t('profile.updateEmail')}</Button>
                  </form>
                </div>

                {/* Phone */}
                <div style={sectionStyle}>
                  <p style={sectionTitle}>{t('profile.phoneManagement')}</p>
                  <form onSubmit={handleUpdatePhone} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                    <Input type="tel" label={t('profile.newPhone')} value={updatePhoneForm.new_phone}
                      onChange={(e) => setUpdatePhoneForm({ ...updatePhoneForm, new_phone: e.target.value })} required fullWidth />
                    <div style={{ display: 'flex', gap: 8, alignItems: 'flex-end' }}>
                      <div style={{ flex: 1 }}>
                        <Input type="text" label={t('profile.verificationCode')} value={updatePhoneForm.verification_code}
                          onChange={(e) => setUpdatePhoneForm({ ...updatePhoneForm, verification_code: e.target.value })} required fullWidth />
                      </div>
                      <Button type="button" variant="secondary"
                        onClick={async () => {
                          if (!updatePhoneForm.new_phone) { alert(t('profile.pleaseEnterNewPhone')); return; }
                          try {
                            const r = await authService.sendVerificationCode({ phone_number: updatePhoneForm.new_phone, type: 'phone_verification' });
                            alert(r.success ? t('profile.phoneCodeSent') : t('profile.sendResetEmailFailed'));
                          } catch { alert(t('profile.sendPhoneCodeFailed')); }
                        }}>{t('profile.sendCode')}</Button>
                    </div>
                    <Button type="submit" variant="primary">{t('profile.updatePhone')}</Button>
                  </form>
                </div>
              </div>
            )}

            {activeTab === 'social' && (
              <div>
                <p style={sectionTitle}>{t('profile.socialAccounts')}</p>
                {user?.social_accounts && user.social_accounts.length > 0 ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                    {user.social_accounts.map((account) => (
                      <div
                        key={account.provider}
                        style={{ border: '1px solid var(--border-dim)', padding: '12px 16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                          {account.avatar && (
                            <img src={account.avatar} alt={account.nickname} style={{ width: 32, height: 32 }} />
                          )}
                          <div>
                            <p style={{ color: 'var(--text-primary)', fontSize: 13, fontWeight: 500 }}>{account.nickname || account.provider}</p>
                            <p style={{ color: 'var(--text-dim)', fontSize: 11 }}>{account.provider} · {t('profile.boundAt')} {new Date(account.linked_at).toLocaleDateString()}</p>
                          </div>
                        </div>
                        <Button variant="destructive" size="sm" onClick={() => handleUnlinkSocialAccount(account.provider)}>{t('profile.unbind')}</Button>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p style={{ color: 'var(--text-dim)', fontSize: 13 }}>{t('profile.noSocialAccounts')}</p>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </Layout>
  );
};

export const getServerSideProps: GetServerSideProps = async ({ locale }) => {
  return {
    props: {
      ...(await serverSideTranslations(locale ?? 'en', ['common'])),
    },
  };
};

export default ProfilePage;
