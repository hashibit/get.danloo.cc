// Enhanced pellet types with intelligent generation support
export interface Pellet {
  id: string;
  title: string;
  content: string;
  status: 'in-queue' | 'completed' | 'draft' | 'processing';
  user_id: string;
  material_ids?: string[];
  is_gold: boolean;
  view_count: number;
  tags: Tag[];
  
  // New AI-enhanced fields
  ai_score?: number;  // 0-100 AI quality score
  pellet_type?: 'high_value' | 'standard' | 'specialized';
  generation_metadata?: {
    ai_generated: boolean;
    pellet_type: string;
    generation_timestamp: string;
    source_materials: string[];
  };
  
  created_at: string;
  updated_at: string;
}

export interface Tag {
  id: string;
  name: string;
  color: string;
  description: string;
  weight?: number;
  created_at: string;
  updated_at: string;
}

// Request/Response types for batch pellet creation
export interface BatchPelletCreateRequest {
  material_ids: string[];
}

export interface BatchPelletCreateResponse {
  job_id: string;
  status: string;
  message: string;
  material_count: number;
}

// Material analysis types
export interface MaterialAnalysis {
  value_score: number;  // 0-1 scale
  pellet_potential: number;  // Number of potential pellets
  content_quality: 'high' | 'medium' | 'low';
  suggested_titles: string[];
  extracted_content: string;
}

// Job status tracking
export interface JobStatus {
  job_id: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  progress?: number;  // 0-100 percentage
  message?: string;
  created_at: string;
  updated_at: string;
}

// Pellet generation result
export interface PelletGenerationResult {
  job_id: string;
  generated_pellets: Pellet[];
  failed_materials: string[];
  analysis_summary: {
    total_materials: number;
    high_value_count: number;
    generated_pellets_count: number;
    average_quality_score: number;
  };
}