import { apiRequest } from './api';

export interface FileUploadRequest {
  filename: string;
  file_size?: number;
  content_type?: string;
}

export interface FileUploadResponse {
  object_id: string;
  presigned_url: string;
  expires_in: number;
}

export interface FileObject {
  id: string;
  name: string;
  status: 'pending' | 'uploaded' | 'processing' | 'processed';
  file_info: any;
  created_at: string;
  updated_at: string;
}

export class FileService {
  async initiateUpload(request: FileUploadRequest): Promise<FileUploadResponse> {
    const response = await apiRequest<FileUploadResponse>('/files/upload/init', {
      method: 'POST',
      body: JSON.stringify(request),
    });

    if (!response.success) {
      throw new Error(response.error?.message || 'Failed to initiate file upload');
    }

    return response.data!;
  }

  async uploadToPresignedUrl(presignedUrl: string, file: File, contentType?: string): Promise<void> {
    const headers: HeadersInit = {};
    
    // Set Content-Type to match what was used in presigned URL signature
    if (contentType) {
      headers['Content-Type'] = contentType;
    }
    
    const response = await fetch(presignedUrl, {
      method: 'PUT',
      body: file,
      headers,
    });

    if (!response.ok) {
      throw new Error('Failed to upload file to storage');
    }
  }

  async commitUpload(objectId: string, fileInfo?: any): Promise<FileObject> {
    const response = await apiRequest<FileObject>('/files/upload/commit', {
      method: 'POST',
      body: JSON.stringify({ object_id: objectId, file_info: fileInfo }),
    });

    if (!response.success) {
      throw new Error(response.error?.message || 'Failed to commit file upload');
    }

    return response.data!;
  }

  async getFileObject(objectId: string): Promise<FileObject> {
    const response = await apiRequest<FileObject>(`/objects/${objectId}`, {
      method: 'GET',
    });

    if (!response.success) {
      throw new Error(response.error?.message || 'Failed to retrieve file object');
    }

    return response.data!;
  }

  async deleteFileObject(objectId: string): Promise<void> {
    const response = await apiRequest<void>(`/objects/${objectId}`, {
      method: 'DELETE',
    });

    if (!response.success) {
      throw new Error(response.error?.message || 'Failed to delete file object');
    }
  }

  async uploadFile(file: File, options?: any): Promise<FileObject> {
    // Step 1: Initiate upload
    const initiateRequest: FileUploadRequest = {
      filename: file.name,
      file_size: file.size,
      content_type: file.type,
    };

    const initiateResponse = await this.initiateUpload(initiateRequest);

    // Step 2: Upload file to presigned URL  
    await this.uploadToPresignedUrl(initiateResponse.presigned_url, file, initiateRequest.content_type);

    // Step 3: Commit upload
    const file_info = {
      size: file.size,
      type: file.type,
      ...options,
    };

    const commitResponse = await this.commitUpload(initiateResponse.object_id, file_info);

    return commitResponse;
  }
}

export const fileService = new FileService();
