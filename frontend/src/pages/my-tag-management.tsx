import React, { useState } from 'react';
import Head from 'next/head';
import { TagType } from '../types/tag';
import TagDisplay from '../components/TagDisplay';
import Layout from '../components/Layout';
import { Card, CardHeader, CardBody } from '../components/Card';
import { Input } from '../components/Input';
import { Textarea } from '../components/Input';
import { Select } from '../components/Input';
import { Button } from '../components/Button';

export default function TagManagement() {
  // Default tag types
  const defaultTags: TagType[] = [
    { id: 'gold', name: '金丹', color: 'yellow', description: 'High quality pellets with golden content' },
    { id: 'with-image', name: '彩丹-图片', color: 'blue', description: 'Pellets with rich image content' },
    { id: 'with-video', name: '彩丹-视频', color: 'purple', description: 'Pellets with video content' }
  ];

  const [tags, setTags] = useState<TagType[]>(defaultTags);
  const [newTagName, setNewTagName] = useState('');
  const [newTagColor, setNewTagColor] = useState('gray');
  const [newTagDescription, setNewTagDescription] = useState('');
  const [editingTagId, setEditingTagId] = useState<string | null>(null);
  const [error, setError] = useState('');

  const handleAddTag = () => {
    if (!newTagName.trim()) {
      setError('标签名称不能为空');
      return;
    }

    const newTag: TagType = {
      id: `tag-${Date.now()}`,
      name: newTagName,
      color: newTagColor,
      description: newTagDescription
    };

    setTags(prev => [...prev, newTag]);
    setNewTagName('');
    setNewTagColor('gray');
    setNewTagDescription('');
    setError('');
  };

  const handleEditTag = (tag: TagType) => {
    setEditingTagId(tag.id);
    setNewTagName(tag.name);
    setNewTagColor(tag.color);
    setNewTagDescription(tag.description);
  };

  const handleUpdateTag = () => {
    if (!newTagName.trim()) {
      setError('标签名称不能为空');
      return;
    }

    if (!editingTagId) return;

    setTags(prev =>
      prev.map(tag =>
        tag.id === editingTagId
          ? { ...tag, name: newTagName, color: newTagColor, description: newTagDescription }
          : tag
      )
    );

    setEditingTagId(null);
    setNewTagName('');
    setNewTagColor('gray');
    setNewTagDescription('');
    setError('');
  };

  const handleDeleteTag = (tagId: string) => {
    if (defaultTags.some(tag => tag.id === tagId)) {
      setError('不能删除默认标签');
      return;
    }

    setTags(prev => prev.filter(tag => tag.id !== tagId));
    setError('');
  };

  const colorOptions = [
    { value: 'yellow', label: '黄色' },
    { value: 'blue', label: '蓝色' },
    { value: 'green', label: '绿色' },
    { value: 'red', label: '红色' },
    { value: 'purple', label: '紫色' },
    { value: 'gray', label: '灰色' }
  ];

  return (
    <div className="min-h-screen bg-white">
      <Head>
        <title>标签管理 - 丹炉 (Danloo)</title>
        <meta name="description" content="Manage pellet tags in 丹炉 platform" />
        <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
      </Head>

      <Layout title="标签管理 - 丹炉 (Danloo)">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-semibold text-gray-900 mb-2">标签管理</h1>
          <p className="text-gray-600">创建、编辑和删除文章标签类型</p>
        </div>

        {/* Add/Edit tag form */}
        <Card padding="lg" className="mb-8">
          <CardHeader
            title={editingTagId ? '编辑标签' : '添加新标签'}
            subtitle="创建和管理您的标签"
          />

          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-100 rounded-input text-sm text-danger">
              {error}
            </div>
          )}

          <div className="space-y-4">
            <Input
              label="标签名称"
              value={newTagName}
              onChange={(e) => setNewTagName(e.target.value)}
              placeholder="输入标签名称"
              fullWidth
            />

            <Select
              label="标签颜色"
              value={newTagColor}
              onChange={(e) => setNewTagColor(e.target.value)}
              options={colorOptions}
              fullWidth
            />

            <Textarea
              label="标签描述"
              value={newTagDescription}
              onChange={(e) => setNewTagDescription(e.target.value)}
              placeholder="输入标签描述"
              rows={3}
              fullWidth
            />

            <div className="flex items-center gap-3">
              {editingTagId ? (
                <>
                  <Button onClick={handleUpdateTag} variant="primary">
                    更新标签
                  </Button>
                  <Button
                    onClick={() => {
                      setEditingTagId(null);
                      setNewTagName('');
                      setNewTagColor('gray');
                      setNewTagDescription('');
                    }}
                    variant="tertiary"
                  >
                    取消
                  </Button>
                </>
              ) : (
                <Button onClick={handleAddTag} variant="primary" fullWidth>
                  添加标签
                </Button>
              )}
            </div>
          </div>
        </Card>

        {/* Tags list */}
        <Card padding="lg">
          <CardHeader
            title="现有标签"
            subtitle="管理已创建的标签"
          />

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {tags.map((tag) => (
              <div key={tag.id} className="border border-gray-100 rounded-card p-4 flex justify-between items-start">
                <div className="flex-1">
                  <div className="mb-2">
                    <TagDisplay tag={tag} />
                  </div>
                  <p className="text-gray-600 text-sm">{tag.description}</p>
                </div>

                <div className="flex gap-2">
                  <Button variant="tertiary" size="sm" onClick={() => handleEditTag(tag)}>
                    编辑
                  </Button>
                  <Button variant="destructive" size="sm" onClick={() => handleDeleteTag(tag.id)}>
                    删除
                  </Button>
                </div>
              </div>
            ))}
          </div>

          {tags.length === 0 && (
            <p className="text-center text-gray-500 py-8">暂无标签</p>
          )}
        </Card>
      </Layout>
    </div>
  );
}