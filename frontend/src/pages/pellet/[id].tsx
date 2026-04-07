import React, { useRef, useEffect, useState } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import Link from 'next/link';
import Header from '../../components/Header';
import { Button } from '../../components/Button';
import { useApi } from '../../hooks/useApi';
import { useOptionalAuth } from '../../contexts/AuthContext';
import { pelletService } from '../../services/pellets';
import { serverSideTranslations } from 'next-i18next/serverSideTranslations';
import { useTranslation } from 'next-i18next';
import ReactMarkdown, { Components } from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import mermaid from 'mermaid';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { dracula } from 'react-syntax-highlighter/dist/cjs/styles/prism';
import { oneLight } from 'react-syntax-highlighter/dist/cjs/styles/prism';
import { useTheme } from '../../contexts/ThemeContext';

function useMermaidRender(chart: string, mermaidTheme: string, onRender?: () => void) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!ref.current) return;
    mermaid.initialize({ startOnLoad: false, theme: mermaidTheme as any, securityLevel: 'loose' });
    const id = `mermaid-${Math.random().toString(36).slice(2)}`;
    mermaid.render(id, chart)
      .then(({ svg }) => {
        if (ref.current) ref.current.innerHTML = svg;
        onRender?.();
      })
      .catch(() => { if (ref.current) ref.current.textContent = chart; });
  }, [chart, mermaidTheme, onRender]);
  return ref;
}

function MermaidChart({ chart, mermaidTheme, onClick }: { chart: string; mermaidTheme: string; onClick?: () => void }) {
  const ref = useMermaidRender(chart, mermaidTheme);

  return (
    <div
      ref={ref}
      onClick={onClick}
      style={{
        overflowX: 'auto', margin: '16px 0',
        cursor: onClick ? 'zoom-in' : undefined,
        position: 'relative',
      }}
    />
  );
}

function MermaidModal({ chart, mermaidTheme, onClose }: { chart: string; mermaidTheme: string; onClose: () => void }) {
  const [rendered, setRendered] = useState(false);
  const ref = useMermaidRender(chart, mermaidTheme, () => setRendered(true));
  const containerRef = useRef<HTMLDivElement>(null);
  const [scale, setScale] = useState(1);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [initialScale, setInitialScale] = useState(1);
  const [initialPosition, setInitialPosition] = useState({ x: 0, y: 0 });

  // Auto-fit on render
  useEffect(() => {
    if (!rendered) return;
    const diagram = ref.current?.firstElementChild;
    const container = containerRef.current;
    if (!diagram || !container) return;

    // Temporarily remove transform to get original size
    diagram.removeAttribute('style');
    const diagramRect = diagram.getBoundingClientRect();
    const containerRect = container.getBoundingClientRect();

    const scaleX = containerRect.width / diagramRect.width;
    const scaleY = containerRect.height / diagramRect.height;
    const fitScale = Math.min(scaleX, scaleY);

    const centeredX = (containerRect.width - diagramRect.width * fitScale) / 2;
    const centeredY = (containerRect.height - diagramRect.height * fitScale) / 2;

    const newScale = fitScale;
    const newPos = { x: centeredX, y: centeredY };

    setScale(newScale);
    setPosition(newPos);
    setInitialScale(newScale);
    setInitialPosition(newPos);
    setRendered(false);
  }, [rendered, ref, containerRef]);

  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
    document.addEventListener('keydown', handleKey);
    return () => document.removeEventListener('keydown', handleKey);
  }, [onClose]);

  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? -0.1 : 0.1;
    setScale(s => Math.max(0.1, s + delta));
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    setIsDragging(true);
    setDragStart({ x: e.clientX - position.x, y: e.clientY - position.y });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging) return;
    setPosition({ x: e.clientX - dragStart.x, y: e.clientY - dragStart.y });
  };

  const handleMouseUp = () => setIsDragging(false);

  const resetView = () => {
    setScale(initialScale);
    setPosition(initialPosition);
  };

  return (
    <div
      onClick={onClose}
      style={{
        position: 'fixed', inset: 0, zIndex: 1000,
        backgroundColor: 'rgba(0,0,0,0.5)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        userSelect: 'none',
      }}
    >
      <div
        onClick={e => e.stopPropagation()}
        style={{
          position: 'relative',
          backgroundColor: 'var(--bg-surface)',
          border: '1px solid var(--border-mid)',
          width: '90vw', height: '90vh',
          display: 'flex', flexDirection: 'column',
          overflow: 'hidden',
        }}
      >
        {/* Controls */}
        <div style={{
          position: 'absolute', top: 12, right: 12, zIndex: 10,
          display: 'flex', gap: 8,
        }}>
          <button
            onClick={() => setScale(s => s * 1.25)}
            style={{
              width: 28, height: 28, display: 'flex', alignItems: 'center', justifyContent: 'center',
              backgroundColor: 'var(--bg-raised)', border: '1px solid var(--border-mid)',
              color: 'var(--text-secondary)', cursor: 'pointer', fontSize: 16, lineHeight: 1,
            }}
          >+</button>
          <button
            onClick={() => setScale(s => s / 1.25)}
            style={{
              width: 28, height: 28, display: 'flex', alignItems: 'center', justifyContent: 'center',
              backgroundColor: 'var(--bg-raised)', border: '1px solid var(--border-mid)',
              color: 'var(--text-secondary)', cursor: 'pointer', fontSize: 16, lineHeight: 1,
            }}
          >−</button>
          <button
            onClick={resetView}
            style={{
              width: 36, height: 28, display: 'flex', alignItems: 'center', justifyContent: 'center',
              backgroundColor: 'var(--bg-raised)', border: '1px solid var(--border-mid)',
              color: 'var(--text-secondary)', cursor: 'pointer', fontSize: 10,
            }}
          >↺</button>
          <button
            onClick={onClose}
            style={{
              width: 28, height: 28, display: 'flex', alignItems: 'center', justifyContent: 'center',
              backgroundColor: 'var(--bg-raised)', border: '1px solid var(--border-mid)',
              color: 'var(--text-secondary)', cursor: 'pointer', fontSize: 14, lineHeight: 1,
            }}
          >✕</button>
        </div>

        {/* Diagram */}
        <div
          ref={containerRef}
          onWheel={handleWheel}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
          style={{ overflow: 'hidden', flex: 1, cursor: isDragging ? 'grabbing' : 'grab' }}
        >
          <div
            ref={ref}
            style={{
              transform: `translate(${position.x}px, ${position.y}px) scale(${scale})`,
              transformOrigin: '0 0',
              position: 'absolute',
              top: 0, left: 0,
            }}
          />
        </div>
      </div>
    </div>
  );
}

