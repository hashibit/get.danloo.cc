import { apiRequest } from './api';
import { parseIds } from '../lib/utils';

export interface Material {
  id: string;
  title: string;
  content_type: string;
  file_path: string;
  file_size?: number;
  user_id: string;
  created_at: string;
  updated_at: string;
  pelletIds?: string[];
}


export interface MaterialCreateRequest {
  title: string;
  contentType: string;
  file: File;
}

export interface MaterialListResponse {
  materials: Material[];
  pagination: {
    limit: number;
    offset: number;
    total: number;
  };
}

export interface ProcessingJob {
  jobId: string;
  materialId: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  pelletIds?: string[];
  processingJobIds?: string[];
  errorMessage?: string;
  progress?: number;
  createdAt: string;
  updatedAt: string;
  startedAt?: string;
  completedAt?: string;
}

export const materialService = {
  // Get all materials for current user
  getMaterials: async (params?: {
    limit?: number;
    offset?: number;
    contentType?: string;
  }) => {
    const queryParams = new URLSearchParams();
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.offset) queryParams.append('offset', params.offset.toString());
    if (params?.contentType) queryParams.append('contentType', params.contentType);

    const endpoint = `/materials${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    const response = await apiRequest<MaterialListResponse>(endpoint, {
      method: 'GET',
    });

    // Convert comma-separated strings to arrays
    if (response.success && response.data) {
      response.data.materials = response.data.materials.map(material => ({
        ...material
      }));
    }

    return response;
  },

  // Get material by ID
  getMaterial: async (materialId: string) => {
    const response = await apiRequest<Material>(`/materials/${materialId}`, {
      method: 'GET',
    });

    // Convert comma-separated strings to arrays
    if (response.success && response.data) {
      response.data = {
        ...response.data
      };
    }

    return response;
  },

  // Upload new material
  uploadMaterial: async (data: MaterialCreateRequest) => {
    const formData = new FormData();
    formData.append('title', data.title);
    formData.append('content_type', data.contentType);
    formData.append('file', data.file);

    const response = await apiRequest<Material>('/materials', {
      method: 'POST',
      body: formData,
    });

    // Convert comma-separated strings to arrays
    if (response.success && response.data) {
      response.data = {
        ...response.data,
        pelletIds: parseIds(response.data.pelletIds as any)
      };
    }

    return response;
  },

  // Start processing a material
  processMaterial: async (materialId: string, options?: {
    processingType?: string;
    modelVersion?: string;
    priority?: 'low' | 'normal' | 'high';
  }) => {
    const response = await apiRequest<ProcessingJob>(`/processing/${materialId}`, {
      method: 'POST',
      body: JSON.stringify({ options: options || {} }),
    });

    // Convert comma-separated strings to arrays
    if (response.success && response.data) {
      response.data = {
        ...response.data,
        pelletIds: parseIds(response.data.pelletIds as any)
      };
    }

    return response;
  },

  // Get processing job status
  getProcessingJob: async (jobId: string) => {
    const response = await apiRequest<ProcessingJob>(`/processing/${jobId}`, {
      method: 'GET',
    });

    // Convert comma-separated strings to arrays
    if (response.success && response.data) {
      response.data = {
        ...response.data,
        pelletIds: parseIds(response.data.pelletIds as any)
      };
    }

    return response;
  },

  // Get all processing jobs for current user
  getProcessingJobs: async (params?: {
    limit?: number;
    offset?: number;
    status?: string;
  }) => {
    const queryParams = new URLSearchParams();
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.offset) queryParams.append('offset', params.offset.toString());
    if (params?.status) queryParams.append('status', params.status);

    const endpoint = `/processing${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    const response = await apiRequest<{
      jobs: ProcessingJob[];
      pagination: {
        limit: number;
        offset: number;
        total: number;
      };
    }>(endpoint, {
      method: 'GET',
    });

    // Convert comma-separated strings to arrays
    if (response.success && response.data) {
      response.data.jobs = response.data.jobs.map(job => ({
        ...job,
        pelletIds: parseIds(job.pelletIds as any)
      }));
    }

    return response;
  }
};
