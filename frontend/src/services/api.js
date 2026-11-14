import { mockService } from './mockService';

/**
 * RevenueGuard Frontend API Service Layer
 * Currently bound exclusively to the frontend mock-data layer
 * ensuring strict frontend isolation during development.
 */
export const api = mockService;
export default api;

