import React, { useState } from "react";
import Head from "next/head";
import Link from "next/link";
import { useRouter } from "next/router";
import { useTranslation } from "next-i18next";
import { GetStaticProps } from "next";
import { serverSideTranslations } from "next-i18next/serverSideTranslations";
import { authService, RegisterRequest } from "../services/auth";
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

export default function Register() {
  const { t } = useTranslation('common');
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    if (password !== confirmPassword) {
      setError(t('register.passwordsNotMatch'));
      setLoading(false);
      return;
    }

    try {
      const registerData: RegisterRequest = {
        email,
        username,
        password,
      };

      const response = await authService.register(registerData);

      if (response.success) {
        // Get redirect URL from query params, default to dashboard
        const redirectUrl =
          (router.query.redirect as string) || "/my-dashboard";
        router.push(redirectUrl);
      } else {
        setError(
          response.error?.message || t('register.registerFailed'),
        );
      }
    } catch (err) {
      setError(t('register.registerFailed'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col" style={{ backgroundColor: 'var(--bg-base)' }}>
      <Head>
        <title>{t('register.title')}</title>
        <meta name="description" content={t('register.description')} />
        <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
      </Head>

      <main className="flex-1 flex items-center justify-center px-4 py-10">
        <div style={{ width: '100%', maxWidth: 440 }}>
          {/* Logo */}
          <div className="text-center mb-8">
            <Link href="/" className="inline-block mb-4">
              <FlaskIcon size={48} />
            </Link>
            <h1 style={{ fontSize: 20, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 4 }}>
              {t('register.createAccount')}
            </h1>
            <p className="pixel-label" style={{ color: 'var(--text-muted)' }}>{t('register.subtitle')}</p>
          </div>

          {/* Form Card */}
          <div style={{ backgroundColor: 'var(--bg-surface)', border: '1px solid var(--border-mid)', padding: '28px 28px' }}>
            {error && (
              <div style={{ marginBottom: 16, padding: '10px 12px', backgroundColor: '#1a0a0a', border: '1px solid #4a1a1a', color: '#f87171', fontSize: 12 }}>
                ✕ {error}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-5">
              <Input
                id="username"
                type="text"
                label={t('register.username')}
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder={t('register.usernamePlaceholder')}
                required
                leftIcon={
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                }
              />

              <Input
                id="email"
                type="email"
                label={t('auth.email')}
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder={t('register.enterEmail')}
                required
                leftIcon={
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 12a4 4 0 10-8 0 4 4 0 008 0zm0 0v1.5a2.5 2.5 0 005 0V12a9 9 0 10-9 9m4.5-1.206a8.959 8.959 0 01-4.5 1.207" />
                  </svg>
                }
              />

              <Input
                id="password"
                type="password"
                label={t('register.setPassword')}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder={t('register.passwordPlaceholder')}
                required
                leftIcon={
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                  </svg>
                }
              />

              <Input
                id="confirmPassword"
                type="password"
                label={t('register.confirmPassword')}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder={t('register.confirmPasswordPlaceholder')}
                required
                leftIcon={
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                }
              />

              <Button type="submit" variant="primary" size="lg" fullWidth loading={loading}>
                {t('register.registerAccount')}
              </Button>
            </form>

            <div style={{ marginTop: 20, paddingTop: 20, borderTop: '1px solid var(--border-dim)', fontSize: 13, color: 'var(--text-dim)', textAlign: 'center' }}>
              {t('register.hasAccount')}{' '}
              <Link href="/login" style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{t('register.loginNow')}</Link>
            </div>
          </div>

          <p className="pixel-label text-center mt-6" style={{ color: 'var(--text-muted)' }}>
            {t('register.copyright')}
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