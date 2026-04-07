import React from 'react';
import { TagType } from '../types/tag';

interface TagDisplayProps {
  tag: TagType;
  className?: string;
}

export default function TagDisplay({ tag, className = '' }: TagDisplayProps) {
  return (
    <span 
      className={`px-2 py-1 rounded-full text-xs font-medium inline-block ${
        tag.color === 'yellow' ? 'bg-yellow-100 text-yellow-800' :
        tag.color === 'blue' ? 'bg-blue-100 text-blue-800' :
        tag.color === 'green' ? 'bg-green-100 text-green-800' :
        tag.color === 'red' ? 'bg-red-100 text-red-800' :
        tag.color === 'purple' ? 'bg-purple-100 text-purple-800' :
        'bg-gray-100 text-gray-800'
      } ${className}`}
    >
      {tag.name}
    </span>
  );
}