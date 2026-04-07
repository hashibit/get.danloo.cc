import React, { useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { useTranslation } from 'next-i18next';
import { GetStaticProps } from 'next';
import { serverSideTranslations } from 'next-i18next/serverSideTranslations';
import Layout from '../components/Layout';
import { Button } from '../components/Button';
import { useApi } from '../hooks/useApi';
import { useOptionalAuth } from '../contexts/AuthContext';
import { materialService } from '../services/materials';
import { pelletService } from '../services/pellets';

export default function Dashboard() {
  const router = useRouter();
  const { t } = useTranslation('common');
  const { isAuthenticated, loading: authLoading } = useOptionalAuth();

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, authLoading, router]);

  const { data: materialsData, loading: materialsLoading, error: materialsError } =
    useApi(() => materialService.getMaterials({ limit: 5 }), [isAuthenticated]);

  const { data: pelletsData, loading: pelletsLoading, error: pelletsError } =
    useApi(() => pelletService.getPellets({ limit: 5, sortBy: 'createdAt', sortOrder: 'desc' }), [isAuthenticated]);

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: 'var(--bg-base)' }}>
        <span style={{ color: 'var(--text-dim)', fontSize: 13 }}>LOADING...</span>
      </div>
    );
  }

  if (!isAuthenticated) return null;

  const materials = materialsData?.materials || [];
  const pellets = pelletsData?.pellets || [];

  return (
    <Layout
      title={`${t('dashboard.title')} - ${t('brand.name')}`}
      description={`Your ${t('brand.name')} ${t('dashboard.title')}`}
    >
      {/* Hero Section */}
      <div style={{
        backgroundColor: 'var(--bg-surface)',
        border: '1px solid var(--border-mid)',
        padding: '24px 28px',
        marginBottom: 28,
      }}>
        <h1 style={{ fontSize: 20, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 8 }}>
          {t('dashboard.welcomeTitle')}
        </h1>
        <p style={{ color: 'var(--text-dim)', fontSize: 13, marginBottom: 18, lineHeight: 1.6, maxWidth: 560 }}>
          {t('dashboard.welcomeSubtitle')}
        </p>
        <div className="flex flex-wrap gap-3">
          <Link href="/my-create">
            <Button variant="primary" size="sm">{t('nav.create')}</Button>
          </Link>
          <Link href="/my-materials?upload=true">
            <Button variant="secondary" size="sm">{t('nav.upload')}</Button>
          </Link>
        </div>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-7">
        {[
          { value: pellets.length,    label: t('dashboard.stats.totalPellets'), icon: '⬡' },
          { value: pellets.filter(p => p.tags?.some(tag => tag.id === 'gold')).length,
                                       label: t('dashboard.stats.goldenPellets'), icon: '★' },
          { value: materials.length,  label: t('dashboard.stats.materials'),    icon: '▣' },
        ].map((stat) => (
          <div
            key={stat.label}
            style={{
              backgroundColor: 'var(--bg-surface)',
              border: '1px solid var(--border-mid)',
              padding: '18px 22px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <div>
              <div style={{ fontSize: 32, fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1 }}>{stat.value}</div>
              <div style={{ fontSize: 12, color: 'var(--text-dim)', marginTop: 4 }}>{stat.label}</div>
            </div>
            <span style={{ fontSize: 28, color: 'var(--text-muted)', opacity: 1 }}>{stat.icon}</span>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Materials */}
        <div style={{ backgroundColor: 'var(--bg-surface)', border: '1px solid var(--border-mid)' }}>
          <div style={{ padding: '12px 18px', borderBottom: '1px solid var(--border-dim)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div className="flex items-center gap-2">
              <span style={{ color: 'var(--text-dim)', fontSize: 14 }}>▣</span>
              <span style={{ color: 'var(--text-primary)', fontSize: 13, fontWeight: 600 }}>{t('dashboard.sections.recentMaterials')}</span>
            </div>
            <Link href="/my-materials" style={{ color: 'var(--text-dim)', fontSize: 12, textDecoration: 'none' }}>
              {t('dashboard.sections.viewAll')} →
            </Link>
          </div>

          <div style={{ padding: '10px 0' }}>
            {materialsLoading ? (
              <div style={{ padding: '10px 18px' }}>
                {[1, 2, 3].map(i => (
                  <div key={i} style={{ height: 54, backgroundColor: 'var(--bg-raised)', marginBottom: 8 }} />
                ))}
              </div>
            ) : materialsError ? (
              <div style={{ padding: '24px 18px', textAlign: 'center' }}>
                <p style={{ color: '#f87171', fontSize: 13, marginBottom: 12 }}>✕ {materialsError}</p>
                <Button variant="secondary" size="sm" onClick={() => window.location.reload()}>
                  {t('dashboard.actions.tryAgain')}
                </Button>
              </div>
            ) : materials.length > 0 ? (
              materials.map((material) => (
                <div
                  key={material.id}
                  style={{ padding: '10px 18px', borderBottom: '1px solid var(--border-dim)', cursor: 'default' }}
                  onMouseEnter={e => (e.currentTarget.style.backgroundColor = 'var(--bg-raised)')}
                  onMouseLeave={e => (e.currentTarget.style.backgroundColor = 'transparent')}
                >
                  <p style={{ color: 'var(--text-primary)', fontSize: 13, fontWeight: 500, marginBottom: 4,
                    overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {material.title}
                  </p>
                  <div className="flex items-center gap-3">
                    <span style={{ fontSize: 11, color: 'var(--text-dim)', backgroundColor: 'var(--bg-raised)', border: '1px solid var(--border-mid)', padding: '1px 6px' }}>
                      {material.content_type}
                    </span>
                    <span style={{ fontSize: 11, color: 'var(--text-dim)' }}>
                      {new Date(material.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              ))
            ) : (
              <div style={{ padding: '40px 18px', textAlign: 'center' }}>
                <p style={{ color: 'var(--text-muted)', fontSize: 13, marginBottom: 14 }}>
                  {t('dashboard.empty.noMaterials')}
                </p>
                <Link href="/my-materials">
                  <Button variant="primary" size="sm">{t('dashboard.empty.uploadFirst')}</Button>
                </Link>
              </div>
            )}
          </div>
        </div>

        {/* Recent Pellets */}
        <div style={{ backgroundColor: 'var(--bg-surface)', border: '1px solid var(--border-mid)' }}>
          <div style={{ padding: '12px 18px', borderBottom: '1px solid var(--border-dim)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div className="flex items-center gap-2">
              <span style={{ color: 'var(--text-dim)', fontSize: 14 }}>⬡</span>
              <span style={{ color: 'var(--text-primary)', fontSize: 13, fontWeight: 600 }}>{t('dashboard.sections.recentPellets')}</span>
            </div>
            <Link href="/my-pellets" style={{ color: 'var(--text-dim)', fontSize: 12, textDecoration: 'none' }}>
              {t('dashboard.sections.viewAll')} →
            </Link>
          </div>

          <div style={{ padding: '10px 0' }}>
            {pelletsLoading ? (
              <div style={{ padding: '10px 18px' }}>
                {[1, 2, 3].map(i => (
                  <div key={i} style={{ height: 66, backgroundColor: 'var(--bg-raised)', marginBottom: 8 }} />
                ))}
              </div>
            ) : pelletsError ? (
              <div style={{ padding: '24px 18px', textAlign: 'center' }}>
                <p style={{ color: '#f87171', fontSize: 13, marginBottom: 12 }}>✕ {pelletsError}</p>
                <Button variant="secondary" size="sm" onClick={() => window.location.reload()}>
                  {t('dashboard.actions.tryAgain')}
                </Button>
              </div>
            ) : pellets.length > 0 ? (
              pellets.map((pellet) => (
                <div
                  key={pellet.id}
                  style={{ padding: '10px 18px', borderBottom: '1px solid var(--border-dim)' }}
                  onMouseEnter={e => (e.currentTarget.style.backgroundColor = 'var(--bg-raised)')}
                  onMouseLeave={e => (e.currentTarget.style.backgroundColor = 'transparent')}
                >
                  <div className="flex items-start justify-between" style={{ marginBottom: 6 }}>
                    <p style={{ color: 'var(--text-primary)', fontSize: 13, fontWeight: 500, flex: 1, paddingRight: 8,
                      overflow: 'hidden', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical' }}>
                      {pellet.title}
                    </p>
                    {pellet.tags?.some(tag => tag.id === 'gold') && (
                      <span style={{ fontSize: 11, color: 'var(--text-dim)', backgroundColor: 'var(--bg-raised)', border: '1px solid var(--border-mid)', padding: '1px 5px', whiteSpace: 'nowrap' }}>
                        ★
                      </span>
                    )}
                  </div>
                  <div className="flex items-center justify-between">
                    <span style={{ fontSize: 11, color: 'var(--text-dim)' }}>
                      {new Date(pellet.createdAt).toLocaleDateString()}
                    </span>
                    <div className="flex gap-2">
                      <Link
                        href={`/pellet/${pellet.id}`}
                        style={{ fontSize: 11, padding: '2px 8px', color: 'var(--text-secondary)', border: '1px solid var(--border-mid)', textDecoration: 'none' }}
                        onMouseEnter={e => { (e.currentTarget as HTMLAnchorElement).style.color = 'var(--text-primary)'; (e.currentTarget as HTMLAnchorElement).style.borderColor = 'var(--text-muted)'; }}
                        onMouseLeave={e => { (e.currentTarget as HTMLAnchorElement).style.color = 'var(--text-secondary)'; (e.currentTarget as HTMLAnchorElement).style.borderColor = 'var(--border-mid)'; }}
                      >
                        {t('dashboard.actions.read')}
                      </Link>
                      <button
                        style={{ fontSize: 11, padding: '2px 8px', color: 'var(--text-dim)', border: '1px solid var(--border-mid)', backgroundColor: 'transparent', cursor: 'pointer' }}
                        onMouseEnter={e => { e.currentTarget.style.color = 'var(--text-secondary)'; e.currentTarget.style.borderColor = 'var(--text-muted)'; }}
                        onMouseLeave={e => { e.currentTarget.style.color = 'var(--text-dim)'; e.currentTarget.style.borderColor = 'var(--border-mid)'; }}
                        onClick={() => alert(`Sharing pellet: ${pellet.title}`)}
                      >
                        {t('dashboard.actions.share')}
                      </button>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div style={{ padding: '40px 18px', textAlign: 'center' }}>
                <p style={{ color: 'var(--text-muted)', fontSize: 13, marginBottom: 14 }}>
                  {t('dashboard.empty.noPellets')}
                </p>
                <Link href="/my-create">
                  <Button variant="primary" size="sm">{t('dashboard.empty.createFirst')}</Button>
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>
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
