import React from 'react';
import Head from 'next/head';
import Header from './Header';
import Footer from './Footer';

interface LayoutProps {
  children: React.ReactNode;
  title?: string;
  description?: string;
  showHeader?: boolean;
  showFooter?: boolean;
  maxWidth?: 'sm' | 'md' | 'lg' | 'xl' | '2xl';
}

const maxWidthClasses = {
  sm: 'max-w-2xl',
  md: 'max-w-3xl',
  lg: 'max-w-4xl',
  xl: 'max-w-5xl',
  '2xl': 'max-w-6xl',
};

export default function Layout({
  children,
  title,
  description,
  showHeader = true,
  showFooter = true,
  maxWidth = '2xl',
}: LayoutProps) {
  return (
    <div className="min-h-screen flex flex-col" style={{ backgroundColor: 'var(--bg-base)' }}>
      {title && (
        <Head>
          <title>{title}</title>
          {description && <meta name="description" content={description} />}
          <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
          <link rel="icon" type="image/x-icon" href="/favicon.svg" />
          <link rel="apple-touch-icon" href="/favicon.svg" />
        </Head>
      )}

      {showHeader && <Header />}

      <main className={`flex-1 w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 ${maxWidthClasses[maxWidth]}`}>
        {children}
      </main>

      {showFooter && <Footer />}
    </div>
  );
}