import { apiRequest } from './api';

export interface Job {
  job_id: string;
  job_type: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed' | 'cancelled';
  user_id: string;
  priority: number;
  job_metadata?: Record<string, any>;
  error_message?: string;
  created_at: string;
  updated_at: string;
}

export interface JobsResponse {
  jobs: Job[];
  total: number;
}

export interface GetJobsParams {
  user_id: string;
  limit?: number;
  offset?: number;
}

class JobService {
  private apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

  async getUserJobs(params: GetJobsParams) {
    const { user_id, limit = 20, offset = 0 } = params;
    return await apiRequest<JobsResponse>(`/jobs?user_id=${user_id}&limit=${limit}&offset=${offset}`);
  }

  async getJobStatus(jobId: string) {
    return await apiRequest<Job>(`/job/${jobId}`);
  }

  async getTaskStatus(taskId: string) {
    return await apiRequest<any>(`/task/${taskId}`);
  }

  async retryJob(jobId: string) {
    return await apiRequest<any>(`/job/${jobId}/retry`, {
      method: 'POST'
    });
  }

  getJobStatusText(status: Job['status']): string {
    const statusMap = {
      pending: '排队中',
      in_progress: '炼丹中',
      completed: '已完成',
      failed: '失败',
      cancelled: '已取消'
    };
    return statusMap[status] || status;
  }

  getJobTypeText(jobType: string): string {
    const typeMap = {
      material_processing: '材料处理',
      pellet_generation: '丹药生成',
      batch_analysis: '批量分析'
    };
    return typeMap[jobType as keyof typeof typeMap] || jobType;
  }

  getJobStatusColor(status: Job['status']): string {
    const colorMap = {
      pending: 'text-yellow-600 bg-yellow-50',
      in_progress: 'text-blue-600 bg-blue-50',
      completed: 'text-green-600 bg-green-50',
      failed: 'text-red-600 bg-red-50',
      cancelled: 'text-gray-600 bg-gray-50'
    };
    return colorMap[status as keyof typeof colorMap] || 'text-gray-600 bg-gray-50';
  }
}

export const jobService = new JobService();