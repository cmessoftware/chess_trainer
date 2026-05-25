// Service for Error Logs API calls
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Get error logs with optional filters and pagination
 * @param {number} limit - Number of logs per page (default: 50)
 * @param {number} offset - Offset for pagination (default: 0)
 * @param {string|null} severity - Filter by severity (critical, error, warning, info)
 * @param {string|null} category - Filter by category (feature_extraction, import, database, etc.)
 * @returns {Promise<{errors: Array, total: number, limit: number, offset: number}>}
 */
export const getErrorLogs = async (limit = 50, offset = 0, severity = null, category = null) => {
    try {
        const params = new URLSearchParams({
            limit: limit.toString(),
            offset: offset.toString()
        });

        if (severity) params.append('severity', severity);
        if (category) params.append('category', category);

        const response = await axios.get(
            `${API_BASE_URL}/api/features/error-logs?${params.toString()}`,
            {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            }
        );

        return response.data;
    } catch (error) {
        console.error('Error fetching error logs:', error);
        throw error;
    }
};

/**
 * Get detailed information about a specific error log
 * @param {string} errorId - Error log ID
 * @returns {Promise<Object>} - Error log details
 */
export const getErrorLogDetail = async (errorId) => {
    try {
        const response = await axios.get(
            `${API_BASE_URL}/api/features/error-logs/${errorId}`,
            {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            }
        );

        return response.data;
    } catch (error) {
        console.error(`Error fetching error log ${errorId}:`, error);
        throw error;
    }
};

/**
 * Mark error log as resolved
 * @param {string} errorId - Error log ID
 * @param {string|null} resolutionNotes - Optional resolution notes
 * @returns {Promise<{success: boolean}>}
 */
export const resolveErrorLog = async (errorId, resolutionNotes = null) => {
    try {
        const response = await axios.put(
            `${API_BASE_URL}/api/features/error-logs/${errorId}/resolve`,
            {
                resolution_notes: resolutionNotes
            },
            {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                    'Content-Type': 'application/json'
                }
            }
        );

        return response.data;
    } catch (error) {
        console.error(`Error resolving error log ${errorId}:`, error);
        throw error;
    }
};

export default {
    getErrorLogs,
    getErrorLogDetail,
    resolveErrorLog
};
