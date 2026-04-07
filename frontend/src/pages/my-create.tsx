import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { useTranslation } from 'next-i18next';
import { GetStaticProps } from 'next';
import { serverSideTranslations } from 'next-i18next/serverSideTranslations';
import Layout from '../components/Layout';
import MaterialUpload from '../components/MaterialUpload';
import { Button } from '../components/Button';
import { Input } from '../components/Input';
import { useApi } from '../hooks/useApi';
import { useOptionalAuth } from '../contexts/AuthContext';
import { materialService, Material } from '../services/materials';
import { pelletService } from '../services/pellets';

export default function Create() {
  const { t } = useTranslation('common');
  const router = useRouter();
  const { isAuthenticated, loading: authLoading } = useOptionalAuth();

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, authLoading, router]);

  const [selectedMaterials, setSelectedMaterials] = useState<Material[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [isCreating, setIsCreating] = useState(false);

  const {
    data: materialsData,
    loading: materialsLoading,
    refetch: refetchMaterials,
  } = useApi(
    () => materialService.getMaterials({ limit: 50 }),
    [isAuthenticated]
  );

  const materials = materialsData?.materials || [];
  const filteredMaterials = materials.filter(material =>
    material.title.toLowerCase().includes(searchTerm.toLowerCase()) &&
    !selectedMaterials.some(selected => selected.id === material.id)
  );

  const handleAddMaterial = (material: Material) => {
    setSelectedMaterials(prev => [...prev, material]);
    setSearchTerm('');
  };

  const handleRemoveMaterial = (materialId: string) => {
    setSelectedMaterials(prev => prev.filter(m => m.id !== materialId));
  };

  const handleMaterialAdded = (material: Material) => {
    setSelectedMaterials(prev => [...prev, material]);
    refetchMaterials();
  };

  const handleCreatePellets = async () => {
    if (selectedMaterials.length === 0) return;

    setIsCreating(true);
    try {
      const materialIds = selectedMaterials.map(m => m.id);
      const response = await pelletService.createPelletsFromMaterials(materialIds);

      if (response.success && response.data) {
        router.push('/my-jobs');
      } else {
        throw new Error(response.error?.message || '启动炼丹失败');
      }
    } catch (error) {
      console.error('炼丹失败:', error);
    } finally {
      setIsCreating(false);
    }
  };

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: 'var(--bg-base)' }}>
        <span style={{ color: 'var(--text-dim)', fontSize: 13 }}>LOADING...</span>
      </div>
    );
  }

  if (!isAuthenticated) return null;

  return (
    <Layout
      title={`${t('nav.create')} - ${t('brand.name')}`}
      description={t('create.subtitle')}
    >
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Main Alchemy Area */}
        <div className="lg:col-span-3 space-y-5">
          {/* Upload */}
          <MaterialUpload
            onMaterialAdded={handleMaterialAdded}
            buttonText={t('create.form.uploadNewMaterial')}
          />

          {/* Furnace */}
          <div style={{
            backgroundColor: 'var(--bg-surface)',
            border: '1px solid var(--border-mid)',
          }}>
            {/* Furnace header */}
            <div style={{ padding: '14px 18px', borderBottom: '1px solid var(--border-mid)', display: 'flex', alignItems: 'center', gap: 10 }}>
              <div style={{
                width: 32, height: 32,
                backgroundColor: 'var(--bg-raised)', border: '1px solid var(--border-mid)',
                display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
              }}>
                <span style={{ color: 'var(--text-dim)', fontSize: 14 }}>▲</span>
              </div>
              <div>
                <h3 style={{ color: 'var(--text-primary)', fontSize: 14, fontWeight: 600 }}>{t('create.alchemyWorkbench')}</h3>
                <p style={{ color: 'var(--text-dim)', fontSize: 12 }}>
                  {selectedMaterials.length > 0
                    ? t('create.materialsInFurnace', { count: selectedMaterials.length })
                    : t('create.selectFromLibrary')}
                </p>
              </div>
            </div>

            {/* Furnace body */}
            <div style={{ padding: '18px', minHeight: 240 }}>
              {selectedMaterials.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {selectedMaterials.map((material, index) => (
                    <div
                      key={material.id}
                      style={{
                        border: '1px solid var(--border-mid)', backgroundColor: 'var(--bg-raised)',
                        padding: '10px 12px', display: 'flex', alignItems: 'center', gap: 10,
                      }}
                    >
                      <div style={{
                        width: 22, height: 22, flexShrink: 0,
                        backgroundColor: 'var(--border-mid)', display: 'flex', alignItems: 'center', justifyContent: 'center',
                      }}>
                        <span style={{ color: 'var(--text-primary)', fontSize: 10, fontWeight: 700 }}>{index + 1}</span>
                      </div>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <p style={{ color: 'var(--text-primary)', fontSize: 12, fontWeight: 500,
                          overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {material.title}
                        </p>
                        <p style={{ color: 'var(--text-dim)', fontSize: 11 }}>{material.content_type}</p>
                      </div>
                      <button
                        onClick={() => handleRemoveMaterial(material.id)}
                        style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', padding: 4, flexShrink: 0 }}
                        onMouseEnter={e => (e.currentTarget.style.color = '#f87171')}
                        onMouseLeave={e => (e.currentTarget.style.color = 'var(--text-muted)')}
                      >
                        ✕
                      </button>
                    </div>
                  ))}
                </div>
              ) : (
                <div style={{ textAlign: 'center', paddingTop: 40, paddingBottom: 40 }}>
                  <p style={{ color: 'var(--border-mid)', fontSize: 32, marginBottom: 12 }}>⬡</p>
                  <p style={{ color: 'var(--text-dim)', fontSize: 14 }}>{t('create.furnaceStandby')}</p>
                  <p style={{ color: 'var(--text-muted)', fontSize: 12, marginTop: 4 }}>{t('create.selectFromRight')}</p>
                </div>
              )}
            </div>

            {/* Alchemy button */}
            <div style={{ padding: '0 18px 18px' }}>
              <Button
                onClick={handleCreatePellets}
                disabled={selectedMaterials.length === 0 || isCreating}
                loading={isCreating}
                variant="primary"
                size="lg"
                fullWidth
              >
                {isCreating ? t('create.alchemyWorking') : t('create.startAlchemyWithCount', { count: selectedMaterials.length })}
              </Button>
            </div>
          </div>
        </div>

        {/* Material Library Sidebar */}
        <div style={{
          backgroundColor: 'var(--bg-surface)',
          border: '1px solid var(--border-mid)',
        }}>
          <div style={{ padding: '12px 14px', borderBottom: '1px solid var(--border-mid)' }}>
            <span style={{ color: 'var(--text-primary)', fontSize: 13, fontWeight: 600 }}>{t('create.materialLibrary')}</span>
          </div>

          {/* Search */}
          <div style={{ padding: '10px 14px', borderBottom: '1px solid var(--border-dim)' }}>
            <Input
              type="text"
              placeholder={t('create.searchMaterials')}
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              leftIcon={
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              }
            />
          </div>

          {/* Materials list */}
          <div style={{ maxHeight: 500, overflowY: 'auto' }}>
            {materialsLoading ? (
              <div style={{ padding: '24px', textAlign: 'center' }}>
                <span style={{ color: 'var(--text-dim)', fontSize: 12 }}>{t('common.loading')}</span>
              </div>
            ) : filteredMaterials.length === 0 ? (
              <div style={{ padding: '24px', textAlign: 'center' }}>
                <p style={{ color: 'var(--text-dim)', fontSize: 12 }}>
                  {searchTerm ? t('create.noMatchingMaterials') : t('create.noAvailableMaterials')}
                </p>
              </div>
            ) : (
              filteredMaterials.map((material) => (
                <div
                  key={material.id}
                  onClick={() => handleAddMaterial(material)}
                  style={{
                    padding: '10px 14px', borderBottom: '1px solid var(--border-dim)',
                    cursor: 'pointer',
                  }}
                  onMouseEnter={e => { e.currentTarget.style.backgroundColor = 'var(--bg-raised)'; }}
                  onMouseLeave={e => { e.currentTarget.style.backgroundColor = 'transparent'; }}
                >
                  <p style={{ color: 'var(--text-primary)', fontSize: 12, fontWeight: 500, marginBottom: 2,
                    overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {material.title}
                  </p>
                  <p style={{ color: 'var(--text-dim)', fontSize: 11 }}>{material.content_type}</p>
                </div>
              ))
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
