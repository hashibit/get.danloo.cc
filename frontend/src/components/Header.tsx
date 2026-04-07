import React from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { useTranslation } from 'next-i18next';
import { Button } from './Button';
import UserMenu from './UserMenu';
import ThemeToggle from './ThemeToggle';
import { useOptionalAuth } from '../contexts/AuthContext';

const FlaskIcon: React.FC<{ size?: number }> = ({ size = 18 }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    style={{ color: 'var(--logo-fg)' }}
  >
    {/* Flask body */}
    <path
      d="M8 4V9L4 18C3.6 18.9 4.3 20 5.3 20H18.7C19.7 20 20.4 18.9 20 18L16 9V4"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    {/* Flask neck rim */}
    <path
      d="M7 4H17"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
    />
    {/* Bubbles */}
    <circle cx="12" cy="16" r="1.5" fill="currentColor" opacity="0.5" />
    <circle cx="9" cy="14" r="1" fill="currentColor" opacity="0.5" />
    <circle cx="15" cy="14" r="1" fill="currentColor" opacity="0.5" />
  </svg>
);

function LangToggle() {
  const router = useRouter();
  const { locale, pathname, asPath, query } = router;
  const next = locale === 'zh' ? 'en' : 'zh';
  const toggle = () => router.push({ pathname, query }, asPath, { locale: next });
  return (
    <button
      onClick={toggle}
      className="icon-btn"
      title={next === 'en' ? 'Switch to English' : '切换为中文'}
      style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.04em', minWidth: 32 }}
    >
      {locale === 'zh' ? 'EN' : '中'}
    </button>
  );
}

export default function Header() {
  const { t } = useTranslation('common');
  const router = useRouter();
  const { isAuthenticated, loading } = useOptionalAuth();

  const isActive = (path: string) =>
    path === '/' ? router.pathname === '/' : router.pathname.startsWith(path);

  if (loading) return (
    <header style={{ position: 'sticky', top: 0, zIndex: 50, backgroundColor: 'var(--bg-base)', borderBottom: '1px solid var(--border-dim)' }}>
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div style={{ height: 52, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <span style={{ color: 'var(--text-primary)', fontWeight: 700, fontSize: 15 }}>{t('brand.name')}</span>
          <div style={{ width: 120, height: 28, backgroundColor: 'var(--bg-raised)' }} />
        </div>
      </div>
    </header>
  );

  return (
    <header style={{ position: 'sticky', top: 0, zIndex: 50, backgroundColor: 'var(--bg-base)', borderBottom: '1px solid var(--border-dim)' }}>
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div style={{ height: 52, display: 'grid', gridTemplateColumns: '1fr auto 1fr', alignItems: 'center' }}>

          {/* Logo — left */}
          <Link href="/" style={{ textDecoration: 'none', display: 'flex', alignItems: 'center', gap: 8 }}>
            <span className="logo-mark" style={{ width: 28, height: 28 }}>
              <FlaskIcon size={18} />
            </span>
            <span className="hidden sm:block" style={{ color: 'var(--text-primary)', fontWeight: 700, fontSize: 15, letterSpacing: '0.04em' }}>
              {t('brand.name')}
            </span>
          </Link>

          {/* Navigation — true center */}
          <nav className="hidden md:flex items-center gap-8">
            {isAuthenticated ? (
              <>
                {[
                  { href: '/my-dashboard', label: t('nav.dashboard') },
                  { href: '/explore',      label: t('nav.explore') },
                ].map(({ href, label }) => (
                  <Link key={href} href={href} className={`nav-link ${isActive(href) ? 'active' : ''}`}>{label}</Link>
                ))}
              </>
            ) : (
              <Link href="/explore" className={`nav-link ${isActive('/explore') ? 'active' : ''}`}>{t('nav.explore')}</Link>
            )}
          </nav>

          {/* Actions — right */}
          <div className="flex items-center gap-2" style={{ justifyContent: 'flex-end' }}>
            <LangToggle />
            <ThemeToggle />
            {isAuthenticated ? (
              <>
                <UserMenu />
              </>
            ) : (
              <>
                <Link href="/login">
                  <Button variant="ghost" size="sm">{t('auth.login')}</Button>
                </Link>
                <Link href="/register">
                  <Button variant="primary" size="sm">{t('auth.register')}</Button>
                </Link>
              </>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
