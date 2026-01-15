import { useState, useRef, useEffect, KeyboardEvent, useCallback } from 'react'
import { Check, X, Pencil } from 'lucide-react'

type FieldType = 'text' | 'number' | 'percentage' | 'date' | 'textarea'

// Editable Slider Component for percentage values
interface EditableSliderProps {
  value: number // Value as decimal (0.10 = 10%)
  fieldPath: string
  onSave: (fieldPath: string, newValue: number) => Promise<void>
  min?: number // Min percentage (e.g., 1 for 1%)
  max?: number // Max percentage (e.g., 50 for 50%)
  step?: number // Step in percentage (e.g., 1 for 1%)
  label: string
  sourceText?: string
  disabled?: boolean
}

export function EditableSlider({
  value,
  fieldPath,
  onSave,
  min = 1,
  max = 50,
  step = 1,
  label,
  sourceText,
  disabled = false,
}: EditableSliderProps) {
  const [sliderValue, setSliderValue] = useState(Math.round(value * 100))
  const [isSaving, setIsSaving] = useState(false)
  const [isDragging, setIsDragging] = useState(false)
  const saveTimeoutRef = useRef<NodeJS.Timeout | null>(null)

  // Sync with prop changes
  useEffect(() => {
    if (!isDragging) {
      setSliderValue(Math.round(value * 100))
    }
  }, [value, isDragging])

  const handleSave = useCallback(async (newValue: number) => {
    if (disabled) return
    setIsSaving(true)
    try {
      await onSave(fieldPath, newValue / 100) // Convert back to decimal
    } catch (error) {
      console.error('Failed to save:', error)
      // Revert to original value on error
      setSliderValue(Math.round(value * 100))
    } finally {
      setIsSaving(false)
    }
  }, [disabled, fieldPath, onSave, value])

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = parseInt(e.target.value, 10)
    setSliderValue(newValue)

    // Debounce save - save 500ms after user stops dragging
    if (saveTimeoutRef.current) {
      clearTimeout(saveTimeoutRef.current)
    }
    saveTimeoutRef.current = setTimeout(() => {
      handleSave(newValue)
    }, 500)
  }

  const handleMouseDown = () => {
    setIsDragging(true)
  }

  const handleMouseUp = () => {
    setIsDragging(false)
    // Clear any pending timeout and save immediately
    if (saveTimeoutRef.current) {
      clearTimeout(saveTimeoutRef.current)
    }
    handleSave(sliderValue)
  }

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current)
      }
    }
  }, [])

  const percentage = sliderValue
  const isCritical = percentage >= 10

  return (
    <div className="p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-1.5">
          <span className="text-sm text-gray-700">{label}</span>
          {sourceText && (
            <span className="group relative cursor-help">
              <svg className="w-3.5 h-3.5 text-gray-400 hover:text-gray-600 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span className="absolute bottom-full left-0 mb-2 px-3 py-2 text-xs bg-white text-gray-700 border border-gray-200 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity w-72 pointer-events-none z-50 leading-relaxed shadow-lg">
                <span className="font-medium text-gray-900">Source: </span>{sourceText}
              </span>
            </span>
          )}
        </div>
        <span className={`text-sm font-semibold tabular-nums ${isCritical ? 'text-gray-900' : 'text-gray-600'}`}>
          {percentage}%
          {isSaving && <span className="ml-1 text-xs text-gray-400">saving...</span>}
        </span>
      </div>
      <div className="flex items-center gap-3">
        <span className="text-xs text-gray-400 w-6">{min}%</span>
        <input
          type="range"
          min={min}
          max={max}
          step={step}
          value={sliderValue}
          onChange={handleChange}
          onMouseDown={handleMouseDown}
          onMouseUp={handleMouseUp}
          onTouchStart={handleMouseDown}
          onTouchEnd={handleMouseUp}
          disabled={disabled || isSaving}
          className={`
            flex-1 h-2 rounded-full appearance-none cursor-pointer
            bg-gray-200
            [&::-webkit-slider-thumb]:appearance-none
            [&::-webkit-slider-thumb]:w-4
            [&::-webkit-slider-thumb]:h-4
            [&::-webkit-slider-thumb]:rounded-full
            [&::-webkit-slider-thumb]:bg-gray-800
            [&::-webkit-slider-thumb]:cursor-pointer
            [&::-webkit-slider-thumb]:shadow-md
            [&::-webkit-slider-thumb]:transition-transform
            [&::-webkit-slider-thumb]:hover:scale-110
            [&::-moz-range-thumb]:w-4
            [&::-moz-range-thumb]:h-4
            [&::-moz-range-thumb]:rounded-full
            [&::-moz-range-thumb]:bg-gray-800
            [&::-moz-range-thumb]:border-0
            [&::-moz-range-thumb]:cursor-pointer
            ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
          `}
          style={{
            background: `linear-gradient(to right, ${isCritical ? '#1f2937' : '#9ca3af'} 0%, ${isCritical ? '#1f2937' : '#9ca3af'} ${((sliderValue - min) / (max - min)) * 100}%, #e5e7eb ${((sliderValue - min) / (max - min)) * 100}%, #e5e7eb 100%)`
          }}
        />
        <span className="text-xs text-gray-400 w-6">{max}%</span>
      </div>
    </div>
  )
}

