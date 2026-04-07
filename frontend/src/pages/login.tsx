import React, { useState } from "react";
import Head from "next/head";
import Link from "next/link";
import { useRouter } from "next/router";
import { useTranslation } from "next-i18next";
import { GetStaticProps } from "next";
import { serverSideTranslations } from "next-i18next/serverSideTranslations";
import { authService, LoginRequest, PhoneLoginRequest } from "../services/auth";
import { useAuth } from "../contexts/AuthContext";
import { Button } from "../components/Button";
import { Input } from "../components/Input";

const FlaskIcon: React.FC<{ size?: number }> = ({ size = 48 }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    style={{ color: 'var(--logo-fg)' }}
  >
    <path
      d="M8 4V9L4 18C3.6 18.9 4.3 20 5.3 20H18.7C19.7 20 20.4 18.9 20 18L16 9V4"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <path
      d="M7 4H17"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
    />
    <circle cx="12" cy="16" r="1.5" fill="currentColor" opacity="0.5" />
    <circle cx="9" cy="14" r="1" fill="currentColor" opacity="0.5" />
    <circle cx="15" cy="14" r="1" fill="currentColor" opacity="0.5" />
  </svg>
);

export default function Login() {
  const { t } = useTranslation("common");
  const [loginType, setLoginType] = useState<'email' | 'phone'>('email');
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [verificationCode, setVerificationCode] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [codeSent, setCodeSent] = useState(false);
  const [countdown, setCountdown] = useState(0);
  const router = useRouter();
  const { login } = useAuth();

  const sendVerificationCode = async () => {
    if (!phoneNumber || !/^1[3-9]\d{9}$/.test(phoneNumber)) {
      setError(t('login.enterCorrectPhone'));
      return;
    }
    try {
      setLoading(true);
      const response = await authService.sendVerificationCode({ phone_number: phoneNumber, type: 'login' });
      if (response.success) {
        setCodeSent(true);
        setCountdown(60);
        const timer = setInterval(() => {
          setCountdown(prev => { if (prev <= 1) { clearInterval(timer); return 0; } return prev - 1; });
        }, 1000);
      } else {
        setError(response.error?.message || t('login.sendCodeFailed'));
      }
    } catch (err) {
      setError(t('login.sendCodeRetry'));
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      if (loginType === 'email') {
        const response = await authService.login({ email, password });
        if (response.success && response.data) {
          const profileResponse = await authService.getProfile();
          if (profileResponse.success && profileResponse.data) {
            login(profileResponse.data, response.data.access_token);
            router.push((router.query.redirect as string) || "/my-dashboard");
          } else {
            setError(t('login.getProfileFailed'));
          }
        } else {
          setError(response.error?.message || t('login.loginFailed'));
        }
      } else {
        if (!verificationCode) { setError(t('login.enterCode')); setLoading(false); return; }
        const response = await authService.loginWithPhone({ phone_number: phoneNumber, verification_code: verificationCode });
        if (response.success && response.data) {
          const profileResponse = await authService.getProfile();
          if (profileResponse.success && profileResponse.data) {
            login(profileResponse.data, response.data.access_token);
            router.push((router.query.redirect as string) || "/my-dashboard");
          } else {
            setError(t('login.getProfileFailed'));
          }
        } else {
          setError(response.error?.message || t('login.phoneLoginFailed'));
        }
      }
    } catch (err) {
      setError(t('login.loginFailed'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col" style={{ backgroundColor: 'var(--bg-base)' }}>
      <Head>
        <title>{t("auth.login")} — {t("brand.name")}</title>
        <meta name="description" content={`${t("auth.login")} to ${t("brand.name")} platform`} />
        <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
      </Head>

      <main className="flex-1 flex items-center justify-center px-4 py-10">
        <div style={{ width: '100%', maxWidth: 440 }}>
          {/* Logo */}
          <div className="text-center mb-8">
            <Link href="/" className="inline-block mb-4">
              <div className="logo-mark">
                <FlaskIcon size={48} />
              </div>
            </Link>
            <h1 style={{ fontSize: 20, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 4 }}>
              {t('login.welcomeBack')}
            </h1>
            <p className="pixel-label" style={{ color: 'var(--text-muted)' }}>LOGIN</p>
          </div>

          {/* Form Card */}
          <div style={{ backgroundColor: 'var(--bg-surface)', border: '1px solid var(--border-mid)', padding: '28px 28px' }}>
            {/* Login type tabs */}
            <div style={{ display: 'flex', marginBottom: 24, border: '1px solid var(--border-mid)' }}>
              {(['email', 'phone'] as const).map((type, i) => (
                <button
                  key={type}
                  onClick={() => setLoginType(type)}
                  style={{
                    flex: 1, padding: '9px 12px',
                    backgroundColor: loginType === type ? 'var(--text-primary)' : 'transparent',
                    color: loginType === type ? 'var(--bg-base)' : 'var(--text-dim)',
                    border: 'none',
                    borderRight: i === 0 ? '1px solid var(--border-mid)' : 'none',
                    cursor: 'pointer', fontSize: 13,
                    fontWeight: loginType === type ? 600 : 400,
                  }}
                >
                  {type === 'email' ? t('login.emailLogin') : t('login.phoneLogin')}
                </button>
              ))}
            </div>

            {/* Error */}
            {error && (
              <div style={{ marginBottom: 16, padding: '10px 12px', backgroundColor: '#1a0a0a', border: '1px solid #4a1a1a', color: '#f87171', fontSize: 12 }}>
                ✕ {error}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-5">
              {loginType === 'email' && (
                <>
                  <Input id="email" type="email" label={t('auth.email')} value={email}
                    onChange={(e) => setEmail(e.target.value)} placeholder={t('login.enterEmail')} required
                    leftIcon={<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 12a4 4 0 10-8 0 4 4 0 008 0zm0 0v1.5a2.5 2.5 0 005 0V12a9 9 0 10-9 9m4.5-1.206a8.959 8.959 0 01-4.5 1.207" /></svg>}
                  />
                  <Input id="password" type={showPassword ? "text" : "password"} label={t('auth.password')} value={password}
                    onChange={(e) => setPassword(e.target.value)} placeholder={t('login.enterPassword')} required
                    leftIcon={<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" /></svg>}
                    rightIcon={
                      <button type="button" onClick={() => setShowPassword(!showPassword)}>
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          {showPassword
                            ? <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.878 9.878L3 3m6.878 6.878L21 21" />
                            : <><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" /></>
                          }
                        </svg>
                      </button>
                    }
                  />
                </>
              )}

              {loginType === 'phone' && (
                <>
                  <div style={{ padding: '10px 12px', backgroundColor: '#0a0e1a', border: '1px solid #1a2030', color: '#93c5fd', fontSize: 12 }}>
                    {t('login.phoneLoginHint')}
                  </div>
                  <Input id="phone" type="tel" label={t('login.phoneLogin')} value={phoneNumber}
                    onChange={(e) => setPhoneNumber(e.target.value)} placeholder={t('login.enterPhone')} required
                    leftIcon={<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" /></svg>}
                  />
                  <div>
                    <label style={{ display: 'block', fontSize: 13, fontWeight: 500, color: 'var(--text-secondary)', marginBottom: 6 }}>{t('login.verificationCode')}</label>
                    <div className="flex gap-2">
                      <Input id="code" type="text" value={verificationCode}
                        onChange={(e) => setVerificationCode(e.target.value)} placeholder={t('login.enterCode')} required fullWidth
                      />
                      <Button type="button" onClick={sendVerificationCode} disabled={loading || countdown > 0} variant="secondary">
                        {countdown > 0 ? `${countdown}s` : t('login.send')}
                      </Button>
                    </div>
                  </div>
                </>
              )}

              <div className="flex items-center justify-between" style={{ fontSize: 13 }}>
                <label className="flex items-center gap-2 cursor-pointer" style={{ color: 'var(--text-dim)' }}>
                  <input type="checkbox" className="w-4 h-4" />
                  {t('login.rememberMe')}
                </label>
                {loginType === 'email' && (
                  <Link href="/reset-password" style={{ color: 'var(--text-dim)', fontSize: 13 }}>{t('login.forgotPassword')}</Link>
                )}
              </div>

              <Button type="submit" variant="primary" size="lg" fullWidth loading={loading}>
                {loginType === 'email' ? t('login.loginWithEmail') : t('login.loginWithPhone')}
              </Button>
            </form>

            <div style={{ marginTop: 20, paddingTop: 20, borderTop: '1px solid var(--border-dim)', fontSize: 13, color: 'var(--text-dim)', textAlign: 'center' }}>
              {t('login.noAccount')}{' '}
              <Link href="/register" style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{t('login.registerNow')}</Link>
            </div>
          </div>

          <p className="pixel-label text-center mt-6" style={{ color: 'var(--text-muted)' }}>
            {t('login.copyright')}
          </p>
        </div>
      </main>
    </div>
  );
}

export const getStaticProps: GetStaticProps = async ({ locale = 'en' }) => {
  return {
    props: {
      ...(await serverSideTranslations(locale, ["common"])),
    },
  };
};
