import React from 'react';
import { useTranslation } from 'next-i18next';
import { GetStaticProps } from 'next';
import { serverSideTranslations } from 'next-i18next/serverSideTranslations';
import Layout from '../components/Layout';

export default function Terms() {
  const { t } = useTranslation('common');

  return (
    <Layout
      title={`${t('terms.title')} - ${t('brand.name')}`}
      description={t('terms.description')}
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
            {t('terms.title')}
          </h1>

          <p style={{
            fontSize: 13,
            color: 'var(--text-dim)',
            marginBottom: 28,
          }}>
            {t('terms.lastUpdated')}
          </p>

          <div style={{ color: 'var(--text-secondary)', fontSize: 14, lineHeight: 1.8 }}>
            <section style={{ marginBottom: 24 }}>
              <h2 style={{
                fontSize: 18,
                fontWeight: 600,
                color: 'var(--text-primary)',
                marginBottom: 12,
                paddingBottom: 8,
                borderBottom: '1px solid var(--border-dim)',
              }}>
                {t('terms.acceptTerms')}
              </h2>
              <p>{t('terms.acceptTermsDesc')}</p>
            </section>

            <section style={{ marginBottom: 24 }}>
              <h2 style={{
                fontSize: 18,
                fontWeight: 600,
                color: 'var(--text-primary)',
                marginBottom: 12,
                paddingBottom: 8,
                borderBottom: '1px solid var(--border-dim)',
              }}>
                {t('terms.serviceDescription')}
              </h2>
              <p style={{ marginBottom: 12 }}>{t('terms.serviceDescriptionIntro')}</p>
              <ul style={{ listStyle: 'disc', paddingLeft: 24, display: 'flex', flexDirection: 'column', gap: 8 }}>
                <li>{t('terms.aiAnalysis')}</li>
                <li>{t('terms.contentClassification')}</li>
                <li>{t('terms.materialUpload')}</li>
                <li>{t('terms.aiGeneratedContent')}</li>
                <li>{t('terms.personalLibrary')}</li>
              </ul>
            </section>

            <section style={{ marginBottom: 24 }}>
              <h2 style={{
                fontSize: 18,
                fontWeight: 600,
                color: 'var(--text-primary)',
                marginBottom: 12,
                paddingBottom: 8,
                borderBottom: '1px solid var(--border-dim)',
              }}>
                {t('terms.userResponsibility')}
              </h2>
              <h3 style={{
                fontSize: 16,
                fontWeight: 600,
                color: 'var(--text-primary)',
                marginTop: 20,
                marginBottom: 8,
              }}>
                {t('terms.accountSecurity')}
              </h3>
              <ul style={{ listStyle: 'disc', paddingLeft: 24, display: 'flex', flexDirection: 'column', gap: 6, marginBottom: 16 }}>
                <li>{t('terms.protectAccount')}</li>
                <li>{t('terms.responsibleForActivity')}</li>
                <li>{t('terms.notifyUnauthorized')}</li>
              </ul>
              <h3 style={{
                fontSize: 16,
                fontWeight: 600,
                color: 'var(--text-primary)',
                marginTop: 20,
                marginBottom: 8,
              }}>
                {t('terms.contentResponsibility')}
              </h3>
              <ul style={{ listStyle: 'disc', paddingLeft: 24, display: 'flex', flexDirection: 'column', gap: 6 }}>
                <li>{t('terms.ownLegalRights')}</li>
                <li>{t('terms.noInfringement')}</li>
                <li>{t('terms.noIllegalContent')}</li>
                <li>{t('terms.takeLegalResponsibility')}</li>
              </ul>
            </section>

            <section style={{ marginBottom: 24 }}>
              <h2 style={{
                fontSize: 18,
                fontWeight: 600,
                color: 'var(--text-primary)',
                marginBottom: 12,
                paddingBottom: 8,
                borderBottom: '1px solid var(--border-dim)',
              }}>
                {t('terms.prohibitedActions')}
              </h2>
              <p style={{ marginBottom: 12 }}>{t('terms.prohibitedActionsIntro')}</p>
              <ul style={{ listStyle: 'disc', paddingLeft: 24, display: 'flex', flexDirection: 'column', gap: 6 }}>
                <li>{t('terms.noIllegalContent2')}</li>
                <li>{t('terms.noInfringement2')}</li>
                <li>{t('terms.noMalware')}</li>
                <li>{t('terms.noUnauthorizedAccess')}</li>
                <li>{t('terms.noDisruption')}</li>
                <li>{t('terms.noSpam')}</li>
                <li>{t('terms.noOtherIllegal')}</li>
              </ul>
            </section>

            <section style={{ marginBottom: 24 }}>
              <h2 style={{
                fontSize: 18,
                fontWeight: 600,
                color: 'var(--text-primary)',
                marginBottom: 12,
                paddingBottom: 8,
                borderBottom: '1px solid var(--border-dim)',
              }}>
                {t('terms.dataUsage')}
              </h2>
              <h3 style={{
                fontSize: 16,
                fontWeight: 600,
                color: 'var(--text-primary)',
                marginTop: 20,
                marginBottom: 8,
              }}>
                {t('terms.dataCollection')}
              </h3>
              <p style={{ marginBottom: 12 }}>{t('terms.dataCollectionIntro')}</p>
              <ul style={{ listStyle: 'disc', paddingLeft: 24, display: 'flex', flexDirection: 'column', gap: 6, marginBottom: 16 }}>
                <li>{t('terms.uploadedMaterials')}</li>
                <li>{t('terms.aiClassification')}</li>
                <li>{t('terms.usagePreferences')}</li>
                <li>{t('terms.accountContact')}</li>
              </ul>
              <h3 style={{
                fontSize: 16,
                fontWeight: 600,
                color: 'var(--text-primary)',
                marginTop: 20,
                marginBottom: 8,
              }}>
                {t('terms.dataUsage2')}
              </h3>
              <p style={{ marginBottom: 12 }}>{t('terms.dataUsageIntro2')}</p>
              <ul style={{ listStyle: 'disc', paddingLeft: 24, display: 'flex', flexDirection: 'column', gap: 6 }}>
                <li>{t('terms.provideAnalysisService')}</li>
                <li>{t('terms.improveAlgorithms')}</li>
                <li>{t('terms.personalizeUserExperience')}</li>
                <li>{t('terms.complyLaws')}</li>
              </ul>
            </section>

            <section style={{ marginBottom: 24 }}>
              <h2 style={{
                fontSize: 18,
                fontWeight: 600,
                color: 'var(--text-primary)',
                marginBottom: 12,
                paddingBottom: 8,
                borderBottom: '1px solid var(--border-dim)',
              }}>
                {t('terms.intellectualProperty')}
              </h2>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                <p>
                  <strong>{t('terms.yourContent')}:</strong> {t('terms.yourContentDesc')}
                </p>
                <p>
                  <strong>{t('terms.ourService')}:</strong> {t('terms.ourServiceDesc')}
                </p>
                <p>
                  <strong>{t('terms.aiGeneratedContent')}:</strong> {t('terms.aiGeneratedContentDesc')}
                </p>
              </div>
            </section>

            <section style={{ marginBottom: 24 }}>
              <h2 style={{
                fontSize: 18,
                fontWeight: 600,
                color: 'var(--text-primary)',
                marginBottom: 12,
                paddingBottom: 8,
                borderBottom: '1px solid var(--border-dim)',
              }}>
                {t('terms.serviceAvailability')}
              </h2>
              <p>{t('terms.serviceAvailabilityDesc')}</p>
            </section>

            <section style={{ marginBottom: 24 }}>
              <h2 style={{
                fontSize: 18,
                fontWeight: 600,
                color: 'var(--text-primary)',
                marginBottom: 12,
                paddingBottom: 8,
                borderBottom: '1px solid var(--border-dim)',
              }}>
                {t('terms.accountTermination')}
              </h2>
              <p style={{ marginBottom: 12 }}>{t('terms.accountTerminationIntro')}</p>
              <ul style={{ listStyle: 'disc', paddingLeft: 24, display: 'flex', flexDirection: 'column', gap: 6 }}>
                <li>{t('terms.violateTerms')}</li>
                <li>{t('terms.illegalActivity')}</li>
                <li>{t('terms.inactiveAccount')}</li>
                <li>{t('terms.requestDeletion')}</li>
              </ul>
            </section>

            <section style={{ marginBottom: 24 }}>
              <h2 style={{
                fontSize: 18,
                fontWeight: 600,
                color: 'var(--text-primary)',
                marginBottom: 12,
                paddingBottom: 8,
                borderBottom: '1px solid var(--border-dim)',
              }}>
                {t('terms.disclaimer')}
              </h2>
              <p>{t('terms.disclaimerDesc')}</p>
            </section>

            <section style={{ marginBottom: 24 }}>
              <h2 style={{
                fontSize: 18,
                fontWeight: 600,
                color: 'var(--text-primary)',
                marginBottom: 12,
                paddingBottom: 8,
                borderBottom: '1px solid var(--border-dim)',
              }}>
                {t('terms.liabilityLimitation')}
              </h2>
              <p>{t('terms.liabilityLimitationDesc')}</p>
            </section>

            <section style={{ marginBottom: 24 }}>
              <h2 style={{
                fontSize: 18,
                fontWeight: 600,
                color: 'var(--text-primary)',
                marginBottom: 12,
                paddingBottom: 8,
                borderBottom: '1px solid var(--border-dim)',
              }}>
                {t('terms.termsModification')}
              </h2>
              <p>{t('terms.termsModificationDesc')}</p>
            </section>

            <section style={{ marginBottom: 24 }}>
              <h2 style={{
                fontSize: 18,
                fontWeight: 600,
                color: 'var(--text-primary)',
                marginBottom: 12,
                paddingBottom: 8,
                borderBottom: '1px solid var(--border-dim)',
              }}>
                {t('terms.disputeResolution')}
              </h2>
              <p>{t('terms.disputeResolutionDesc')}</p>
            </section>

            <section style={{ marginBottom: 24 }}>
              <h2 style={{
                fontSize: 18,
                fontWeight: 600,
                color: 'var(--text-primary)',
                marginBottom: 12,
                paddingBottom: 8,
                borderBottom: '1px solid var(--border-dim)',
              }}>
                {t('terms.contactUs')}
              </h2>
              <p style={{ marginBottom: 12 }}>{t('terms.contactUsIntro')}</p>
              <div style={{
                padding: 16,
                backgroundColor: 'var(--bg-raised)',
                border: '1px solid var(--border-mid)',
                borderRadius: 8,
              }}>
                <p>
                  <strong>{t('terms.supportEmail')}:</strong> support@danloo.com<br />
                  <strong>{t('terms.supportAddress')}:</strong> 北京市海淀区<br />
                  <strong>{t('terms.hotline')}:</strong> 400-XXX-XXXX
                </p>
              </div>
            </section>

            <div style={{
              borderTop: '1px solid var(--border-dim)',
              paddingTop: 24,
              marginTop: 28,
            }}>
              <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>
                {t('terms.footerNote')}
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