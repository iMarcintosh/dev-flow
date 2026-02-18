import { useState, useRef, useEffect } from 'react'
import { createPortal } from 'react-dom'
import { ChevronDown, Check } from 'lucide-react'

export interface SelectOption {
  value: string
  label: string
  description?: string
}

interface SelectProps {
  value: string
  onChange: (value: string) => void
  options: SelectOption[]
  label?: string
  placeholder?: string
  disabled?: boolean
  className?: string
  forceUpward?: boolean  // Force dropdown to open upward
}

export function Select({
  value,
  onChange,
  options,
  label,
  placeholder = 'Select an option...',
  disabled = false,
  className = '',
  forceUpward = false,
}: SelectProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [openUpward, setOpenUpward] = useState(forceUpward)
  const [dropdownPosition, setDropdownPosition] = useState({ top: 0, left: 0, width: 0 })
  const dropdownRef = useRef<HTMLDivElement>(null)
  const buttonRef = useRef<HTMLButtonElement>(null)

  const selectedOption = options.find((opt) => opt.value === value)

  // Calculate dropdown position
  useEffect(() => {
    if (isOpen && buttonRef.current) {
      const rect = buttonRef.current.getBoundingClientRect()
      setDropdownPosition({
        top: rect.top,
        left: rect.left,
        width: rect.width,
      })

      if (forceUpward) {
        setOpenUpward(true)
        return
      }
      
      const spaceBelow = window.innerHeight - rect.bottom
      const spaceAbove = rect.top
      const dropdownHeight = 320 // max-h-80 = 20rem = 320px
      
      // Open upward if not enough space below and more space above
      setOpenUpward(spaceBelow < dropdownHeight && spaceAbove > spaceBelow)
    }
  }, [isOpen, forceUpward])

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside)
      return () => document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [isOpen])

  // Keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (disabled) return

    switch (e.key) {
      case 'Enter':
      case ' ':
        e.preventDefault()
        setIsOpen(!isOpen)
        break
      case 'Escape':
        setIsOpen(false)
        break
    }
  }

  return (
    <div className={`relative ${className}`} ref={dropdownRef}>
      {label && (
        <label className="block text-sm font-medium text-foreground mb-2">
          {label}
        </label>
      )}

      {/* Trigger Button */}
      <button
        ref={buttonRef}
        type="button"
        onClick={() => !disabled && setIsOpen(!isOpen)}
        onKeyDown={handleKeyDown}
        disabled={disabled}
        className="w-full px-4 py-2 bg-background border border-border rounded-lg text-left flex items-center justify-between hover:border-border/80 transition-colors disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-primary/50"
      >
        <div className="flex-1 min-w-0">
          {selectedOption ? (
            <div>
              <div className="text-foreground font-medium truncate">
                {selectedOption.label}
              </div>
              {selectedOption.description && (
                <div className="text-xs text-muted-foreground mt-0.5 truncate">
                  {selectedOption.description}
                </div>
              )}
            </div>
          ) : (
            <div className="text-muted-foreground">{placeholder}</div>
          )}
        </div>
        <ChevronDown
          className={`w-5 h-5 text-muted-foreground ml-2 flex-shrink-0 transition-transform ${
            isOpen ? 'rotate-180' : ''
          }`}
        />
      </button>

      {/* Dropdown Menu - Rendered via Portal */}
      {isOpen && createPortal(
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-[998]"
            onClick={() => setIsOpen(false)}
          />

          {/* Options List - Portal ensures it renders above everything */}
          <div 
            ref={dropdownRef}
            className="fixed z-[999] bg-background border border-border rounded-lg shadow-xl max-h-80 overflow-y-auto"
            style={{
              left: `${dropdownPosition.left}px`,
              width: `${dropdownPosition.width}px`,
              ...(openUpward 
                ? { bottom: `${window.innerHeight - dropdownPosition.top + 8}px` }
                : { top: `${dropdownPosition.top + 48}px` }
              )
            }}
          >
            {options.map((option) => (
              <button
                key={option.value}
                type="button"
                onClick={() => {
                  onChange(option.value)
                  setIsOpen(false)
                }}
                className="w-full px-4 py-3 hover:bg-accent transition-colors text-left flex items-start gap-3 focus:outline-none focus:bg-accent"
              >
                {/* Checkmark */}
                <div className="flex-shrink-0 mt-0.5">
                  {value === option.value ? (
                    <Check className="w-4 h-4 text-primary" />
                  ) : (
                    <div className="w-4 h-4" />
                  )}
                </div>

                {/* Option Content */}
                <div className="flex-1 min-w-0">
                  <div className="text-foreground font-medium">{option.label}</div>
                  {option.description && (
                    <div className="text-xs text-muted-foreground mt-1">
                      {option.description}
                    </div>
                  )}
                </div>
              </button>
            ))}
          </div>
        </>,
        document.body
      )}
    </div>
  )
}
