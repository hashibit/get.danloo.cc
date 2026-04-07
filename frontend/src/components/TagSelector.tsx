import React from 'react';
import { TagType } from '../types/tag';

interface TagSelectorProps {
  tags: TagType[];
  selectedTagIds: string[];
  onTagToggle: (tagId: string) => void;
}

export default function TagSelector({ tags, selectedTagIds, onTagToggle }: TagSelectorProps) {
  return (
    <div className="mb-4">
      <label className="block text-gray-700 text-sm font-bold mb-2">
        标签选择
      </label>
      <div className="flex flex-wrap gap-2">
        {tags.map((tag) => (
          <button
            key={tag.id}
            type="button"
            onClick={() => onTagToggle(tag.id)}
            className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
              selectedTagIds.includes(tag.id)
                ? tag.color === 'yellow' ? 'bg-yellow-500 text-white' :
                  tag.color === 'blue' ? 'bg-blue-500 text-white' :
                  tag.color === 'green' ? 'bg-green-500 text-white' :
                  tag.color === 'red' ? 'bg-red-500 text-white' :
                  tag.color === 'purple' ? 'bg-purple-500 text-white' :
                  'bg-gray-500 text-white'
                : tag.color === 'yellow' ? 'bg-yellow-100 text-yellow-800 hover:bg-yellow-200' :
                  tag.color === 'blue' ? 'bg-blue-100 text-blue-800 hover:bg-blue-200' :
                  tag.color === 'green' ? 'bg-green-100 text-green-800 hover:bg-green-200' :
                  tag.color === 'red' ? 'bg-red-100 text-red-800 hover:bg-red-200' :
                  tag.color === 'purple' ? 'bg-purple-100 text-purple-800 hover:bg-purple-200' :
                  'bg-gray-100 text-gray-800 hover:bg-gray-200'
            }`}
          >
            {tag.name}
          </button>
        ))}
      </div>
      <p className="text-gray-500 text-xs mt-2">
        选择适合您文章的标签。可以多选。
      </p>
    </div>
  );
}