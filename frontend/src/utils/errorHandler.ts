import { ElMessage, ElNotification } from 'element-plus'

export interface ErrorInfo {
  message: string
  code?: string | number
  detail?: string
  timestamp?: string
}

export class ErrorHandler {
  private static instance: ErrorHandler
  private errorLog: ErrorInfo[] = []

  static getInstance(): ErrorHandler {
    if (!ErrorHandler.instance) {
      ErrorHandler.instance = new ErrorHandler()
    }
    return ErrorHandler.instance
  }

  handleError(error: Error | ErrorInfo, context?: string): void {
    const errorInfo: ErrorInfo = this.normalizeError(error, context)
    
    // Log error
    this.logError(errorInfo)
    
    // Show user notification
    this.showErrorNotification(errorInfo)
    
    // Report to console in development
    if (import.meta.env.DEV) {
      console.error('[ErrorHandler]', errorInfo, error)
    }
  }

  private normalizeError(error: Error | ErrorInfo, context?: string): ErrorInfo {
    if (error instanceof Error) {
      return {
        message: error.message,
        detail: context,
        timestamp: new Date().toISOString(),
        code: 'JS_ERROR'
      }
    }
    
    return {
      ...error,
      timestamp: error.timestamp || new Date().toISOString(),
      detail: error.detail || context
    }
  }

  private logError(errorInfo: ErrorInfo): void {
    this.errorLog.push(errorInfo)
    
    // Keep only last 100 errors
    if (this.errorLog.length > 100) {
      this.errorLog = this.errorLog.slice(-100)
    }
  }

  private showErrorNotification(errorInfo: ErrorInfo): void {
    const isNetworkError = errorInfo.message?.includes('fetch') || 
                          errorInfo.message?.includes('network') ||
                          errorInfo.code === 'NETWORK_ERROR'
    
    const isServerError = typeof errorInfo.code === 'number' && 
                         errorInfo.code >= 500
    
    if (isNetworkError) {
      ElNotification({
        title: 'Network Error',
        message: 'Please check your connection and try again.',
        type: 'error',
        duration: 5000
      })
    } else if (isServerError) {
      ElNotification({
        title: 'Server Error',
        message: 'Something went wrong on our end. Please try again later.',
        type: 'error',
        duration: 5000
      })
    } else {
      ElMessage({
        message: errorInfo.message || 'An unexpected error occurred',
        type: 'error',
        duration: 3000
      })
    }
  }

  getErrorLog(): ErrorInfo[] {
    return [...this.errorLog]
  }

  clearErrorLog(): void {
    this.errorLog = []
  }

  // Handle API errors specifically
  handleApiError(response: Response, context?: string): ErrorInfo {
    const errorInfo: ErrorInfo = {
      message: `API Error: ${response.statusText}`,
      code: response.status,
      detail: context,
      timestamp: new Date().toISOString()
    }
    
    this.handleError(errorInfo)
    return errorInfo
  }
}

// Global error handler instance
export const errorHandler = ErrorHandler.getInstance()

// Setup global error handlers
export function setupGlobalErrorHandlers(): void {
  // Handle unhandled promise rejections
  window.addEventListener('unhandledrejection', (event) => {
    errorHandler.handleError(
      new Error(`Unhandled Promise Rejection: ${event.reason}`),
      'Global Promise Handler'
    )
  })

  // Handle global JavaScript errors
  window.addEventListener('error', (event) => {
    errorHandler.handleError(
      new Error(`${event.message} at ${event.filename}:${event.lineno}`),
      'Global Error Handler'
    )
  })
}

// Axios interceptor for API errors
export function setupAxiosErrorHandler(): void {
  // This should be called in main.ts to setup axios interceptors
}