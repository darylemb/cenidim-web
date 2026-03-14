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
   * Search songs in the backend.
   * @param {string} query Text to search
   * @param {string} field Field to search (default "all")
   * @returns {Promise<Array>} List of songs that match
   */
  searchSongs: async (query = '', field = 'all') => {
    try {
      const response = await fetch(
        `${BASE_URL}/search?query=${encodeURIComponent(query)}&field=${encodeURIComponent(field)}`
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
};
