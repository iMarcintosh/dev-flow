import { AxiosError } from 'axios'

export interface ApiError {
  message: string
  detail?: string
  statusCode?: number
}

/**
 * Extract user-friendly error message from API response
 */
export function getErrorMessage(error: unknown): ApiError {
  if (error instanceof AxiosError) {
    const status = error.response?.status
    const data = error.response?.data

    // Handle validation errors (422)
    if (status === 422 && data?.detail) {
      if (Array.isArray(data.detail)) {
        // Pydantic validation errors
        const messages = data.detail.map((err: any) => err.msg).join(', ')
        return {
          message: 'Validation Error',
          detail: messages,
          statusCode: 422,
        }
      }
      return {
        message: 'Validation Error',
        detail: data.detail,
        statusCode: 422,
      }
    }

    // Handle specific HTTP status codes
    switch (status) {
      case 400:
        return {
          message: 'Bad Request',
          detail: data?.detail || 'Invalid request data',
          statusCode: 400,
        }
      case 401:
        return {
          message: 'Unauthorized',
          detail: 'Please log in to continue',
          statusCode: 401,
        }
      case 403:
        return {
          message: 'Forbidden',
          detail: 'You don\'t have permission to perform this action',
          statusCode: 403,
        }
      case 404:
        return {
          message: 'Not Found',
          detail: data?.detail || 'The requested resource was not found',
          statusCode: 404,
        }
      case 409:
        return {
          message: 'Conflict',
          detail: data?.detail || 'Resource already exists',
          statusCode: 409,
        }
      case 500:
        return {
          message: 'Server Error',
          detail: 'Something went wrong on our end. Please try again later.',
          statusCode: 500,
        }
      default:
        return {
          message: 'Request Failed',
          detail: data?.detail || error.message || 'An unexpected error occurred',
          statusCode: status,
        }
    }
  }

  // Handle network errors
  if (error instanceof Error) {
    if (error.message === 'Network Error') {
      return {
        message: 'Network Error',
        detail: 'Cannot connect to server. Please check your internet connection.',
      }
    }
    return {
      message: 'Error',
      detail: error.message,
    }
  }

  // Unknown error type
  return {
    message: 'Unknown Error',
    detail: 'An unexpected error occurred',
  }
}

/**
 * Format validation errors from 422 response for form display
 */
export function getValidationErrors(error: unknown): Record<string, string> {
  if (error instanceof AxiosError) {
    const data = error.response?.data
    if (error.response?.status === 422 && data?.detail && Array.isArray(data.detail)) {
      const errors: Record<string, string> = {}
      data.detail.forEach((err: any) => {
        const field = err.loc[err.loc.length - 1]
        errors[field] = err.msg
      })
      return errors
    }
  }
  return {}
}
