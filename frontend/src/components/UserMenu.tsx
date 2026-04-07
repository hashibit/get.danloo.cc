import React, { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import { useTranslation } from 'next-i18next';
import { useOptionalAuth } from '../contexts/AuthContext';
import { User } from '../services/auth';

export default function UserMenu() {
  const { t } = useTranslation('common');
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const { user, isAuthenticated, logout } = useOptionalAuth();

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleLogout = () => { logout(); setIsOpen(false); };

  const getUserInitials = (user: User): string => {
    if (user.username) return user.username.slice(0, 2).toUpperCase();
    if (user.email) return user.email.slice(0, 2).toUpperCase();
    return 'U';
  };

  if (!isAuthenticated) return null;

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        style={{
          display: 'flex', alignItems: 'center', gap: 7,
          padding: '4px 10px',
          border: '1px solid var(--border-mid)', backgroundColor: 'transparent', cursor: 'pointer',
        }}
        onMouseEnter={e => (e.currentTarget.style.borderColor = 'var(--text-muted)')}
        onMouseLeave={e => (e.currentTarget.style.borderColor = 'var(--border-mid)')}
      >
        <span style={{
          color: 'var(--text-primary)', fontSize: 13, fontWeight: 400,
          maxWidth: 100, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
        }}>
          {user?.username || user?.email || 'user'}
        </span>
        <span style={{ color: 'var(--text-dim)', fontSize: 9, lineHeight: 1 }}>
          {isOpen ? '▲' : '▼'}
        </span>
      </button>

      {isOpen && (
        <div style={{
          position: 'absolute', right: 0, top: '100%', marginTop: 4,
          width: 200, backgroundColor: 'var(--bg-surface)', border: '1px solid var(--border-mid)', zIndex: 50,
        }}>
          <div style={{ padding: '10px 14px', borderBottom: '1px solid var(--border-dim)' }}>
            <p style={{ color: 'var(--text-primary)', fontSize: 13, fontWeight: 600, marginBottom: 2 }}>
              {user?.username || 'user'}
            </p>
            <p style={{ color: 'var(--text-dim)', fontSize: 12 }}>{user?.email}</p>
          </div>

          <div style={{ padding: '4px 0' }}>
            {[
              { href: '/profile',      label: t('userMenu.settings') },
              { href: '/my-materials', label: t('userMenu.materials') },
              { href: '/my-pellets',   label: t('userMenu.pellets') },
              { href: '/my-jobs',      label: t('userMenu.jobs') },
            ].map(item => (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setIsOpen(false)}
                style={{ display: 'block', padding: '7px 14px', color: 'var(--text-secondary)', fontSize: 13, textDecoration: 'none' }}
                onMouseEnter={e => { (e.currentTarget as HTMLAnchorElement).style.color = 'var(--text-primary)'; (e.currentTarget as HTMLAnchorElement).style.backgroundColor = 'var(--bg-raised)'; }}
                onMouseLeave={e => { (e.currentTarget as HTMLAnchorElement).style.color = 'var(--text-secondary)'; (e.currentTarget as HTMLAnchorElement).style.backgroundColor = 'transparent'; }}
              >
                {item.label}
              </Link>
            ))}
          </div>

          <div style={{ borderTop: '1px solid var(--border-dim)' }}>
            <button
              onClick={handleLogout}
              style={{
                display: 'block', width: '100%', textAlign: 'left',
                padding: '7px 14px', color: '#f87171', fontSize: 13,
                backgroundColor: 'transparent', border: 'none', cursor: 'pointer',
              }}
              onMouseEnter={e => (e.currentTarget.style.backgroundColor = 'var(--alert-error-bg)')}
              onMouseLeave={e => (e.currentTarget.style.backgroundColor = 'transparent')}
            >
              {t('userMenu.logout')}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
