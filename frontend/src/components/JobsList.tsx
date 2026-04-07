import React, { useState } from 'react';
import { useTranslation } from 'next-i18next';
import { Job, jobService } from '../services/jobs';

interface JobsListProps {
  jobs: Job[];
  loading?: boolean;
  onRefresh?: () => void;
  onRetry?: (jobId: string) => void;
}

export default function JobsList({ jobs, loading, onRefresh, onRetry }: JobsListProps) {
  const { t } = useTranslation('common');
  const [isExpanded, setIsExpanded] = useState(false);

  const runningJobs = jobs.filter(job => job.status === 'pending' || job.status === 'in_progress');
  const completedJobs = jobs.filter(job => job.status === 'completed' || job.status === 'failed' || job.status === 'cancelled');

  if (loading) {
    return (
      <div className="bg-white border border-gray-200 rounded-xl p-6 mb-8">
        <div className="flex items-center">
          <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-green-600 mr-3"></div>
          <span className="text-gray-600">加载炼丹任务中...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white border border-gray-200 rounded-xl mb-8 overflow-hidden">
      {/* Header */}
      <div 
        className="flex items-center justify-between p-6 cursor-pointer hover:bg-gray-50 transition-colors"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center">
          <div className="flex items-center mr-4">
            <div className="w-8 h-8 bg-gradient-to-r from-purple-400 to-pink-500 rounded-full flex items-center justify-center mr-3">
              <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 8.172V5L8 4z" />
              </svg>
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">炼丹任务</h3>
              <p className="text-sm text-gray-500">
                {runningJobs.length > 0 ? `${runningJobs.length} 个任务正在运行` : '暂无运行中的任务'}
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          {/* Running jobs count */}
          {runningJobs.length > 0 && (
            <div className="flex items-center space-x-2">
              {runningJobs.filter(job => job.status === 'in_progress').length > 0 && (
                <div className="flex items-center px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-sm">
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse mr-2"></div>
                  炼丹中 {runningJobs.filter(job => job.status === 'in_progress').length}
                </div>
              )}
              {runningJobs.filter(job => job.status === 'pending').length > 0 && (
                <div className="px-3 py-1 bg-yellow-50 text-yellow-700 rounded-full text-sm">
                  排队中 {runningJobs.filter(job => job.status === 'pending').length}
                </div>
              )}
            </div>
          )}
          
          {/* Refresh button */}
          {onRefresh && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onRefresh();
              }}
              className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
              title="刷新任务状态"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </button>
          )}
          
          {/* Expand/Collapse Icon */}
          <svg 
            className={`w-5 h-5 text-gray-400 transition-transform ${isExpanded ? 'rotate-180' : ''}`} 
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </div>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="border-t border-gray-200">
          {/* Running Jobs */}
          {runningJobs.length > 0 && (
            <div className="p-6 border-b border-gray-100">
              <h4 className="text-sm font-medium text-gray-700 mb-3">正在运行的任务</h4>
              <div className="space-y-3">
                {runningJobs.map((job) => (
                  <JobItem key={job.job_id} job={job} onRetry={onRetry} />
                ))}
              </div>
            </div>
          )}

          {/* Completed Jobs */}
          {completedJobs.length > 0 && (
            <div className="p-6">
              <h4 className="text-sm font-medium text-gray-700 mb-3">最近完成的任务</h4>
              <div className="space-y-3">
                {completedJobs.slice(0, 3).map((job) => (
                  <JobItem key={job.job_id} job={job} onRetry={onRetry} />
                ))}
              </div>
            </div>
          )}

          {/* Empty state */}
          {jobs.length === 0 && (
            <div className="p-8 text-center">
              <div className="text-4xl mb-3">🧪</div>
              <h4 className="text-lg font-medium text-gray-800 mb-2">暂无炼丹任务</h4>
              <p className="text-gray-600">创建材料后开始炼丹之旅</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function JobItem({ job, onRetry }: { job: Job; onRetry?: (jobId: string) => void }) {
  const [isRetrying, setIsRetrying] = useState(false);
  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffDays > 0) return `${diffDays}天前`;
    if (diffHours > 0) return `${diffHours}小时前`;
    if (diffMins > 0) return `${diffMins}分钟前`;
    return '刚刚';
  };

  const handleRetry = async () => {
    if (isRetrying || !onRetry) return;
    
    setIsRetrying(true);
    try {
      await jobService.retryJob(job.job_id);
      onRetry(job.job_id);
    } catch (error) {
      console.error('Failed to retry job:', error);
      alert('重试任务失败，请稍后再试');
    } finally {
      setIsRetrying(false);
    }
  };

  return (
    <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
      <div className="flex items-center flex-1">
        <div className="flex-1">
          <div className="flex items-center space-x-2 mb-1">
            <span className="text-sm font-medium text-gray-900">
              {jobService.getJobTypeText(job.job_type)}
            </span>
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${jobService.getJobStatusColor(job.status)}`}>
              {jobService.getJobStatusText(job.status)}
            </span>
          </div>
          <div className="flex items-center text-xs text-gray-500 space-x-2">
            <span>创建于 {formatTime(job.created_at)}</span>
            {job.job_metadata?.materials_count && (
              <span>• {job.job_metadata.materials_count} 个材料</span>
            )}
            {job.job_metadata?.pellets_generated && (
              <span>• 生成 {job.job_metadata.pellets_generated} 个丹药</span>
            )}
          </div>
          {job.error_message && (
            <div className="text-xs text-red-600 mt-1">
              错误: {job.error_message}
            </div>
          )}
          
          {/* Retry button for failed and cancelled jobs */}
          {(job.status === 'failed' || job.status === 'cancelled') && onRetry && (
            <div className="mt-2">
              <button
                onClick={handleRetry}
                disabled={isRetrying}
                className={`px-3 py-1 text-xs font-medium rounded transition-colors ${
                  isRetrying
                    ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                    : 'bg-blue-600 text-white hover:bg-blue-700'
                }`}
              >
                {isRetrying ? '重试中...' : '重试'}
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Progress indicator for running jobs */}
      {job.status === 'in_progress' && (
        <div className="ml-3">
          <div className="w-6 h-6 border-2 border-blue-200 border-t-blue-600 rounded-full animate-spin"></div>
        </div>
      )}
    </div>
  );
}