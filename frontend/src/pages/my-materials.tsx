import React, { useState, useEffect } from "react";
import { useRouter } from "next/router";
import { useTranslation } from "next-i18next";
import { GetStaticProps } from "next";
import { serverSideTranslations } from "next-i18next/serverSideTranslations";
import Layout from "../components/Layout";
import MaterialUpload from "../components/MaterialUpload";
import { Input } from "../components/Input";
import { Button } from "../components/Button";
import { useApi } from "../hooks/useApi";
import { useOptionalAuth } from "../contexts/AuthContext";
import { materialService, Material } from "../services/materials";

export default function Materials() {
  const { t } = useTranslation("common");
  const router = useRouter();
  const { isAuthenticated, loading: authLoading } = useOptionalAuth();

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, authLoading, router]);

  const [searchTerm, setSearchTerm] = useState("");

  const {
    data: materialsData,
    loading: materialsLoading,
    error: materialsError,
    refetch: refetchMaterials,
  } = useApi(
    () => materialService.getMaterials({ limit: 50 }),
    [isAuthenticated],
  );

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: 'var(--bg-base)' }}>
        <span style={{ color: 'var(--text-dim)', fontSize: 13 }}>LOADING...</span>
      </div>
    );
  }

  if (!isAuthenticated) return null;

  const materials = materialsData?.materials || [];
  const filtered = materials.filter(m =>
    m.title.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleMaterialAdded = (material: Material) => {
    refetchMaterials();
  };

  return (
    <Layout
      title={`${t("materials.title")} - ${t("brand.name")}`}
      description={t("materials.subtitle")}
    >
      {/* Search */}
      <div style={{ marginBottom: 20 }}>
        <Input
          type="text"
          placeholder="搜索材料..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          leftIcon={
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          }
        />
      </div>

      {/* Upload */}
      <div style={{ marginBottom: 20 }}>
        <MaterialUpload
          onMaterialAdded={handleMaterialAdded}
          buttonText={t("materials.addNew")}
        />
      </div>

      {/* Materials List */}
      <div>
        {materialsLoading ? (
          <div style={{ padding: '32px 0', textAlign: 'center' }}>
            <span style={{ color: 'var(--text-dim)', fontSize: 13 }}>LOADING...</span>
          </div>
        ) : materialsError ? (
          <div style={{ padding: '24px', border: '1px solid #f87171', backgroundColor: '#1a0a0a', textAlign: 'center' }}>
            <p style={{ color: '#f87171', fontSize: 13, marginBottom: 12 }}>✕ {materialsError}</p>
            <Button variant="secondary" size="sm" onClick={() => window.location.reload()}>重试</Button>
          </div>
        ) : filtered.length === 0 ? (
          <div style={{ padding: '48px 0', textAlign: 'center' }}>
            <p style={{ color: 'var(--text-muted)', fontSize: 24, marginBottom: 12 }}>▣</p>
            <p style={{ color: 'var(--text-dim)', fontSize: 14, marginBottom: 6 }}>{t("materials.empty.noMaterials")}</p>
            <p style={{ color: 'var(--text-muted)', fontSize: 12 }}>{t("materials.empty.noMaterialsSubtitle")}</p>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {filtered.map((material: Material) => (
              <div
                key={material.id}
                style={{
                  backgroundColor: 'var(--bg-surface)',
                  border: '1px solid var(--border-dim)',
                  padding: '12px 16px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: 12,
                }}
                onMouseEnter={e => (e.currentTarget.style.borderColor = 'var(--border-mid)')}
                onMouseLeave={e => (e.currentTarget.style.borderColor = 'var(--border-dim)')}
              >
                <div style={{ flex: 1, minWidth: 0 }}>
                  <p style={{ color: 'var(--text-primary)', fontSize: 13, fontWeight: 500, marginBottom: 4,
                    overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {material.title}
                  </p>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <span style={{ fontSize: 11, color: 'var(--text-dim)', backgroundColor: 'var(--bg-raised)', border: '1px solid var(--border-mid)', padding: '1px 6px' }}>
                      {material.content_type}
                    </span>
                    <span style={{ fontSize: 11, color: 'var(--text-dim)' }}>
                      {new Date(material.created_at).toLocaleDateString("zh-CN")}
                    </span>
                  </div>
                </div>
                <div style={{ display: 'flex', gap: 8, flexShrink: 0 }}>
                  <Button variant="ghost" size="sm">{t("materials.actions.view")}</Button>
                  <Button variant="destructive" size="sm">{t("materials.actions.delete")}</Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </Layout>
  );
}

export const getStaticProps: GetStaticProps = async ({ locale = 'en' }) => {
  return {
    props: {
      ...(await serverSideTranslations(locale, ["common"])),
    },
  };
};
