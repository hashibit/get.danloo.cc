import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { useTranslation } from 'next-i18next';
import { GetStaticProps } from 'next';
import { serverSideTranslations } from 'next-i18next/serverSideTranslations';
import Link from 'next/link';
import Layout from '../components/Layout';
import { Button } from '../components/Button';
import { Input } from '../components/Input';
import { useApi } from '../hooks/useApi';
import { useOptionalAuth } from '../contexts/AuthContext';
import { pelletService } from '../services/pellets';

export default function Pellets() {
  const router = useRouter();
  const { t } = useTranslation('common');
  const { isAuthenticated, loading: authLoading } = useOptionalAuth();

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, authLoading, router]);

  const [searchTerm, setSearchTerm] = useState('');

  const {
    data: pelletsData,
    loading: pelletsLoading,
    error: pelletsError,
    refetch: refetchPellets,
  } = useApi(
    () => pelletService.getPellets({ limit: 20, sortBy: 'createdAt', sortOrder: 'desc' }),
    [isAuthenticated]
  );

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: 'var(--bg-base)' }}>
        <span style={{ color: 'var(--text-dim)', fontSize: 13 }}>LOADING...</span>
      </div>
    );
  }

  if (!isAuthenticated) return null;

  const pellets = pelletsData?.pellets || [];
  const filtered = pellets.filter(p =>
    p.title.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <Layout
      title={`${t('nav.myPellets')} - ${t('brand.name')}`}
      description={t('myPellets.subtitle')}
    >
      {/* Search */}
      <div style={{ marginBottom: 20 }}>
        <Input
          type="text"
          placeholder={t('pellets.search.placeholder')}
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          leftIcon={
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          }
        />
      </div>

      {/* Pellets Grid */}
      {pelletsLoading ? (
        <div style={{ padding: '32px 0', textAlign: 'center' }}>
          <span style={{ color: 'var(--text-dim)', fontSize: 13 }}>{t('common.loading')}</span>
        </div>
      ) : pelletsError ? (
        <div style={{ padding: '24px', border: '1px solid #f87171', backgroundColor: '#1a0a0a', textAlign: 'center' }}>
          <p style={{ color: '#f87171', fontSize: 13, marginBottom: 12 }}>✕ {pelletsError}</p>
          <Button variant="secondary" size="sm" onClick={() => refetchPellets()}>{t('pellets.card.retry')}</Button>
        </div>
      ) : filtered.length === 0 ? (
        <div style={{ padding: '48px 0', textAlign: 'center' }}>
          <p style={{ color: 'var(--text-muted)', fontSize: 24, marginBottom: 12 }}>⬡</p>
          <p style={{ color: 'var(--text-dim)', fontSize: 14, marginBottom: 16 }}>{t('dashboard.empty.noPellets')}</p>
          <Button variant="primary" onClick={() => router.push('/my-create')}>{t('nav.create')}</Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((pellet) => (
            <div
              key={pellet.id}
              style={{
                backgroundColor: 'var(--bg-surface)',
                border: '1px solid var(--border-dim)',
                padding: '16px',
                cursor: 'pointer',
                display: 'flex',
                flexDirection: 'column',
                gap: 10,
              }}
              onClick={() => router.push(`/pellet/${pellet.id}`)}
              onMouseEnter={e => (e.currentTarget.style.borderColor = 'var(--border-mid)')}
              onMouseLeave={e => (e.currentTarget.style.borderColor = 'var(--border-dim)')}
            >
              {/* Author row */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <div style={{
                  width: 28, height: 28, flexShrink: 0,
                  backgroundColor: 'var(--bg-raised)', border: '1px solid var(--border-mid)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                }}>
                  <span style={{ color: 'var(--text-dim)', fontSize: 10, fontWeight: 700 }}>{t('logo.mark')}</span>
                </div>
                <div>
                  <span style={{ color: 'var(--text-secondary)', fontSize: 12, fontWeight: 500 }}>{t('pellets.card.alchemist')}</span>
                  <span style={{ color: 'var(--text-dim)', fontSize: 11, display: 'block' }}>
                    {new Date((pellet as any).created_at || pellet.createdAt).toLocaleDateString()}
                  </span>
                </div>
                {pellet.tags?.some(tag => tag.id === 'gold') && (
                  <span style={{ marginLeft: 'auto', fontSize: 11, color: 'var(--text-dim)', backgroundColor: 'var(--bg-raised)', border: '1px solid var(--border-mid)', padding: '1px 6px' }}>
                    {t('pellets.card.star')}
                  </span>
                )}
              </div>

              {/* Title */}
              <h3 style={{ color: 'var(--text-primary)', fontSize: 13, fontWeight: 600, lineHeight: 1.4,
                display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                {pellet.title}
              </h3>

              {/* Preview */}
              {pellet.content && (
                <p style={{ color: 'var(--text-dim)', fontSize: 12, lineHeight: 1.5,
                  display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                  {pellet.content.substring(0, 120)}...
                </p>
              )}

              {/* Tags */}
              {pellet.tags && pellet.tags.length > 0 && (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                  {pellet.tags.slice(0, 2).map(tag => (
                    <span key={tag.id} style={{ fontSize: 11, color: 'var(--text-dim)', backgroundColor: 'var(--bg-raised)', border: '1px solid var(--border-mid)', padding: '1px 6px' }}>
                      {tag.name}
                    </span>
                  ))}
                </div>
              )}

              {/* Footer */}
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingTop: 8, borderTop: '1px solid var(--border-dim)' }}>
                <span style={{ color: 'var(--text-dim)', fontSize: 11 }}>5 {t('pellets.meta.readTime')}</span>
                <div style={{ display: 'flex', gap: 10 }}>
                  <button
                    style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', padding: 0 }}
                    onClick={(e) => { e.stopPropagation(); }}
                    onMouseEnter={e => (e.currentTarget.style.color = 'var(--text-secondary)')}
                    onMouseLeave={e => (e.currentTarget.style.color = 'var(--text-muted)')}
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
                    </svg>
                  </button>
                  <button
                    style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', padding: 0 }}
                    onClick={(e) => { e.stopPropagation(); }}
                    onMouseEnter={e => (e.currentTarget.style.color = 'var(--text-secondary)')}
                    onMouseLeave={e => (e.currentTarget.style.color = 'var(--text-muted)')}
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.367 2.684 3 3 0 00-5.367-2.684z" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </Layout>
  );
}

export const getStaticProps: GetStaticProps = async ({ locale = 'en' }) => {
  return {
    props: {
      ...(await serverSideTranslations(locale, ['common'])),
    },
  };
};
