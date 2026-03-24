/**
 * api.js
 * Service for Go/Gin API calls.
 *
 * Uses native fetch promises.
 * Routes use /api to align with the configured proxy.
 */

const BASE_URL = '/api';

export const apiService = {
  /**
   * Search songs in the backend with pagination.
   * @param {string} query Text to search
   * @param {string} field Field to search (default "all")
   * @param {number} page Current page number (default 1)
   * @param {number} limit Number of items per page (default 20)
   * @returns {Promise<Object>} Object with "results" array and "total" count
   */
  searchSongs: async (query = '', field = 'all', page = 1, limit = 20) => {
    try {
      const response = await fetch(
        `${BASE_URL}/search?query=${encodeURIComponent(query)}&field=${encodeURIComponent(field)}&page=${Number(page)}&limit=${Number(limit)}`
      );
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error searching songs:', error);
      throw error;
    }
  },

  /**
   * Get the song detail and lyrics by its ID.
   * @param {number} songId The song ID
   * @returns {Promise<Object>} Song detail
   */
  getSongDetail: async (songId) => {
    try {
      const response = await fetch(`${BASE_URL}/song/${encodeURIComponent(songId)}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error(`Error getting song with ID ${songId}:`, error);
      throw error;
    }
  },
  /**
   * Get songs grouped by year for the timeline view.
   * @returns {Promise<Object>} Object with "years" array and "timeline" map
   */
  getTimeline: async () => {
    try {
      const response = await fetch(`${BASE_URL}/timeline`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error getting timeline:', error);
      throw error;
    }
  },
};
