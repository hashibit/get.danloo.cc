import React from 'react';
import { TagType } from '../types/tag';
import TagDisplay from './TagDisplay';

interface PelletCardProps {
  id: string;
  title: string;
  tags: TagType[];
  materialIds?: string[];
  processingJobIds?: string[];
  onView: (id: string) => void;
  onShare: (id: string) => void;
}

export default function PelletCard({ id, title, tags, materialIds, processingJobIds, onView, onShare }: PelletCardProps) {
  // 如果没有标签，则显示"普通丹"
  const displayTags = tags.length > 0 ? tags : [{ id: 'default', name: '普通丹', color: 'gray', description: 'Default tag' }];

  return (
    <div className="border-b pb-4">
      <h3 className="text-xl font-medium">{title}</h3>
      <div className="flex justify-between items-center mt-2">
        <div className="flex flex-wrap gap-2">
          {displayTags.map((tag) => (
            <TagDisplay key={tag.id} tag={tag} />
          ))}
        </div>
      </div>
      <div className="mt-2">
        <button
          className="primary-button mr-2"
          onClick={() => onView(id)}
        >
          View
        </button>
        <button
          className="secondary-button"
          onClick={() => onShare(id)}
        >
          Share
        </button>
      </div>
    </div>
  );
}
