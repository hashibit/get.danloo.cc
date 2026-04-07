import React from 'react';

interface MaterialCardProps {
  id: string;
  title: string;
  contentType: string;
  createdAt: string;
  onProcess: (id: string) => void;
  onView: (id: string) => void;
}

const getContentTypeDisplayName = (contentType: string): string => {
  const typeMap: { [key: string]: string } = {
    'text/plain': '文本文档',
    'application/pdf': 'PDF文档',
    'image/jpeg': '图片文件',
    'image/png': '图片文件',
    'image/gif': '图片文件',
    'video/mp4': '视频文件',
    'audio/mpeg': '音频文件',
  };
  
  return typeMap[contentType] || contentType;
};

export default function MaterialCard({ id, title, contentType, createdAt, onProcess, onView }: MaterialCardProps) {
  const displayType = getContentTypeDisplayName(contentType);
  
  return (
    <div className="border-b pb-4">
      <h3 className="text-xl font-medium">{title}</h3>
      <div className="flex justify-between items-center mt-2">
        <span className="text-gray-600">{displayType}</span>
        <span className="text-gray-500 text-sm">{createdAt}</span>
      </div>
      <div className="mt-2">
        <button 
          className="primary-button mr-2"
          onClick={() => onProcess(id)}
        >
          Process
        </button>
        <button 
          className="secondary-button"
          onClick={() => onView(id)}
        >
          View
        </button>
      </div>
    </div>
  );
}