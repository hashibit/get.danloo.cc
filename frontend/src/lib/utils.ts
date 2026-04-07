/**
 * Utility functions for the application
 */

/**
 * Convert comma-separated string to array of strings
 * @param idsString - Comma-separated string of IDs
 * @returns Array of trimmed IDs or undefined if input is empty
 */
export const parseIds = (idsString: string | null | undefined): string[] | undefined => {
  if (!idsString) return undefined;
  return idsString.split(',').filter(id => id.trim() !== '');
};