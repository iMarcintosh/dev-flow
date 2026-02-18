import { useState } from 'react'
import { Clock } from 'lucide-react'

interface CronSelectorProps {
  value?: string
  onChange: (cron: string) => void
  className?: string
}

interface CronPreset {
  label: string
  value: string
  description: string
}

const CRON_PRESETS: CronPreset[] = [
  { label: 'Every Hour', value: '0 * * * *', description: 'Runs at the start of every hour' },
  { label: 'Daily at 9 AM', value: '0 9 * * *', description: 'Runs every day at 9:00 AM' },
  { label: 'Daily at 6 PM', value: '0 18 * * *', description: 'Runs every day at 6:00 PM' },
  { label: 'Weekly (Monday 9 AM)', value: '0 9 * * 1', description: 'Runs every Monday at 9:00 AM' },
  { label: 'Monthly (1st at 9 AM)', value: '0 9 1 * *', description: 'Runs on the 1st of each month at 9:00 AM' },
  { label: 'Weekdays at 9 AM', value: '0 9 * * 1-5', description: 'Runs Monday-Friday at 9:00 AM' },
]

export function CronSelector({ value = '', onChange, className = '' }: CronSelectorProps) {
  const [isCustom, setIsCustom] = useState(() => {
    return value !== '' && !CRON_PRESETS.some(preset => preset.value === value)
  })
  const [customValue, setCustomValue] = useState(value)

  const handlePresetChange = (presetValue: string) => {
    if (presetValue === 'custom') {
      setIsCustom(true)
      onChange(customValue)
    } else {
      setIsCustom(false)
      setCustomValue(presetValue)
      onChange(presetValue)
    }
  }

  const handleCustomChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value
    setCustomValue(newValue)
    onChange(newValue)
  }

  const selectedPreset = CRON_PRESETS.find(p => p.value === value)?.value || 'custom'

  return (
    <div className={`space-y-3 ${className}`}>
      {/* Preset Selector */}
      <div>
        <label className="block text-sm font-medium text-foreground mb-2">
          <Clock className="inline w-4 h-4 mr-1" />
          Schedule Preset
        </label>
        <select
          value={isCustom ? 'custom' : selectedPreset}
          onChange={(e) => handlePresetChange(e.target.value)}
          className="w-full px-3 py-2 bg-background border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
        >
          {CRON_PRESETS.map((preset) => (
            <option key={preset.value} value={preset.value}>
              {preset.label}
            </option>
          ))}
          <option value="custom">Custom...</option>
        </select>
        
        {!isCustom && selectedPreset !== 'custom' && (
          <p className="mt-1 text-xs text-muted-foreground">
            {CRON_PRESETS.find(p => p.value === selectedPreset)?.description}
          </p>
        )}
      </div>

      {/* Custom Input */}
      {isCustom && (
        <div>
          <label className="block text-sm font-medium text-foreground mb-2">
            Custom Cron Expression
          </label>
          <input
            type="text"
            value={customValue}
            onChange={handleCustomChange}
            placeholder="0 9 * * *"
            className="w-full px-3 py-2 bg-background border border-border rounded-lg text-foreground font-mono text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
          />
          <div className="mt-2 text-xs text-muted-foreground space-y-1">
            <p className="font-medium">Cron Format: minute hour day month weekday</p>
            <p className="font-mono">* * * * *</p>
            <p className="pl-2">│ │ │ │ └─ Weekday (0-6, 0=Sunday)</p>
            <p className="pl-2">│ │ │ └─── Month (1-12)</p>
            <p className="pl-2">│ │ └───── Day (1-31)</p>
            <p className="pl-2">│ └─────── Hour (0-23)</p>
            <p className="pl-2">└───────── Minute (0-59)</p>
          </div>
        </div>
      )}

      {/* Next Run Preview */}
      {value && (
        <div className="p-3 bg-primary/10 border border-primary/20 rounded-lg">
          <p className="text-sm text-foreground">
            <span className="font-medium">Schedule: </span>
            <span className="font-mono text-primary">{value}</span>
          </p>
          <p className="text-xs text-muted-foreground mt-1">
            Next run will be calculated by the server
          </p>
        </div>
      )}
    </div>
  )
}