interface EditableFieldProps {
  value: string | number
  fieldPath: string
  type?: FieldType
  className?: string
  displayClassName?: string
  onSave: (fieldPath: string, newValue: string | number) => Promise<void>
  formatter?: (value: string | number) => string
  disabled?: boolean
}

export function EditableField({
  value,
  fieldPath,
  type = 'text',
  className = '',
  displayClassName = '',
  onSave,
  formatter,
  disabled = false,
}: EditableFieldProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [editValue, setEditValue] = useState(String(value))
  const [isSaving, setIsSaving] = useState(false)
  const inputRef = useRef<HTMLInputElement | HTMLTextAreaElement>(null)

  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus()
      inputRef.current.select()
    }
  }, [isEditing])

  useEffect(() => {
    setEditValue(String(value))
  }, [value])

  const handleDoubleClick = () => {
    if (disabled) return
    setIsEditing(true)
    // For percentage type, strip the % for editing
    if (type === 'percentage' && typeof value === 'number') {
      setEditValue(String(value * 100))
    } else {
      setEditValue(String(value))
    }
  }

  const handleSave = async () => {
    setIsSaving(true)
    try {
      let finalValue: string | number = editValue

      if (type === 'number') {
        finalValue = parseFloat(editValue) || 0
      } else if (type === 'percentage') {
        // Convert back to decimal
        finalValue = (parseFloat(editValue) || 0) / 100
      }

      await onSave(fieldPath, finalValue)
      setIsEditing(false)
    } catch (error) {
      console.error('Failed to save:', error)
    } finally {
      setIsSaving(false)
    }
  }

  const handleCancel = () => {
    setIsEditing(false)
    setEditValue(String(value))
  }

  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === 'Enter' && type !== 'textarea') {
      e.preventDefault()
      handleSave()
    } else if (e.key === 'Escape') {
      handleCancel()
    }
  }

  const displayValue = formatter ? formatter(value) : String(value)

  if (isEditing) {
    const inputClasses = `
      px-2 py-1 text-sm border border-blue-400 rounded-md
      focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
      bg-white shadow-sm
      ${type === 'textarea' ? 'min-h-[60px] resize-y' : ''}
      ${className}
    `

    return (
      <div className="inline-flex items-center gap-1">
        {type === 'textarea' ? (
          <textarea
            ref={inputRef as React.RefObject<HTMLTextAreaElement>}
            value={editValue}
            onChange={(e) => setEditValue(e.target.value)}
            onKeyDown={handleKeyDown}
            onBlur={() => setTimeout(handleCancel, 150)}
            className={inputClasses}
            disabled={isSaving}
          />
        ) : (
          <input
            ref={inputRef as React.RefObject<HTMLInputElement>}
            type={type === 'number' || type === 'percentage' ? 'number' : 'text'}
            value={editValue}
            onChange={(e) => setEditValue(e.target.value)}
            onKeyDown={handleKeyDown}
            className={inputClasses}
            disabled={isSaving}
            step={type === 'percentage' ? '1' : type === 'number' ? 'any' : undefined}
          />
        )}
        <button
          onClick={handleSave}
          disabled={isSaving}
          className="p-1 text-green-600 hover:bg-green-50 rounded transition-colors"
          title="Save (Enter)"
        >
          <Check className="w-3.5 h-3.5" />
        </button>
        <button
          onClick={handleCancel}
          disabled={isSaving}
          className="p-1 text-gray-400 hover:bg-gray-100 rounded transition-colors"
          title="Cancel (Esc)"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      </div>
    )
  }

  return (
    <span
      onDoubleClick={handleDoubleClick}
      className={`
        group inline-flex items-center gap-1 cursor-pointer
        hover:bg-blue-50 hover:text-blue-700 rounded px-1 -mx-1
        transition-colors duration-150
        ${disabled ? 'cursor-not-allowed opacity-60' : ''}
        ${displayClassName}
      `}
      title={disabled ? 'Read-only field' : 'Double-click to edit'}
    >
      {displayValue}
      {!disabled && (
        <Pencil className="w-3 h-3 text-gray-300 opacity-0 group-hover:opacity-100 transition-opacity" />
      )}
    </span>
  )
}

