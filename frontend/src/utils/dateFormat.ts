/**
 * Date and time formatting utilities with timezone support.
 */

/**
 * Format a date/time string to local timezone.
 * @param dateString ISO 8601 date string (UTC)
 * @param options Intl.DateTimeFormatOptions
 * @returns Formatted string in user's local timezone
 */
export function formatDateTime(
  dateString: string | null | undefined,
  options?: Intl.DateTimeFormatOptions
): string {
  if (!dateString) return 'N/A'
  
  try {
    const date = new Date(dateString)
    
    if (isNaN(date.getTime())) {
      return 'Invalid date'
    }
    
    const defaultOptions: Intl.DateTimeFormatOptions = {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      ...options,
    }
    
    return date.toLocaleString(undefined, defaultOptions)
  } catch (error) {
    console.error('Error formatting date:', error)
    return 'Invalid date'
  }
}

/**
 * Format time only (HH:MM) in local timezone.
 * @param dateString ISO 8601 date string (UTC)
 * @returns Time string like "14:30"
 */
export function formatTime(dateString: string | null | undefined): string {
  if (!dateString) return 'N/A'
  
  try {
    const date = new Date(dateString)
    
    if (isNaN(date.getTime())) {
      return 'Invalid'
    }
    
    return date.toLocaleTimeString(undefined, {
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch (error) {
    console.error('Error formatting time:', error)
    return 'Invalid'
  }
}

/**
 * Format date only (without time).
 * @param dateString ISO 8601 date string (UTC)
 * @returns Date string like "Jan 15, 2024"
 */
export function formatDate(dateString: string | null | undefined): string {
  if (!dateString) return 'N/A'
  
  try {
    const date = new Date(dateString)
    
    if (isNaN(date.getTime())) {
      return 'Invalid date'
    }
    
    return date.toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  } catch (error) {
    console.error('Error formatting date:', error)
    return 'Invalid'
  }
}

/**
 * Format relative time (e.g., "2 hours ago", "in 5 minutes").
 * @param dateString ISO 8601 date string (UTC)
 * @returns Relative time string
 */
export function formatRelativeTime(dateString: string | null | undefined): string {
  if (!dateString) return 'N/A'
  
  try {
    const date = new Date(dateString)
    const now = new Date()
    const diffMs = date.getTime() - now.getTime()
    const diffSec = Math.abs(Math.floor(diffMs / 1000))
    const diffMin = Math.floor(diffSec / 60)
    const diffHour = Math.floor(diffMin / 60)
    const diffDay = Math.floor(diffHour / 24)
    
    const rtf = new Intl.RelativeTimeFormat(undefined, { numeric: 'auto' })
    
    if (diffDay > 0) {
      return rtf.format(diffMs > 0 ? diffDay : -diffDay, 'day')
    } else if (diffHour > 0) {
      return rtf.format(diffMs > 0 ? diffHour : -diffHour, 'hour')
    } else if (diffMin > 0) {
      return rtf.format(diffMs > 0 ? diffMin : -diffMin, 'minute')
    } else {
      return 'just now'
    }
  } catch (error) {
    console.error('Error formatting relative time:', error)
    return 'Unknown'
  }
}

/**
 * Format timestamp for chat messages (time if today, date + time otherwise).
 * @param dateString ISO 8601 date string (UTC)
 * @returns Formatted string
 */
export function formatChatTimestamp(dateString: string | null | undefined): string {
  if (!dateString) return ''
  
  try {
    const date = new Date(dateString)
    const now = new Date()
    const isToday = 
      date.getDate() === now.getDate() &&
      date.getMonth() === now.getMonth() &&
      date.getFullYear() === now.getFullYear()
    
    if (isToday) {
      return formatTime(dateString)
    } else {
      return formatDateTime(dateString, {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      })
    }
  } catch (error) {
    console.error('Error formatting chat timestamp:', error)
    return ''
  }
}
