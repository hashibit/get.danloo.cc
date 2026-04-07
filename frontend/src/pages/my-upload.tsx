import React, { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/router";
import { useTranslation } from 'next-i18next';
import { GetStaticProps } from 'next';
import { serverSideTranslations } from 'next-i18next/serverSideTranslations';
import Layout from "../components/Layout";
import TagSelector from "../components/TagSelector";
import { TagType } from "../types/tag";
import { useApiMutation } from "../hooks/useApi";
import { materialService } from "../services/materials";
import { fileService, FileObject } from "../services/files";
import { authService } from "../services/auth";
import { getAuthToken, removeAuthToken } from "../services/api";
import { Card } from "../components/Card";
import { Button } from "../components/Button";
import { Input } from "../components/Input";
import { Textarea } from "../components/Input";

interface FileType {
  id: string;
  name: string;
  description: string;
  icon: string;
  accept: string;
  maxSize: number; // in MB
}

export default function Upload() {
  const { t } = useTranslation('common');
  const router = useRouter();
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [authLoading, setAuthLoading] = useState(true);
  const [selectedFileType, setSelectedFileType] = useState<FileType | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState("");
  const [uploadedFile, setUploadedFile] = useState<FileObject | null>(null);
  const [isResetting, setIsResetting] = useState(false);

  // New state for URL and text input
  const [urlInput, setUrlInput] = useState("");
  const [textContent, setTextContent] = useState("");
  const [materialTitle, setMaterialTitle] = useState("");

  // Tags related state
  const [selectedTagIds, setSelectedTagIds] = useState<string[]>([]);

  // Input type definitions
  const inputTypes: FileType[] = [
    {
      id: 'file-text',
      name: t('upload.inputTypes.file.name'),
      description: t('upload.inputTypes.file.description'),
      icon: '📁',
      accept: '.txt,.md,.rtf,.pdf,.jpg,.jpeg,.png,.gif,.webp',
      maxSize: 50
    },
    {
      id: 'url',
      name: t('upload.inputTypes.url.name'),
      description: t('upload.inputTypes.url.description'),
      icon: '🌐',
      accept: '',
      maxSize: 0
    },
    {
      id: 'text-paste',
      name: t('upload.inputTypes.textPaste.name'),
      description: t('upload.inputTypes.textPaste.description'),
      icon: '✏️',
      accept: '',
      maxSize: 0
    }
  ];

  const fileInputRef = useRef<HTMLInputElement>(null);

  // Use API mutation hook for upload
  const { mutate: uploadMaterial, loading, error, data } = useApiMutation<any, any>();
  const [fileUploading, setFileUploading] = useState(false);
  const [fileError, setFileError] = useState<string | null>(null);

  // Check authentication status on component mount
  useEffect(() => {
    const checkAuthStatus = async () => {
      const token = getAuthToken();
      if (!token) {
        router.push('/login?redirect=/my-upload');
        return;
      }

      try {
        const response = await authService.getProfile();
        if (response.success && response.data) {
          setIsLoggedIn(true);
        } else {
          removeAuthToken();
          router.push('/login?redirect=/my-upload');
          return;
        }
      } catch (error) {
        removeAuthToken();
        router.push('/login?redirect=/my-upload');
        return;
      } finally {
        setAuthLoading(false);
      }
    };

    checkAuthStatus();
  }, [router]);

  // Default tag types
  const defaultTags: TagType[] = [
    {
      id: 'gold',
      name: '金丹',
      color: 'yellow',
      description: "High quality pellets with golden content",
    },
    {
      id: 'with-image',
      name: '彩丹-图片',
      color: 'blue',
      description: "Pellets with rich image content",
    },
    {
      id: 'with-video',
      name: '彩丹-视频',
      color: 'purple',
      description: "Pellets with video content",
    },
  ];

  // Auto generate title and type
  const generateTitleAndType = (file: File, fileType: FileType) => {
    const fileName = file.name.replace(/\.[^/.]+$/, "");
    const contentTypeMap: { [key: string]: string } = {
      'text': 'text/plain',
      'pdf': 'application/pdf',
      'image': 'image/jpeg'
    };
    return {
      title: fileName,
      contentType: contentTypeMap[fileType.id] || 'text/plain'
    };
  };

  const handleInputTypeSelect = (inputType: FileType) => {
    setSelectedFileType(inputType);

    if (inputType.id === 'file-text') {
      if (fileInputRef.current) {
        fileInputRef.current.accept = inputType.accept;
        fileInputRef.current.click();
      }
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      const fileType = selectedFileType;

      if (!fileType) return;

      // Check file size
      const fileSizeMB = selectedFile.size / 1024 / 1024;
      if (fileSizeMB > fileType.maxSize) {
        setFileError(`文件大小超过限制（${fileType.maxSize}MB）`);
        return;
      }

      setFile(selectedFile);
      setFileError(null);
      setUploadedFile(null);

      const fileSize = fileSizeMB.toFixed(2);
      setPreview(`${fileType.icon} ${selectedFile.name} (${fileSize} MB)`);
    }
  };

  const handleManualUpload = async () => {
    if (!file || !selectedFileType) return;
    await handlePreUpload(file, selectedFileType);
  };

  const handlePreUpload = async (selectedFile?: File, fileType?: FileType) => {
    const fileToUpload = selectedFile || file;
    const typeToUse = fileType || selectedFileType;

    if (!fileToUpload || !typeToUse) return;

    setFileUploading(true);
    setFileError(null);

    try {
      const { contentType } = generateTitleAndType(fileToUpload, typeToUse);
      const uploadedFileObject = await fileService.uploadFile(fileToUpload, {
        contentType,
      });
      setUploadedFile(uploadedFileObject);

      const fileSize = (fileToUpload.size / 1024 / 1024).toFixed(2);
      setPreview(`✅ ${fileToUpload.name} (${fileSize} MB) - ${t('upload.messages.uploadSuccessful')}`);

      await handleAutoSubmit(fileToUpload, typeToUse, uploadedFileObject.id);
    } catch (error) {
      setFileError(
        error instanceof Error ? error.message : t('upload.messages.uploadFailed'),
      );
      const fileSize = (fileToUpload.size / 1024 / 1024).toFixed(2);
      setPreview(`❌ ${fileToUpload.name} (${fileSize} MB) - ${t('upload.messages.uploadFailed')}`);
    } finally {
      setFileUploading(false);
    }
  };

  const handleAutoSubmit = async (file: File, fileType: FileType, fileObjectId: string) => {
    const { title, contentType } = generateTitleAndType(file, fileType);

    const result = await uploadMaterial(async () => {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/materials/from-object`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${getAuthToken()}`
        },
        body: JSON.stringify({
          title,
          content_type: contentType,
          file_object_id: fileObjectId
        })
      });

      if (!response.ok) {
        throw new Error('Failed to create material');
      }

      const data = await response.json();
      return { success: true, data };
    }, undefined);

    if (result.success) {
      setPreview(`✅ ${file.name} - ${t('upload.messages.uploadSuccess')}`);
      handleSuccessAndReset();
    }
  };

  const handleUrlSubmit = async () => {
    if (!urlInput.trim() || !materialTitle.trim()) {
      setFileError(t('upload.messages.urlAndTitleRequired'));
      return;
    }

    setFileUploading(true);
    setFileError(null);

    try {
      const result = await uploadMaterial(async () => {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/materials/from-url`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${getAuthToken()}`
          },
          body: JSON.stringify({
            url: urlInput.trim(),
            title: materialTitle.trim(),
            content_type: 'text/plain'
          })
        });

        if (!response.ok) {
          throw new Error('Failed to create material from URL');
        }

        const data = await response.json();
        return { success: true, data };
      }, undefined);

      if (result.success) {
        setPreview(`✅ ${urlInput} - ${t('upload.messages.uploadSuccess')}`);
        handleSuccessAndReset();
      }
    } catch (error) {
      setFileError(
        error instanceof Error ? error.message : t('upload.messages.uploadFailed')
      );
    } finally {
      setFileUploading(false);
    }
  };

  const handleTextSubmit = async () => {
    if (!textContent.trim() || !materialTitle.trim()) {
      setFileError(t('upload.messages.textAndTitleRequired'));
      return;
    }

    setFileUploading(true);
    setFileError(null);

    try {
      const result = await uploadMaterial(async () => {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/materials/from-text`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${getAuthToken()}`
          },
          body: JSON.stringify({
            text_content: textContent.trim(),
            title: materialTitle.trim(),
            content_type: 'text/plain'
          })
        });

        if (!response.ok) {
          throw new Error('Failed to create material from text');
        }

        const data = await response.json();
        return { success: true, data };
      }, undefined);

      if (result.success) {
        setPreview(`✅ ${materialTitle} - ${t('upload.messages.uploadSuccess')}`);
        handleSuccessAndReset();
      }
    } catch (error) {
      setFileError(
        error instanceof Error ? error.message : t('upload.messages.uploadFailed')
      );
    } finally {
      setFileUploading(false);
    }
  };

  const handleSuccessAndReset = () => {
    setIsResetting(true);

    setTimeout(() => {
      setFile(null);
      setPreview("");
      setUploadedFile(null);
      setSelectedFileType(null);
      setSelectedTagIds([]);
      setUrlInput("");
      setTextContent("");
      setMaterialTitle("");
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }

      setIsResetting(false);
    }, 1500);
  };

  const handleTagToggle = (tagId: string) => {
    setSelectedTagIds((prev) => {
      if (prev.includes(tagId)) {
        return prev.filter((id) => id !== tagId);
      } else {
        return [...prev, tagId];
      }
    });
  };

  const handleReset = () => {
    setFile(null);
    setPreview("");
    setUploadedFile(null);
    setSelectedFileType(null);
    setSelectedTagIds([]);
    setFileError(null);
    setUrlInput("");
    setTextContent("");
    setMaterialTitle("");
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  // Show loading while checking authentication
  if (authLoading) {
    return (
      <Layout
        title={`Upload Material - ${t('brand.name')}`}
        description="Upload a new material to 丹炉 platform"
      >
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-2 border-blue-500 border-t-transparent mx-auto mb-4"></div>
            <p className="text-gray-600">{t('upload.messages.checkingAuth')}</p>
          </div>
        </div>
      </Layout>
    );
  }

  // Show login prompt if not authenticated
  if (!isLoggedIn) {
    return (
      <Layout
        title={`Upload Material - ${t('brand.name')}`}
        description="Upload a new material to 丹炉 platform"
      >
        <div className="max-w-md mx-auto text-center">
          <div className="w-16 h-16 bg-blue-50 rounded-button flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.5 0L4.314 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <h1 className="text-2xl font-semibold text-gray-900 mb-2">{t('auth.loginRequired')}</h1>
          <p className="text-gray-600 mb-6">{t('auth.loginRequiredMessage')}</p>
          <Link href="/login?redirect=/my-upload">
            <Button variant="primary">
              {t('auth.goToLogin')}
            </Button>
          </Link>
        </div>
      </Layout>
    );
  }

  return (
    <Layout
      title={`${t('nav.upload')} - ${t('brand.name')}`}
      description={`${t('upload.title')} to ${t('brand.name')} platform`}
    >
      <div className={`max-w-3xl mx-auto transition-opacity duration-500 ${isResetting ? 'opacity-50' : 'opacity-100'}`}>
        <div className="mb-8">
          <h1 className="text-3xl font-semibold mb-4">{t('upload.title')}</h1>
          <p className="text-gray-600">
            {t('upload.subtitle')}
          </p>
        </div>

        <Card padding="lg">
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-100 rounded-input text-sm text-danger">
              {error}
            </div>
          )}

          {data?.success && (
            <div className="mb-6 p-4 bg-green-50 border border-green-100 rounded-input text-sm text-green-600">
              {t('upload.messages.uploadSuccess')}
            </div>
          )}

          {fileError && (
            <div className="mb-6 p-4 bg-red-50 border border-red-100 rounded-input text-sm text-danger">
              File upload error: {fileError}
            </div>
          )}

          {/* Input type selection */}
          <div className="mb-8">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">{t('upload.selectInputType')}</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {inputTypes.map((inputType) => (
                <div
                  key={inputType.id}
                  onClick={() => handleInputTypeSelect(inputType)}
                  className={`border-2 border-dashed rounded-card p-6 text-center cursor-pointer transition-all duration-200 ${
                    selectedFileType?.id === inputType.id
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-blue-500 hover:bg-gray-50'
                  }`}
                >
                  <div className="text-4xl mb-3">{inputType.icon}</div>
                  <h4 className="font-medium text-gray-800 mb-2">{inputType.name}</h4>
                  <p className="text-sm text-gray-600 mb-2">{inputType.description}</p>
                  {inputType.maxSize > 0 && (
                    <p className="text-xs text-gray-500">
                      {t('upload.maxSize')}: {inputType.maxSize}MB
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* URL input form */}
          {selectedFileType?.id === 'url' && (
            <div className="mb-8 p-6 bg-gray-50 rounded-card">
              <h4 className="font-medium text-gray-800 mb-4">{t('upload.urlForm.title')}</h4>
              <div className="space-y-4">
                <Input
                  id="material-title"
                  type="text"
                  label={t('upload.form.materialTitle')}
                  value={materialTitle}
                  onChange={(e) => setMaterialTitle(e.target.value)}
                  placeholder={t('upload.urlForm.titlePlaceholder')}
                />
                <Input
                  id="url-input"
                  type="url"
                  label={t('upload.urlForm.urlLabel')}
                  value={urlInput}
                  onChange={(e) => setUrlInput(e.target.value)}
                  placeholder={t('upload.urlForm.urlPlaceholder')}
                />
                <Button
                  onClick={handleUrlSubmit}
                  disabled={fileUploading || !urlInput.trim() || !materialTitle.trim()}
                  loading={fileUploading}
                  variant="primary"
                  fullWidth
                >
                  {t('upload.urlForm.submitButton')}
                </Button>
              </div>
            </div>
          )}

          {/* Text input form */}
          {selectedFileType?.id === 'text-paste' && (
            <div className="mb-8 p-6 bg-gray-50 rounded-card">
              <h4 className="font-medium text-gray-800 mb-4">{t('upload.textForm.title')}</h4>
              <div className="space-y-4">
                <Input
                  id="material-title-text"
                  type="text"
                  label={t('upload.form.materialTitle')}
                  value={materialTitle}
                  onChange={(e) => setMaterialTitle(e.target.value)}
                  placeholder={t('upload.textForm.titlePlaceholder')}
                />
                <Textarea
                  id="text-content"
                  label={t('upload.textForm.contentLabel')}
                  value={textContent}
                  onChange={(e) => setTextContent(e.target.value)}
                  placeholder={t('upload.textForm.contentPlaceholder')}
                  rows={8}
                />
                <Button
                  onClick={handleTextSubmit}
                  disabled={fileUploading || !textContent.trim() || !materialTitle.trim()}
                  loading={fileUploading}
                  variant="primary"
                  fullWidth
                >
                  {t('upload.textForm.submitButton')}
                </Button>
              </div>
            </div>
          )}

          {/* Hidden file input */}
          <input
            type="file"
            ref={fileInputRef}
            className="hidden"
            onChange={handleFileChange}
            disabled={fileUploading}
          />

          {/* Upload status display */}
          {fileUploading && (
            <div className="mb-6 text-center">
              <div className="inline-flex items-center px-4 py-2 bg-blue-50 rounded-input">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500 mr-3"></div>
                <span className="text-blue-600">{t('upload.form.uploading')}</span>
              </div>
            </div>
          )}

          {/* File preview - only for file upload */}
          {preview && selectedFileType?.id === 'file-text' && (
            <div className={`mb-6 p-4 bg-gray-50 rounded-card transition-all duration-300 ${isResetting ? 'animate-pulse' : ''}`}>
              <div className="flex items-center justify-between mb-3">
                <span className="text-gray-700">{preview}</span>
                <Button variant="tertiary" size="sm" onClick={handleReset}>
                  {t('common.cancel')}
                </Button>
              </div>
              {!fileUploading && !data?.success && file && (
                <div className="flex gap-3">
                  <Button onClick={handleManualUpload}>
                    {t('upload.form.uploadNow')}
                  </Button>
                </div>
              )}
            </div>
          )}

          {/* Success state display */}
          {preview && (selectedFileType?.id === 'url' || selectedFileType?.id === 'text-paste') && (
            <div className={`mb-6 p-4 bg-gray-50 rounded-card transition-all duration-300 ${isResetting ? 'animate-pulse' : ''}`}>
              <div className="flex items-center justify-between">
                <span className="text-gray-700">{preview}</span>
                <Button variant="tertiary" size="sm" onClick={handleReset}>
                  {t('common.cancel')}
                </Button>
              </div>
            </div>
          )}
        </Card>
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