// Accessibility utilities and enhancements

export class AccessibilityManager {
  private static instance: AccessibilityManager
  private currentFocusedElement: HTMLElement | null = null
  private focusableElements: HTMLElement[] = []

  static getInstance(): AccessibilityManager {
    if (!AccessibilityManager.instance) {
      AccessibilityManager.instance = new AccessibilityManager()
    }
    return AccessibilityManager.instance
  }

  init(): void {
    this.setupKeyboardNavigation()
    this.setupFocusManagement()
    this.addARIALabels()
  }

  private setupKeyboardNavigation(): void {
    document.addEventListener('keydown', (event) => {
      switch (event.key) {
        case 'Tab':
          this.handleTabNavigation(event)
          break
        case 'Escape':
          this.handleEscapeKey(event)
          break
        case 'Enter':
        case ' ':
          this.handleActivation(event)
          break
        case 'ArrowUp':
        case 'ArrowDown':
        case 'ArrowLeft':
        case 'ArrowRight':
          this.handleArrowNavigation(event)
          break
      }
    })
  }

  private handleTabNavigation(event: KeyboardEvent): void {
    this.updateFocusableElements()
    
    if (this.focusableElements.length === 0) return

    const currentIndex = this.focusableElements.indexOf(document.activeElement as HTMLElement)
    
    if (event.shiftKey) {
      // Shift+Tab (backward)
      const nextIndex = currentIndex <= 0 ? this.focusableElements.length - 1 : currentIndex - 1
      this.focusableElements[nextIndex]?.focus()
      event.preventDefault()
    } else {
      // Tab (forward)
      const nextIndex = currentIndex >= this.focusableElements.length - 1 ? 0 : currentIndex + 1
      this.focusableElements[nextIndex]?.focus()
      event.preventDefault()
    }
  }

  private handleEscapeKey(event: KeyboardEvent): void {
    // Close modals, dropdowns, etc.
    const openModals = document.querySelectorAll('[role="dialog"][aria-hidden="false"]')
    if (openModals.length > 0) {
      const lastModal = openModals[openModals.length - 1] as HTMLElement
      const closeButton = lastModal.querySelector('[aria-label="Close"]') as HTMLElement
      closeButton?.click()
    }
  }

  private handleActivation(event: KeyboardEvent): void {
    const target = event.target as HTMLElement
    
    // Handle custom interactive elements
    if (target.getAttribute('role') === 'button' && !target.hasAttribute('disabled')) {
      target.click()
      event.preventDefault()
    }
  }

  private handleArrowNavigation(event: KeyboardEvent): void {
    const target = event.target as HTMLElement
    const parent = target.closest('[role="tablist"], [role="menu"], [role="listbox"]')
    
    if (parent) {
      const items = Array.from(parent.querySelectorAll('[role="tab"], [role="menuitem"], [role="option"]')) as HTMLElement[]
      const currentIndex = items.indexOf(target)
      
      if (currentIndex === -1) return
      
      let nextIndex = currentIndex
      
      switch (event.key) {
        case 'ArrowUp':
        case 'ArrowLeft':
          nextIndex = currentIndex > 0 ? currentIndex - 1 : items.length - 1
          break
        case 'ArrowDown':
        case 'ArrowRight':
          nextIndex = currentIndex < items.length - 1 ? currentIndex + 1 : 0
          break
      }
      
      items[nextIndex]?.focus()
      event.preventDefault()
    }
  }

  private updateFocusableElements(): void {
    const focusableSelectors = [
      'a[href]',
      'button:not([disabled])',
      'input:not([disabled])',
      'select:not([disabled])',
      'textarea:not([disabled])',
      '[tabindex]:not([tabindex="-1"])',
      '[role="button"]:not([disabled])',
      '[role="tab"]',
      '[role="menuitem"]'
    ].join(', ')

    this.focusableElements = Array.from(
      document.querySelectorAll(focusableSelectors)
    ).filter(el => {
      const element = el as HTMLElement
      return this.isVisible(element) && !element.hasAttribute('aria-hidden')
    }) as HTMLElement[]
  }

  private isVisible(element: HTMLElement): boolean {
    const style = window.getComputedStyle(element)
    return style.display !== 'none' && 
           style.visibility !== 'hidden' && 
           style.opacity !== '0'
  }

  private setupFocusManagement(): void {
    // Track focus for better UX
    document.addEventListener('focusin', (event) => {
      this.currentFocusedElement = event.target as HTMLElement
    })

    // Restore focus when appropriate
    document.addEventListener('focusout', (event) => {
      // Focus management logic
    })
  }

  private addARIALabels(): void {
    // Add missing ARIA labels to interactive elements
    const unlabeledButtons = document.querySelectorAll('button:not([aria-label]):not([aria-labelledby])')
    unlabeledButtons.forEach((button, index) => {
      const buttonElement = button as HTMLElement
      const text = buttonElement.textContent?.trim()
      if (!text) {
        buttonElement.setAttribute('aria-label', `Button ${index + 1}`)
      }
    })

    // Add ARIA labels to task cards
    const taskCards = document.querySelectorAll('.task-card')
    taskCards.forEach((card) => {
      const cardElement = card as HTMLElement
      const title = cardElement.querySelector('.task-title')?.textContent
      if (title && !cardElement.hasAttribute('aria-label')) {
        cardElement.setAttribute('aria-label', `Task: ${title}`)
        cardElement.setAttribute('role', 'article')
      }
    })
  }

  // High contrast mode support
  enableHighContrast(): void {
    document.body.classList.add('high-contrast')
  }

  disableHighContrast(): void {
    document.body.classList.remove('high-contrast')
  }

  // Screen reader announcements
  announce(message: string, priority: 'polite' | 'assertive' = 'polite'): void {
    const announcer = document.createElement('div')
    announcer.setAttribute('aria-live', priority)
    announcer.setAttribute('aria-atomic', 'true')
    announcer.classList.add('sr-only')
    announcer.textContent = message
    
    document.body.appendChild(announcer)
    
    // Remove after announcement
    setTimeout(() => {
      document.body.removeChild(announcer)
    }, 1000)
  }

  // Focus management for modals
  trapFocus(container: HTMLElement): () => void {
    const focusableElements = container.querySelectorAll(
      'a[href], button, textarea, input[type="text"], input[type="radio"], input[type="checkbox"], select'
    ) as NodeListOf<HTMLElement>
    
    const firstElement = focusableElements[0]
    const lastElement = focusableElements[focusableElements.length - 1]

    const handleTabKey = (event: KeyboardEvent) => {
      if (event.key === 'Tab') {
        if (event.shiftKey) {
          if (document.activeElement === firstElement) {
            lastElement.focus()
            event.preventDefault()
          }
        } else {
          if (document.activeElement === lastElement) {
            firstElement.focus()
            event.preventDefault()
          }
        }
      }
    }

    container.addEventListener('keydown', handleTabKey)
    firstElement?.focus()

    // Return cleanup function
    return () => {
      container.removeEventListener('keydown', handleTabKey)
    }
  }
}

// Global accessibility manager
export const accessibilityManager = AccessibilityManager.getInstance()

// CSS class for screen reader only content
export const srOnlyStyles = `
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.high-contrast {
  filter: contrast(150%) brightness(150%);
}

.high-contrast .task-card {
  border: 2px solid #000 !important;
  background: #fff !important;
  color: #000 !important;
}

.high-contrast .task-card.selected {
  border-color: #0066cc !important;
  background: #e6f3ff !important;
}
`