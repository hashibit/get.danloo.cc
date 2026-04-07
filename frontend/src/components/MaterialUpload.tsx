import React, { useState, useRef, useEffect } from 'react';
import { useTranslation } from 'next-i18next';
import { useRouter } from 'next/router';
import { useApiMutation } from '../hooks/useApi';
import { ApiResponse } from '../services/api';
import { fileService, FileObject } from '../services/files';
import { materialService, Material } from '../services/materials';
import { getAuthToken } from '../services/api';

interface FileType {
  id: string;
  name: string;
  description: string;
  icon: string;
  accept: string;
  maxSize: number;
}

interface MaterialUploadProps {
  onMaterialAdded?: (material: Material) => void;
  title?: string;
  buttonText?: string;
  expandable?: boolean;
}

export default function MaterialUpload({
  onMaterialAdded,
  title = "添加新材料",
  buttonText = "添加新材料",
  expandable = true
}: MaterialUploadProps) {
  const { t } = useTranslation('common');
  const router = useRouter();

  const [selectedInputType, setSelectedInputType] = useState<FileType | null>(null);
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    if (router.query.upload === 'true') {
      setExpanded(true);
      router.replace('/my-materials', undefined, { shallow: true });
    }
  }, [router.query.upload, router]);

  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState('');
  const [materialUploading, setMaterialUploading] = useState(false);
  const [materialError, setMaterialError] = useState<string | null>(null);
  const [isResetting, setIsResetting] = useState(false);
  const [isUploadSuccess, setIsUploadSuccess] = useState(false);
  const [urlInput, setUrlInput] = useState('');
  const [textContent, setTextContent] = useState('');
  const [materialTitle, setMaterialTitle] = useState('');

  const fileInputRef = useRef<HTMLInputElement>(null);
  const { mutate: uploadMaterial } = useApiMutation();

  const inputTypes: FileType[] = [
    {
      id: 'file-text',
      name: t('upload.inputTypes.file.name'),
      description: t('upload.inputTypes.file.description'),
      icon: '▣',
      accept: '.txt,.md,.rtf,.pdf,.jpg,.jpeg,.png,.gif,.webp',
      maxSize: 50,
    },
    {
      id: 'url',
      name: t('upload.inputTypes.url.name'),
      description: t('upload.inputTypes.url.description'),
      icon: '⬡',
      accept: '',
      maxSize: 0,
    },
    {
      id: 'text-paste',
      name: t('upload.inputTypes.textPaste.name'),
      description: t('upload.inputTypes.textPaste.description'),
      icon: '▶',
      accept: '',
      maxSize: 0,
    },
  ];

  const generateTitleAndType = (file: File, fileType: FileType) => {
    const fileName = file.name.replace(/\.[^/.]+$/, '');
    const contentTypeMap: { [key: string]: string } = {
      'file-text': 'text/plain',
      pdf: 'application/pdf',
      image: 'image/jpeg',
    };
    return { title: fileName, contentType: contentTypeMap[fileType.id] || 'text/plain' };
  };

  const handleInputTypeSelect = (inputType: FileType) => {
    setSelectedInputType(inputType);
    if (inputType.id === 'file-text' && fileInputRef.current) {
      fileInputRef.current.accept = inputType.accept;
      fileInputRef.current.click();
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      const fileType = selectedInputType;
      if (!fileType) return;
      const fileSizeMB = selectedFile.size / 1024 / 1024;
      if (fileSizeMB > fileType.maxSize) {
        setMaterialError(`文件大小超过限制（${fileType.maxSize}MB）`);
        return;
      }
      setFile(selectedFile);
      setMaterialError(null);
      setPreview(`${selectedFile.name} (${fileSizeMB.toFixed(2)} MB)`);
    }
  };

  const handleManualUpload = async () => {
    if (!file || !selectedInputType) return;
    await handlePreUpload(file, selectedInputType);
  };

  const handlePreUpload = async (selectedFile: File, fileType: FileType) => {
    setMaterialUploading(true);
    setMaterialError(null);
    try {
      const { contentType } = generateTitleAndType(selectedFile, fileType);
      const uploadedFileObject = await fileService.uploadFile(selectedFile, { contentType });
      const fileSize = (selectedFile.size / 1024 / 1024).toFixed(2);
      setPreview(`✓ ${selectedFile.name} (${fileSize} MB) — 上传成功`);
      await handleAutoSubmit(selectedFile.name.replace(/\.[^/.]+$/, ''), contentType, uploadedFileObject.id);
    } catch (error) {
      setMaterialError(error instanceof Error ? error.message : '上传失败');
      setPreview(`✕ 上传失败`);
    } finally {
      setMaterialUploading(false);
    }
  };

  const handleAutoSubmit = async (title: string, contentType: string, fileObjectId: string) => {
    const result = await uploadMaterial(async (): Promise<ApiResponse<any>> => {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/materials/from-object`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${getAuthToken()}` },
        body: JSON.stringify({ title, content_type: contentType, file_object_id: fileObjectId }),
      });
      if (!response.ok) throw new Error('Failed to create material');
      return { success: true, data: await response.json() };
    }, undefined);

    if (result.success && result.data) {
      const data = result.data as any;
      const newMaterial: Material = {
        id: data.id, title: data.title, content_type: data.content_type,
        file_path: data.file_path, file_size: data.file_size,
        user_id: data.user_id, created_at: data.created_at, updated_at: data.updated_at,
      };
      setIsUploadSuccess(true);
      onMaterialAdded?.(newMaterial);
      handleSuccessAndClose();
    }
  };

  const handleUrlSubmit = async () => {
    if (!urlInput.trim() || !materialTitle.trim()) { setMaterialError('请输入网页链接和标题'); return; }
    setMaterialUploading(true);
    setMaterialError(null);
    try {
      const result = await uploadMaterial(async (): Promise<ApiResponse<any>> => {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/materials/from-url`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${getAuthToken()}` },
          body: JSON.stringify({ url: urlInput.trim(), title: materialTitle.trim(), content_type: 'text/plain' }),
        });
        if (!response.ok) throw new Error('Failed to create material from URL');
        return { success: true, data: await response.json() };
      }, undefined);
      if (result.success && result.data) {
        const data = result.data as any;
        const newMaterial: Material = {
          id: data.id, title: data.title, content_type: data.content_type,
          file_path: data.file_path, file_size: data.file_size,
          user_id: data.user_id, created_at: data.created_at, updated_at: data.updated_at,
        };
        setIsUploadSuccess(true);
        onMaterialAdded?.(newMaterial);
        handleSuccessAndReset();
      }
    } catch (error) {
      setMaterialError(error instanceof Error ? error.message : '上传失败');
    } finally {
      setMaterialUploading(false);
    }
  };

  const handleTextSubmit = async () => {
    if (!textContent.trim() || !materialTitle.trim()) { setMaterialError('请输入文本内容和标题'); return; }
    setMaterialUploading(true);
    setMaterialError(null);
    try {
      const result = await uploadMaterial(async (): Promise<ApiResponse<any>> => {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/materials/from-text`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${getAuthToken()}` },
          body: JSON.stringify({ text_content: textContent.trim(), title: materialTitle.trim(), content_type: 'text/plain' }),
        });
        if (!response.ok) throw new Error('Failed to create material from text');
        return { success: true, data: await response.json() };
      }, undefined);
      if (result.success && result.data) {
        const data = result.data as any;
        const newMaterial: Material = {
          id: data.id, title: data.title, content_type: data.content_type,
          file_path: data.file_path, file_size: data.file_size,
          user_id: data.user_id, created_at: data.created_at, updated_at: data.updated_at,
        };
        setIsUploadSuccess(true);
        onMaterialAdded?.(newMaterial);
        handleSuccessAndReset();
      }
    } catch (error) {
      setMaterialError(error instanceof Error ? error.message : '上传失败');
    } finally {
      setMaterialUploading(false);
    }
  };

  const handleSuccessAndReset = () => {
    setTimeout(() => { setIsResetting(true); setTimeout(() => { handleReset(); setIsResetting(false); }, 300); }, 2000);
  };

  const handleReset = () => {
    setFile(null); setPreview(''); setSelectedInputType(null); setMaterialError(null);
    setIsUploadSuccess(false); setUrlInput(''); setTextContent(''); setMaterialTitle('');
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleSuccessAndClose = () => {
    setTimeout(() => {
      setIsResetting(true);
      setTimeout(() => { handleReset(); setIsResetting(false); if (expandable) setExpanded(false); }, 300);
    }, 2000);
  };

  const inputStyle: React.CSSProperties = {
    width: '100%', padding: '8px 10px', backgroundColor: 'var(--bg-input)',
    border: '1px solid var(--border-mid)', color: 'var(--text-primary)', fontSize: 13,
    outline: 'none', boxSizing: 'border-box',
  };

  // Collapsed trigger
  if (expandable && !expanded) {
    return (
      <button
        onClick={() => setExpanded(true)}
        style={{
          width: '100%', padding: '12px',
          border: '1px dashed var(--border-mid)', backgroundColor: 'transparent',
          color: 'var(--text-dim)', fontSize: 13, fontWeight: 400,
          cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
        }}
        onMouseEnter={e => { e.currentTarget.style.backgroundColor = 'var(--bg-raised)'; e.currentTarget.style.borderColor = 'var(--text-muted)'; e.currentTarget.style.color = 'var(--text-primary)'; }}
        onMouseLeave={e => { e.currentTarget.style.backgroundColor = 'transparent'; e.currentTarget.style.borderColor = 'var(--border-mid)'; e.currentTarget.style.color = 'var(--text-dim)'; }}
      >
        <span>+</span> {buttonText}
      </button>
    );
  }

  return (
    <div
      style={{
        backgroundColor: 'var(--bg-surface)', border: '1px solid var(--border-mid)',
        padding: '18px',
        opacity: isResetting ? 0.4 : 1, transition: 'opacity 0.3s',
      }}
    >
      {expandable && (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
          <span style={{ color: 'var(--text-primary)', fontSize: 13, fontWeight: 600 }}>{title}</span>
          <button
            onClick={() => setExpanded(false)}
            style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: 16 }}
            onMouseEnter={e => (e.currentTarget.style.color = '#f87171')}
            onMouseLeave={e => (e.currentTarget.style.color = 'var(--text-muted)')}
          >✕</button>
        </div>
      )}

      {/* Input type selection */}
      <div className="grid grid-cols-3 gap-3" style={{ marginBottom: 16 }}>
        {inputTypes.map((inputType) => (
          <div
            key={inputType.id}
            onClick={() => handleInputTypeSelect(inputType)}
            style={{
              border: selectedInputType?.id === inputType.id ? '1px solid var(--text-primary)' : '1px dashed var(--border-mid)',
              backgroundColor: selectedInputType?.id === inputType.id ? 'var(--bg-raised)' : 'transparent',
              padding: '12px 8px', textAlign: 'center', cursor: 'pointer',
            }}
            onMouseEnter={e => { if (selectedInputType?.id !== inputType.id) e.currentTarget.style.borderColor = 'var(--text-muted)'; }}
            onMouseLeave={e => { if (selectedInputType?.id !== inputType.id) e.currentTarget.style.borderColor = 'var(--border-mid)'; }}
          >
            <p style={{ color: 'var(--text-dim)', fontSize: 16, marginBottom: 4 }}>{inputType.icon}</p>
            <p style={{ color: 'var(--text-primary)', fontSize: 12, fontWeight: 600, marginBottom: 2 }}>{inputType.name}</p>
            <p style={{ color: 'var(--text-dim)', fontSize: 11 }}>{inputType.description}</p>
            {inputType.maxSize > 0 && (
              <p style={{ color: 'var(--text-muted)', fontSize: 10, marginTop: 2 }}>最大 {inputType.maxSize}MB</p>
            )}
          </div>
        ))}
      </div>

      {/* Hidden file input */}
      <input type="file" ref={fileInputRef} style={{ display: 'none' }} onChange={handleFileChange} disabled={materialUploading} />

      {/* URL Form */}
      {selectedInputType?.id === 'url' && (
        <div style={{ marginBottom: 16, padding: '14px', border: '1px solid var(--border-dim)', backgroundColor: 'var(--bg-input)' }}>
          <p style={{ color: 'var(--text-primary)', fontSize: 13, fontWeight: 600, marginBottom: 12 }}>{t('upload.urlForm.title')}</p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            <div>
              <label style={{ display: 'block', color: 'var(--text-secondary)', fontSize: 12, marginBottom: 4 }}>{t('upload.form.materialTitle')}</label>
              <input type="text" value={materialTitle} onChange={(e) => setMaterialTitle(e.target.value)}
                placeholder={t('upload.urlForm.titlePlaceholder')} style={inputStyle} />
            </div>
            <div>
              <label style={{ display: 'block', color: 'var(--text-secondary)', fontSize: 12, marginBottom: 4 }}>{t('upload.urlForm.urlLabel')}</label>
              <input type="url" value={urlInput} onChange={(e) => setUrlInput(e.target.value)}
                placeholder={t('upload.urlForm.urlPlaceholder')} style={inputStyle} />
            </div>
            {!isUploadSuccess && (
              <button
                onClick={handleUrlSubmit}
                disabled={materialUploading || !urlInput.trim() || !materialTitle.trim()}
                style={{
                  padding: '9px', backgroundColor: 'var(--btn-primary-bg)', color: 'var(--btn-primary-fg)',
                  border: '1px solid var(--btn-primary-bg)', fontWeight: 600, fontSize: 13, cursor: 'pointer',
                  opacity: (materialUploading || !urlInput.trim() || !materialTitle.trim()) ? 0.4 : 1,
                }}
              >
                {materialUploading ? t('upload.form.uploading') : t('upload.urlForm.submitButton')}
              </button>
            )}
          </div>
        </div>
      )}

      {/* Text Form */}
      {selectedInputType?.id === 'text-paste' && (
        <div style={{ marginBottom: 16, padding: '14px', border: '1px solid var(--border-dim)', backgroundColor: 'var(--bg-input)' }}>
          <p style={{ color: 'var(--text-primary)', fontSize: 13, fontWeight: 600, marginBottom: 12 }}>{t('upload.textForm.title')}</p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            <div>
              <label style={{ display: 'block', color: 'var(--text-secondary)', fontSize: 12, marginBottom: 4 }}>{t('upload.form.materialTitle')}</label>
              <input type="text" value={materialTitle} onChange={(e) => setMaterialTitle(e.target.value)}
                placeholder={t('upload.textForm.titlePlaceholder')} style={inputStyle} />
            </div>
            <div>
              <label style={{ display: 'block', color: 'var(--text-secondary)', fontSize: 12, marginBottom: 4 }}>{t('upload.textForm.contentLabel')}</label>
              <textarea value={textContent} onChange={(e) => setTextContent(e.target.value)}
                placeholder={t('upload.textForm.contentPlaceholder')} rows={6}
                style={{ ...inputStyle, resize: 'vertical' }} />
            </div>
            {!isUploadSuccess && (
              <button
                onClick={handleTextSubmit}
                disabled={materialUploading || !textContent.trim() || !materialTitle.trim()}
                style={{
                  padding: '9px', backgroundColor: 'var(--btn-primary-bg)', color: 'var(--btn-primary-fg)',
                  border: '1px solid var(--btn-primary-bg)', fontWeight: 600, fontSize: 13, cursor: 'pointer',
                  opacity: (materialUploading || !textContent.trim() || !materialTitle.trim()) ? 0.4 : 1,
                }}
              >
                {materialUploading ? t('upload.form.uploading') : t('upload.textForm.submitButton')}
              </button>
            )}
          </div>
        </div>
      )}

      {/* Upload loading */}
      {materialUploading && (
        <div style={{ marginBottom: 12, padding: '10px 14px', border: '1px solid var(--border-dim)', backgroundColor: 'var(--bg-surface)', color: 'var(--text-secondary)', fontSize: 13 }}>
          {t('upload.form.uploading')}...
        </div>
      )}

      {/* File preview */}
      {preview && (
        <div style={{ marginBottom: 12, padding: '10px 14px', border: '1px solid var(--border-mid)', backgroundColor: 'var(--bg-raised)' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: file && !materialUploading ? 10 : 0 }}>
            <span style={{ color: 'var(--text-primary)', fontSize: 12 }}>{preview}</span>
            <button onClick={handleReset} style={{ background: 'none', border: 'none', color: '#f87171', fontSize: 11, cursor: 'pointer' }}>
              取消
            </button>
          </div>
          {!materialUploading && file && (
            <button
              onClick={handleManualUpload}
              style={{
                padding: '6px 14px', backgroundColor: 'var(--btn-primary-bg)', color: 'var(--btn-primary-fg)',
                border: '1px solid var(--btn-primary-bg)', fontWeight: 600, fontSize: 12, cursor: 'pointer',
              }}
            >
              {t('upload.form.uploadNow')}
            </button>
          )}
        </div>
      )}

      {/* Error */}
      {materialError && (
        <div style={{ marginBottom: 12, padding: '10px 14px', border: '1px solid #4a1a1a', backgroundColor: '#1a0a0a', color: '#f87171', fontSize: 12 }}>
          ✕ {materialError}
        </div>
      )}

      {/* Success */}
      {isUploadSuccess && (
        <div style={{ marginBottom: 12, padding: '10px 14px', border: '1px solid #1a3020', backgroundColor: '#0a1a0e', color: '#4ade80', fontSize: 12, opacity: isResetting ? 0.5 : 1 }}>
          ✓ 上传成功
        </div>
      )}
    </div>
  );
}
