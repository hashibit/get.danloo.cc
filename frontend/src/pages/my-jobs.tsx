import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { useTranslation } from 'next-i18next';
import { GetStaticProps } from 'next';
import { serverSideTranslations } from 'next-i18next/serverSideTranslations';
import Layout from '../components/Layout';
import { Button } from '../components/Button';
import { useApi } from '../hooks/useApi';
import { useOptionalAuth } from '../contexts/AuthContext';
import { jobService, Job } from '../services/jobs';

type StatusFilter = 'all' | 'pending' | 'in_progress' | 'completed' | 'failed' | 'cancelled';

export default function MyJobs() {
  const router = useRouter();
  const { t } = useTranslation('common');
  const locale = router.locale || 'zh';
  const { user, isAuthenticated, loading: authLoading } = useOptionalAuth();
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, authLoading, router]);

  const {
    data: jobsData,
    loading: jobsLoading,
    error: jobsError,
    refetch: refetchJobs,
  } = useApi(
    () => {
      if (user?.id) {
        return jobService.getUserJobs({ user_id: user.id, limit: 100 });
      }
      return Promise.resolve({ success: true, data: { jobs: [], total: 0 } });
    },
    [isAuthenticated, user?.id]
  );

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: 'var(--bg-base)' }}>
        <span style={{ color: 'var(--text-dim)', fontSize: 13 }}>LOADING...</span>
      </div>
    );
  }

  if (!isAuthenticated) return null;

  const jobs = jobsData?.jobs || [];
  const filteredJobs = jobs.filter(job => statusFilter === 'all' || job.status === statusFilter);

  const handleRetryJob = async (jobId: string) => {
    try {
      await jobService.retryJob(jobId);
      alert(t('myJobs.retrySuccess'));
      refetchJobs();
    } catch (error) {
      alert(t('myJobs.retryFailed'));
    }
  };

  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    const pad = (n: number) => String(n).padStart(2, '0');
    return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`;
  };

  const statusBadge: Record<string, { cls: string; key: string }> = {
    pending:     { cls: 'badge-yellow', key: 'pending' },
    in_progress: { cls: 'badge-blue',   key: 'in_progress' },
    completed:   { cls: 'badge-green',  key: 'completed' },
    failed:      { cls: 'badge-red',    key: 'failed' },
    cancelled:   { cls: 'badge-gray',   key: 'cancelled' },
  };

  const statusOptions: StatusFilter[] = ['all', 'pending', 'in_progress', 'completed', 'failed', 'cancelled'];

  return (
    <Layout
      title={`${t('myJobs.title')} - ${t('brand.name')}`}
      description={t('myJobs.description')}
    >
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20, flexWrap: 'wrap', gap: 12 }}>
        <h1 style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-primary)' }}>
          {t('myJobs.title')}
        </h1>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Button variant="secondary" size="sm" onClick={refetchJobs}>{t('myJobs.refresh')}</Button>
        </div>
      </div>

      {/* Status filter tabs */}
      <div style={{ display: 'flex', gap: 0, marginBottom: 20, borderBottom: '1px solid var(--border-mid)', overflowX: 'auto' }}>
        {statusOptions.map(s => (
          <button
            key={s}
            onClick={() => setStatusFilter(s)}
            style={{
              padding: '8px 14px', fontSize: 12, fontWeight: statusFilter === s ? 600 : 400,
              color: statusFilter === s ? 'var(--text-primary)' : 'var(--text-dim)',
              backgroundColor: 'transparent', border: 'none',
              borderBottom: statusFilter === s ? '1px solid var(--text-primary)' : '1px solid transparent',
              cursor: 'pointer', whiteSpace: 'nowrap', marginBottom: -1,
            }}
          >
            {t(`myJobs.statusFilter.${s}`)}
          </button>
        ))}
      </div>

      {/* Jobs table */}
      {jobsLoading ? (
        <div style={{ padding: '32px 0', textAlign: 'center' }}>
          <span style={{ color: 'var(--text-dim)', fontSize: 13 }}>LOADING...</span>
        </div>
      ) : filteredJobs.length === 0 ? (
        <div style={{ padding: '48px 0', textAlign: 'center', border: '1px solid var(--border-dim)', backgroundColor: 'var(--bg-surface)' }}>
          <p style={{ color: 'var(--text-muted)', fontSize: 24, marginBottom: 12 }}>—</p>
          <p style={{ color: 'var(--text-dim)', fontSize: 14, marginBottom: jobs.length === 0 ? 16 : 0 }}>
            {jobs.length === 0 ? t('myJobs.empty.noJobs') : t('myJobs.empty.noMatch')}
          </p>
          {jobs.length === 0 && (
            <Button variant="primary" size="sm" onClick={() => router.push('/my-create')}>{t('myJobs.startAlchemy')}</Button>
          )}
        </div>
      ) : (
        <div style={{ border: '1px solid var(--border-mid)', backgroundColor: 'var(--bg-surface)', overflow: 'hidden' }}>
          {/* Table header */}
          <div style={{
            display: 'grid', gridTemplateColumns: '1fr 1fr 120px',
            padding: '10px 18px', borderBottom: '1px solid var(--border-mid)', backgroundColor: 'var(--bg-raised)',
          }}>
            {([t('myJobs.table.status'), t('myJobs.table.createdAt'), t('myJobs.table.actions')]).map(h => (
              <span key={h} style={{ fontSize: 11, color: 'var(--text-dim)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.08em' }}>{h}</span>
            ))}
          </div>

          {/* Table rows */}
          {filteredJobs.map((job) => {
            const sb = statusBadge[job.status] || statusBadge.cancelled;
            return (
              <div
                key={job.job_id}
                style={{
                  display: 'grid', gridTemplateColumns: '1fr 1fr 120px',
                  padding: '12px 18px', borderBottom: '1px solid var(--border-dim)', alignItems: 'center',
                }}
                onMouseEnter={e => (e.currentTarget.style.backgroundColor = 'var(--bg-raised)')}
                onMouseLeave={e => (e.currentTarget.style.backgroundColor = 'transparent')}
              >
                <div>
                  <span className={sb.cls} style={{ gap: 4 }}>
                    {job.status === 'in_progress' && (
                      <span style={{ width: 5, height: 5, backgroundColor: 'currentColor', display: 'inline-block' }} />
                    )}
                    {t(`myJobs.statusFilter.${sb.key}`)}
                  </span>
                </div>
                <span style={{ fontSize: 12, color: 'var(--text-dim)' }}>{formatTime(job.created_at)}</span>
                <div>
                  {(job.status === 'failed' || job.status === 'cancelled') && (
                    <Button variant="secondary" size="sm" onClick={() => handleRetryJob(job.job_id)}>{t('myJobs.retry')}</Button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Count */}
      {!jobsLoading && filteredJobs.length > 0 && (
        <p style={{ marginTop: 12, fontSize: 12, color: 'var(--text-muted)', textAlign: 'center' }}>
          {t('myJobs.count', { shown: filteredJobs.length, total: jobs.length })}
        </p>
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
