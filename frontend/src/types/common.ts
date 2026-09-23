/**
 * Common response & request DTOs
 */

export interface ApiResponse<T = any> {
  message: string;
  data: T;
  error_code?: string;
  errors?: any;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface PaginationParams {
  page?: number;
  page_size?: number;
}