interface EditableListProps {
  items: string[]
  fieldPath: string
  onSave: (fieldPath: string, newValue: string[]) => Promise<void>
  itemClassName?: string
  disabled?: boolean
}

export function EditableList({
  items,
  fieldPath,
  onSave,
  itemClassName = '',
  disabled = false,
}: EditableListProps) {
  const [editingIndex, setEditingIndex] = useState<number | null>(null)
  const [editValue, setEditValue] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (editingIndex !== null && inputRef.current) {
      inputRef.current.focus()
      inputRef.current.select()
    }
  }, [editingIndex])

  const handleDoubleClick = (index: number) => {
    if (disabled) return
    setEditingIndex(index)
    setEditValue(items[index])
  }

  const handleSave = async () => {
    if (editingIndex === null) return

    const newItems = [...items]
    newItems[editingIndex] = editValue

    try {
      await onSave(fieldPath, newItems)
    } catch (error) {
      console.error('Failed to save:', error)
    }
    setEditingIndex(null)
  }

  const handleCancel = () => {
    setEditingIndex(null)
    setEditValue('')
  }

  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      handleSave()
    } else if (e.key === 'Escape') {
      handleCancel()
    }
  }

  return (
    <>
      {items.map((item, idx) => (
        editingIndex === idx ? (
          <div key={idx} className="inline-flex items-center gap-1">
            <input
              ref={inputRef}
              type="text"
              value={editValue}
              onChange={(e) => setEditValue(e.target.value)}
              onKeyDown={handleKeyDown}
              onBlur={() => setTimeout(handleCancel, 150)}
              className="px-2 py-0.5 text-xs border border-blue-400 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button onClick={handleSave} className="p-0.5 text-green-600 hover:bg-green-50 rounded">
              <Check className="w-3 h-3" />
            </button>
            <button onClick={handleCancel} className="p-0.5 text-gray-400 hover:bg-gray-100 rounded">
              <X className="w-3 h-3" />
            </button>
          </div>
        ) : (
          <span
            key={idx}
            onDoubleClick={() => handleDoubleClick(idx)}
            className={`
              group cursor-pointer hover:bg-blue-50 hover:text-blue-700
              rounded transition-colors duration-150
              ${disabled ? 'cursor-not-allowed' : ''}
              ${itemClassName}
            `}
            title={disabled ? 'Read-only' : 'Double-click to edit'}
          >
            {item}
            {!disabled && (
              <Pencil className="w-2.5 h-2.5 ml-1 text-gray-300 opacity-0 group-hover:opacity-100 inline transition-opacity" />
            )}
          </span>
        )
      ))}
    </>
  )
}
