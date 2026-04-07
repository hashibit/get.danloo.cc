import React from 'react';
import Link from 'next/link';
import { useTranslation } from 'next-i18next';

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

export default function Footer() {
  const { t } = useTranslation('common');

  return (
    <footer
      style={{
        backgroundColor: 'var(--bg-base)',
        borderTop: '1px solid var(--border-dim)',
        padding: '28px 0 20px',
      }}
    >
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row justify-between items-center gap-5">
          {/* Logo */}
          <div className="flex items-center gap-3">
            <div
              style={{
                width: 24, height: 24,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                backgroundColor: 'var(--logo-bg)',
              }}
            >
              <FlaskIcon size={16} />
            </div>
            <span style={{ color: 'var(--text-dim)', fontWeight: 400, fontSize: 12, letterSpacing: '0.04em' }}>
              {t('footer.systemName')}
            </span>
          </div>

          {/* ICP */}
          <div className="text-center" style={{ fontSize: 11, color: 'var(--text-muted)' }}>
            <div style={{ marginBottom: 4 }}>{t('footer.copyright')}</div>
            <div>
              <a
                href="https://beian.miit.gov.cn/"
                target="_blank"
                rel="noopener noreferrer"
                style={{ color: 'var(--text-muted)' }}
              >
                京ICP备18023235号-3
              </a>
            </div>
          </div>

          {/* Links */}
          <div className="flex gap-6" style={{ fontSize: 12, color: 'var(--text-muted)' }}>
            <Link href="/privacy" style={{ color: 'var(--text-muted)' }}>{t('footer.privacy')}</Link>
            <Link href="/terms"   style={{ color: 'var(--text-muted)' }}>{t('footer.terms')}</Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