export default function PelletDetail() {
  const router = useRouter();
  const { id } = router.query;
  const { t } = useTranslation('common');
  const { user, isAuthenticated, loading: authLoading } = useOptionalAuth();
  const { theme } = useTheme();
  const [isUpdatingVisibility, setIsUpdatingVisibility] = useState(false);
  const [localVisibility, setLocalVisibility] = useState<'public' | 'private'>('private');
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [mermaidModal, setMermaidModal] = useState<string | null>(null);
  const editRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (editRef.current && !editRef.current.contains(e.target as Node)) setIsEditOpen(false);
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const { data: pellet, loading: pelletLoading, error, refetch } = useApi(
    () => pelletService.getPellet(id as string),
    [id]
  );

  useEffect(() => {
    if (pellet?.visibility) setLocalVisibility(pellet.visibility);
  }, [pellet?.visibility]);

  const pelletOwnerId = pellet ? ((pellet as any).user_id ?? pellet.userId) : undefined;
  const isOwner = isAuthenticated && pellet && user && pelletOwnerId === user.id;
  const loading = authLoading || pelletLoading;

  const handleVisibilityChange = async (newVisibility: 'public' | 'private') => {
    setIsUpdatingVisibility(true);
    try {
      const response = await pelletService.updateVisibility(id as string, newVisibility);
      if (response.success && response.data) {
        setLocalVisibility(newVisibility);
        refetch();
      } else {
        alert(response.error?.message || t('pellet.updateFailed'));
      }
    } catch {
      alert(t('pellet.updateFailed'));
    } finally {
      setIsUpdatingVisibility(false);
    }
  };


  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen" style={{ backgroundColor: 'var(--bg-base)' }}>
        <Header />
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            <div style={{ height: 40, backgroundColor: 'var(--bg-raised)' }} />
            <div style={{ height: 16, backgroundColor: 'var(--bg-raised)' }} />
            <div style={{ height: 16, width: '60%', backgroundColor: 'var(--bg-raised)' }} />
          </div>
        </div>
      </div>
    );
  }

  // Error / not found
  if (error || !pellet) {
    const isAuthError = error && (error.includes('401') || error.includes('Authentication required'));

    return (
      <div className="min-h-screen" style={{ backgroundColor: 'var(--bg-base)' }}>
        <Header />
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12 text-center">
          {isAuthError ? (
            <>
              <p style={{ color: 'var(--text-primary)', fontSize: 20, fontWeight: 700, marginBottom: 8 }}>{t('pellet.loginRequired.title')}</p>
              <p style={{ color: 'var(--text-dim)', fontSize: 14, marginBottom: 20 }}>{t('pellet.loginRequired.desc')}</p>
              <div style={{ display: 'flex', gap: 10, justifyContent: 'center' }}>
                <Link href="/login"><Button variant="primary">{t('auth.login')}</Button></Link>
                <Link href="/explore"><Button variant="ghost">{t('pellet.loginRequired.browse')}</Button></Link>
              </div>
            </>
          ) : (
            <>
              <p style={{ color: '#f87171', fontSize: 20, fontWeight: 700, marginBottom: 8 }}>
                {error ? t('pellet.loadFailed') : t('pellet.notFound')}
              </p>
              <p style={{ color: 'var(--text-dim)', fontSize: 14, marginBottom: 20 }}>
                {error || t('pellet.notFoundDesc')}
              </p>
              <div style={{ display: 'flex', gap: 10, justifyContent: 'center' }}>
                <Link href="/explore"><Button variant="primary">{t('pellet.browse')}</Button></Link>
                {error && <Button variant="ghost" onClick={() => window.location.reload()}>{t('pellet.retry')}</Button>}
              </div>
            </>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen" style={{ backgroundColor: 'var(--bg-base)' }}>
      {mermaidModal && (
        <MermaidModal
          chart={mermaidModal}
          mermaidTheme={theme === 'dark' ? 'dark' : 'neutral'}
          onClose={() => setMermaidModal(null)}
        />
      )}
      <Head>
        <title>{pellet.title || t('pellet.defaultTitle')} - {t('brand.name')}</title>
        <meta name="description" content={`${pellet.title || t('pellet.defaultTitle')} - ${t('brand.name')}`} />
      </Head>

      <Header />

      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 md:py-12">
        <div style={{ backgroundColor: 'var(--bg-surface)', border: '1px solid var(--border-mid)' }}>
          {/* Article header */}
          <div style={{ padding: '18px 24px', borderBottom: '1px solid var(--border-dim)' }}>
            {/* Meta row */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <div style={{
                  width: 32, height: 32, flexShrink: 0,
                  backgroundColor: 'var(--bg-raised)', border: '1px solid var(--border-mid)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                }}>
                  <span style={{ color: 'var(--text-dim)', fontSize: 11, fontWeight: 700 }}>AI</span>
                </div>
                <div>
                  <p style={{ color: 'var(--text-secondary)', fontSize: 13, fontWeight: 600 }}>{t('pellet.author')}</p>
                  <p style={{ color: 'var(--text-dim)', fontSize: 12 }}>
                    8 min · {new Date(pellet.createdAt || new Date()).toLocaleDateString(router.locale, { year: 'numeric', month: 'short', day: 'numeric' })}
                  </p>
                </div>
              </div>

              {/* Visibility badge */}
              <span style={{
                fontSize: 11, color: localVisibility === 'public' ? 'var(--accent-success)' : 'var(--text-muted)',
                border: `1px solid ${localVisibility === 'public' ? 'var(--accent-success)' : 'var(--border-mid)'}`,
                padding: '2px 8px', letterSpacing: '0.04em',
              }}>
                {localVisibility === 'public' ? t('pellet.visibility.public') : t('pellet.visibility.private')}
              </span>
            </div>

            {/* Action bar */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingTop: 12, borderTop: '1px solid var(--border-dim)' }}>
              <div style={{ display: 'flex', gap: 16 }}>
                <button className="action-btn">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                  </svg>
                  6.7K
                </button>
                <button className="action-btn">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                  </svg>
                  21
                </button>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                {/* Bookmark */}
                <button className="action-btn" title={t('pellet.actions.bookmark')}>
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
                  </svg>
                </button>
                {/* Share */}
                <button className="action-btn" title={t('pellet.actions.share')}>
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.367 2.684 3 3 0 00-5.367-2.684z" />
                  </svg>
                </button>
                {/* Edit (owner only) */}
                {isOwner && (
                  <div ref={editRef} style={{ position: 'relative' }}>
                    <button
                      className="action-btn"
                      title={t('pellet.actions.edit')}
                      onClick={() => setIsEditOpen(v => !v)}
                      style={{ color: isEditOpen ? 'var(--text-primary)' : undefined }}
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                      </svg>
                    </button>

                    {isEditOpen && (
                      <div style={{
                        position: 'absolute', right: 0, bottom: 'calc(100% + 8px)',
                        width: 200, backgroundColor: 'var(--bg-surface)',
                        border: '1px solid var(--border-mid)', zIndex: 50,
                        padding: '12px 14px',
                      }}>
                        <p style={{ fontSize: 11, color: 'var(--text-dim)', marginBottom: 10, letterSpacing: '0.06em', textTransform: 'uppercase' }}>{t('pellet.visibility.label')}</p>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                          {(['public', 'private'] as const).map(v => (
                            <button
                              key={v}
                              onClick={() => { handleVisibilityChange(v); setIsEditOpen(false); }}
                              disabled={isUpdatingVisibility}
                              style={{
                                display: 'flex', alignItems: 'center', gap: 8,
                                padding: '7px 10px', fontSize: 13, cursor: 'pointer',
                                backgroundColor: localVisibility === v ? 'var(--bg-raised)' : 'transparent',
                                color: localVisibility === v ? 'var(--text-primary)' : 'var(--text-secondary)',
                                border: `1px solid ${localVisibility === v ? 'var(--border-mid)' : 'transparent'}`,
                                textAlign: 'left', width: '100%',
                                opacity: isUpdatingVisibility ? 0.5 : 1,
                              }}
                            >
                              <span style={{ fontSize: 10, color: v === 'public' ? 'var(--accent-success)' : 'var(--text-muted)' }}>●</span>
                              <span style={{ flex: 1 }}>{v === 'public' ? t('pellet.visibility.public') : t('pellet.visibility.private')}</span>
                              {localVisibility === v && <span style={{ fontSize: 10, color: 'var(--text-dim)' }}>✓</span>}
                            </button>
                          ))}
                        </div>
                        {localVisibility === 'public' && (
                          <p style={{ marginTop: 10, fontSize: 11, color: 'var(--text-muted)', lineHeight: 1.5 }}>
                            {t('pellet.visibility.publicHint')}
                          </p>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Article content */}
          <div style={{ padding: '24px' }} className="article-content">
            {pellet?.content ? (
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                rehypePlugins={[rehypeRaw]}
                components={{
                  // Strip the outer <pre> react-markdown renders so SyntaxHighlighter
                  // is the only container — prevents the double-box issue.
                  pre: ({ children }) => <>{children}</>,
                  code: (props: any) => {
                    const { inline, className, children, ...rest } = props;
                    const match = /language-(\w+)/.exec(className || '');
                    const lang = match?.[1];

                    if (!inline && lang === 'mermaid') {
                      const chartStr = String(children).replace(/\n$/, '');
                      return <MermaidChart chart={chartStr} mermaidTheme={theme === 'dark' ? 'dark' : 'neutral'} onClick={() => setMermaidModal(chartStr)} />;
                    }

                    if (!inline && lang) {
                      return (
                        <SyntaxHighlighter
                          language={lang}
                          style={theme === 'dark' ? dracula : oneLight}
                          customStyle={{
                            margin: '1.5rem 0',
                            fontSize: '13px',
                            lineHeight: '1.65',
                            borderRadius: 0,
                            border: theme === 'dark' ? '1px solid #44475a' : '1px solid #e2e4e6',
                          }}
                          codeTagProps={{ style: { fontFamily: "'JetBrains Mono', 'SF Mono', monospace", fontWeight: 500 } }}
                        >
                          {String(children).replace(/\n$/, '')}
                        </SyntaxHighlighter>
                      );
                    }

                    return <code className={className} {...rest}>{children}</code>;
                  },
                } as Components}
              >
                {pellet.content}
              </ReactMarkdown>
            ) : (
              <p style={{ color: 'var(--text-dim)', fontSize: 14 }}>{t('pellet.empty')}</p>
            )}
          </div>

          {/* Tags */}
          {pellet.tags && pellet.tags.length > 0 && (
            <div style={{ padding: '0 24px 16px', borderTop: '1px solid var(--border-dim)', paddingTop: 16, display: 'flex', flexWrap: 'wrap', gap: 6 }}>
              {pellet.tags.map(tag => (
                <span key={tag.id} style={{ fontSize: 11, color: 'var(--text-dim)', backgroundColor: 'var(--bg-raised)', border: '1px solid var(--border-mid)', padding: '2px 8px' }}>
                  {tag.name}
                </span>
              ))}
            </div>
          )}

          {/* Back nav */}
          <div style={{ padding: '16px 24px', borderTop: '1px solid var(--border-dim)', textAlign: 'center' }}>
            <Link href="/my-pellets">
              <Button variant="ghost">{t('pellet.back')}</Button>
            </Link>
          </div>
        </div>
      </main>
    </div>
  );
}

export async function getServerSideProps({ locale }: { locale: string }) {
  return {
    props: {
      ...(await serverSideTranslations(locale, ['common'])),
    },
  };
}
