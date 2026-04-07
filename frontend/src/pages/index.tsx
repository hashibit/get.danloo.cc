import React from 'react';
import Link from 'next/link';
import { useTranslation } from 'next-i18next';
import { GetServerSideProps } from 'next';
import { serverSideTranslations } from 'next-i18next/serverSideTranslations';
import Layout from '../components/Layout';
import { Button } from '../components/Button';
import { useOptionalAuth } from '../contexts/AuthContext';

export default function Home() {
  const { t } = useTranslation('common');
  const { isAuthenticated } = useOptionalAuth();

  const STEPS = [
    { num: '01', icon: '↑', key: 'upload' },
    { num: '02', icon: '⚡', key: 'process' },
    { num: '03', icon: '◆', key: 'get' },
  ];

  return (
    <Layout
      title={`${t('brand.name')} - ${t('brand.tagline')}`}
      description={t('brand.description')}
    >
      {/* ── Hero ── */}
      <section style={{ padding: '64px 0 56px', textAlign: 'center' }}>
        <h1 style={{
          fontSize: 'clamp(28px, 5vw, 48px)',
          fontWeight: 900, letterSpacing: '0.04em',
          color: 'var(--text-primary)', marginBottom: 16, lineHeight: 1.15,
        }}>
          {t('home.title')}
        </h1>

        <p style={{
          fontSize: 14, color: 'var(--text-dim)', lineHeight: 1.85,
          maxWidth: 440, margin: '0 auto 36px',
        }}>
          {t('home.subtitle')}
        </p>

        <div style={{ display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap' }}>
          <Link href="/explore">
            <Button variant="primary" size="lg">{t('home.startReading')}</Button>
          </Link>
          {isAuthenticated ? (
            <Link href="/my-create">
              <Button variant="secondary" size="lg">{t('nav.create')}</Button>
            </Link>
          ) : (
            <Link href="/login">
              <Button variant="secondary" size="lg">{t('auth.login')}</Button>
            </Link>
          )}
        </div>
      </section>

      {/* ── Divider ── */}
      <div style={{ borderTop: '1px solid var(--border-dim)', marginBottom: 56 }} />

      {/* ── How it works ── */}
      <section style={{ marginBottom: 64 }}>
        <p style={{
          fontSize: 11, fontWeight: 700, letterSpacing: '0.12em',
          color: 'var(--text-muted)', textAlign: 'center', marginBottom: 40,
          textTransform: 'uppercase',
        }}>
          {t('home.howItWorks')}
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 1, backgroundColor: 'var(--border-dim)' }}>
          {STEPS.map((step, i) => (
            <div key={i} style={{
              backgroundColor: 'var(--bg-surface)',
              padding: '28px 24px',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
                <span style={{ fontSize: 10, color: 'var(--text-muted)', fontWeight: 700, letterSpacing: '0.08em', minWidth: 20 }}>
                  {step.num}
                </span>
                <span style={{
                  width: 32, height: 32, flexShrink: 0,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  backgroundColor: 'var(--bg-raised)', border: '1px solid var(--border-mid)',
                  fontSize: 14, color: 'var(--text-secondary)',
                }}>
                  {step.icon}
                </span>
              </div>
              <p style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 8 }}>
                {t(`home.steps.${step.key}.title`)}
              </p>
              <p style={{ fontSize: 12, color: 'var(--text-dim)', lineHeight: 1.75 }}>
                {t(`home.steps.${step.key}.desc`)}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* ── Explore CTA ── */}
      <section style={{
        backgroundColor: 'var(--bg-surface)',
        border: '1px solid var(--border-mid)',
        padding: '36px 32px',
        display: 'flex', flexWrap: 'wrap',
        alignItems: 'center', justifyContent: 'space-between',
        gap: 20,
        marginBottom: 16,
      }}>
        <div>
          <p style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 6 }}>
            {t('home.cta.title')}
          </p>
          <p style={{ fontSize: 12, color: 'var(--text-dim)', lineHeight: 1.7, maxWidth: 400 }}>
            {t('home.cta.subtitle')}
          </p>
        </div>
        <div style={{ display: 'flex', gap: 10, flexShrink: 0 }}>
          <Link href="/explore">
            <Button variant="primary">{t('home.cta.browsePellets')}</Button>
          </Link>
          <Link href="/my-dashboard">
            <Button variant="ghost">{t('home.cta.getStarted')}</Button>
          </Link>
        </div>
      </section>
    </Layout>
  );
}

export const getServerSideProps: GetServerSideProps = async ({ locale = 'en' }) => {
  return {
    props: {
      ...(await serverSideTranslations(locale, ['common'])),
    },
  };
};
