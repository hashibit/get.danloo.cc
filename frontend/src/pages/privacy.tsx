import React from 'react';
import { useTranslation } from 'next-i18next';
import { GetStaticProps } from 'next';
import { serverSideTranslations } from 'next-i18next/serverSideTranslations';
import Layout from '../components/Layout';

export default function Privacy() {
  const { t } = useTranslation('common');

  return (
    <Layout
      title={`${t('privacy.title')} - ${t('brand.name')}`}
      description={t('privacy.description')}
    >
      <div style={{ maxWidth: 880, margin: '0 auto', padding: '28px 20px 60px' }}>
        <div style={{
          backgroundColor: 'var(--bg-surface)',
          border: '1px solid var(--border-mid)',
          padding: '32px',
        }}>
          <h1 style={{
            fontSize: 28,
            fontWeight: 700,
            color: 'var(--text-primary)',
            marginBottom: 8,
          }}>
            {t('privacy.title')}
          </h1>

          <p style={{
            fontSize: 13,
            color: 'var(--text-dim)',
            marginBottom: 28,
          }}>
            {t('privacy.lastUpdated')}
          </p>

          <div style={{ color: 'var(--text-secondary)', fontSize: 14, lineHeight: 1.8 }}>
            <section style={{ marginBottom: 28 }}>
              <h2 style={{
                fontSize: 18,
                fontWeight: 600,
                color: 'var(--text-primary)',
                marginBottom: 12,
                paddingBottom: 8,
                borderBottom: '1px solid var(--border-dim)',
              }}>
                {t('privacy.overview')}
              </h2>
              <p>{t('privacy.overviewContent')}</p>
            </section>

            <section style={{ marginBottom: 28 }}>
              <h2 style={{
                fontSize: 18,
                fontWeight: 600,
                color: 'var(--text-primary)',
                marginBottom: 12,
                paddingBottom: 8,
                borderBottom: '1px solid var(--border-dim)',
              }}>
                {t('privacy.infoCollection')}
              </h2>
              <p style={{ fontWeight: 600, marginBottom: 12 }}>{t('privacy.infoTypes')}</p>
              <ul style={{ listStyle: 'disc', paddingLeft: 24, display: 'flex', flexDirection: 'column', gap: 8 }}>
                <li>
                  <strong>{t('privacy.accountInfo')}:</strong> {t('privacy.accountInfoDesc')}
                </li>
                <li>
                  <strong>{t('privacy.uploadedContent')}:</strong> {t('privacy.uploadedContentDesc')}
                </li>
                <li>
                  <strong>{t('privacy.usageData')}:</strong> {t('privacy.usageDataDesc')}
                </li>
                <li>
                  <strong>{t('privacy.techInfo')}:</strong> {t('privacy.techInfoDesc')}
                </li>
                <li>
                  <strong>{t('privacy.aiResults')}:</strong> {t('privacy.aiResultsDesc')}
                </li>
              </ul>
            </section>

            <section style={{ marginBottom: 28 }}>
              <h2 style={{
                fontSize: 18,
                fontWeight: 600,
                color: 'var(--text-primary)',
                marginBottom: 12,
                paddingBottom: 8,
                borderBottom: '1px solid var(--border-dim)',
              }}>
                {t('privacy.infoUsage')}
              </h2>
              <p style={{ marginBottom: 12 }}>{t('privacy.infoUsageIntro')}</p>
              <ul style={{ listStyle: 'disc', paddingLeft: 24, display: 'flex', flexDirection: 'column', gap: 8 }}>
                <li>{t('privacy.provideImproveService')}</li>
                <li>{t('privacy.personalizeExperience')}</li>
                <li>{t('privacy.processStoreContent')}</li>
                <li>{t('privacy.generateAiResults')}</li>
                <li>{t('privacy.maintainSecurity')}</li>
                <li>{t('privacy.sendNotifications')}</li>
                <li>{t('privacy.complyLaws')}</li>
              </ul>
            </section>

            <section style={{ marginBottom: 28 }}>
              <h2 style={{
                fontSize: 18,
                fontWeight: 600,
                color: 'var(--text-primary)',
                marginBottom: 12,
                paddingBottom: 8,
                borderBottom: '1px solid var(--border-dim)',
              }}>
                {t('privacy.dataStorage')}
              </h2>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                <p>
                  <strong>{t('privacy.dataStorage')}:</strong> {t('privacy.dataStorageDesc')}
                </p>
                <p>
                  <strong>{t('privacy.storagePeriod')}:</strong> {t('privacy.storagePeriodDesc')}
                </p>
                <p>
                  <strong>{t('privacy.securityMeasures')}:</strong> {t('privacy.securityMeasuresDesc')}
                </p>
              </div>
            </section>

            <section style={{ marginBottom: 28 }}>
              <h2 style={{
                fontSize: 18,
                fontWeight: 600,
                color: 'var(--text-primary)',
                marginBottom: 12,
                paddingBottom: 8,
                borderBottom: '1px solid var(--border-dim)',
              }}>
                {t('privacy.infoSharing')}
              </h2>
              <p style={{ marginBottom: 12 }}>{t('privacy.infoSharingIntro')}</p>
              <ul style={{ listStyle: 'disc', paddingLeft: 24, display: 'flex', flexDirection: 'column', gap: 8 }}>
                <li>{t('privacy.explicitConsent')}</li>
                <li>{t('privacy.serviceRequired')}</li>
                <li>{t('privacy.legalRequirements')}</li>
                <li>{t('privacy.protectRights')}</li>
              </ul>
            </section>

            <section style={{ marginBottom: 28 }}>
              <h2 style={{
                fontSize: 18,
                fontWeight: 600,
                color: 'var(--text-primary)',
                marginBottom: 12,
                paddingBottom: 8,
                borderBottom: '1px solid var(--border-dim)',
              }}>
                {t('privacy.yourRights')}
              </h2>
              <p style={{ marginBottom: 12 }}>{t('privacy.yourRightsIntro')}</p>
              <ul style={{ listStyle: 'disc', paddingLeft: 24, display: 'flex', flexDirection: 'column', gap: 8 }}>
                <li>{t('privacy.accessInfo')}</li>
                <li>{t('privacy.correctInfo')}</li>
                <li>{t('privacy.deleteData')}</li>
                <li>{t('privacy.restrictProcessing')}</li>
                <li>{t('privacy.dataPortability')}</li>
              </ul>
            </section>

            <section style={{ marginBottom: 28 }}>
              <h2 style={{
                fontSize: 18,
                fontWeight: 600,
                color: 'var(--text-primary)',
                marginBottom: 12,
                paddingBottom: 8,
                borderBottom: '1px solid var(--border-dim)',
              }}>
                {t('privacy.cookies')}
              </h2>
              <p>{t('privacy.cookiesDesc')}</p>
            </section>

            <section style={{ marginBottom: 28 }}>
              <h2 style={{
                fontSize: 18,
                fontWeight: 600,
                color: 'var(--text-primary)',
                marginBottom: 12,
                paddingBottom: 8,
                borderBottom: '1px solid var(--border-dim)',
              }}>
                {t('privacy.policyUpdates')}
              </h2>
              <p>{t('privacy.policyUpdatesDesc')}</p>
            </section>

            <section style={{ marginBottom: 28 }}>
              <h2 style={{
                fontSize: 18,
                fontWeight: 600,
                color: 'var(--text-primary)',
                marginBottom: 12,
                paddingBottom: 8,
                borderBottom: '1px solid var(--border-dim)',
              }}>
                {t('privacy.contactUs')}
              </h2>
              <p style={{ marginBottom: 12 }}>{t('privacy.contactUsIntro')}</p>
              <div style={{
                padding: 16,
                backgroundColor: 'var(--bg-raised)',
                border: '1px solid var(--border-mid)',
                borderRadius: 8,
              }}>
                <p>
                  <strong>{t('privacy.email')}:</strong> privacy@danloo.com<br />
                  <strong>{t('privacy.address')}:</strong> 北京市海淀区
                </p>
              </div>
            </section>

            <div style={{
              borderTop: '1px solid var(--border-dim)',
              paddingTop: 24,
              marginTop: 28,
            }}>
              <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>
                {t('privacy.footerNote')}
              </p>
            </div>
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