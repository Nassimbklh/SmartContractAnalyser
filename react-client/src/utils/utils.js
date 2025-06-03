/**
 * Utility functions for the application
 */

/**
 * Extract user information from JWT token
 * @param {string} token - JWT token
 * @returns {object} User information
 */
export const getUserFromToken = (token) => {
  if (!token) return null;
  try {
    // JWT tokens are in format: header.payload.signature
    // We need the payload part
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    );
    return JSON.parse(jsonPayload);
  } catch (error) {
    console.error('Error parsing token:', error);
    return null;
  }
};

/**
 * Format date string
 * @param {string} dateString - Date string
 * @returns {string} Formatted date
 */
export const formatDate = (dateString) => {
  const date = new Date(dateString);
  return date.toLocaleString();
};

/**
 * Download a blob as a file
 * @param {Blob} blob - The blob to download
 * @param {string} filename - The name of the file to download
 */
export const downloadBlob = (blob, filename) => {
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  window.URL.revokeObjectURL(url);
};

/**
 * Handle API errors and return a user-friendly error message
 * @param {Error} error - The error object from the API call
 * @returns {string} A user-friendly error message
 */
export const handleApiError = (error) => {
  if (error.response) {
    // The request was made and the server responded with a status code
    // that falls out of the range of 2xx
    if (error.response.data && error.response.data.error) {
      return error.response.data.error;
    }
    return `Erreur ${error.response.status}: ${error.response.statusText}`;
  } else if (error.request) {
    // The request was made but no response was received
    return "Pas de réponse du serveur. Vérifiez votre connexion.";
  } else {
    // Something happened in setting up the request that triggered an Error
    return error.message || "Une erreur inconnue s'est produite";
  }
};
