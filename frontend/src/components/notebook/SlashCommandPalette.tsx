import { useEffect, useRef } from 'react'
import type { SlashCommand } from '@/types/note'

const SLASH_COMMANDS: SlashCommand[] = [
  { command: '/h1', label: 'Heading 1', description: 'Large section heading', prefix: '# ', blockType: 'h1' },
  { command: '/h2', label: 'Heading 2', description: 'Medium section heading', prefix: '## ', blockType: 'h2' },
  { command: '/h3', label: 'Heading 3', description: 'Small section heading', prefix: '### ', blockType: 'h3' },
  { command: '/code', label: 'Code Block', description: 'Code snippet with syntax highlighting', prefix: '```\n\n```', blockType: 'code' },
  { command: '/bullet', label: 'Bullet List', description: 'Unordered list item', prefix: '- ', blockType: 'bullet' },
  { command: '/numbered', label: 'Numbered List', description: 'Ordered list item', prefix: '1. ', blockType: 'numbered' },
  { command: '/quote', label: 'Quote', description: 'Blockquote', prefix: '> ', blockType: 'quote' },
  { command: '/divider', label: 'Divider', description: 'Horizontal rule', prefix: '\n---\n', blockType: 'divider' },
]

interface SlashCommandPaletteProps {
  query: string
  position: { top: number; left: number }
  onSelect: (command: SlashCommand) => void
  onClose: () => void
  selectedIndex: number
  onSelectedIndexChange: (index: number) => void
}

export function SlashCommandPalette({
  query,
  position,
  onSelect,
  onClose,
  selectedIndex,
  onSelectedIndexChange,
}: SlashCommandPaletteProps) {
  const filtered = SLASH_COMMANDS.filter(
    (cmd) =>
      cmd.command.slice(1).startsWith(query.toLowerCase()) ||
      cmd.label.toLowerCase().includes(query.toLowerCase())
  )

  const listRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (filtered.length === 0) {
      onClose()
    }
  }, [filtered.length, onClose])

  if (filtered.length === 0) return null

  return (
    <div
      ref={listRef}
      className="fixed z-50 w-64 rounded-lg border border-border bg-card shadow-xl overflow-hidden"
      style={{ top: position.top, left: position.left }}
    >
      <div className="px-2 py-1.5 text-xs text-muted-foreground border-b border-border">
        Slash Commands
      </div>
      {filtered.map((cmd, idx) => (
        <button
          key={cmd.command}
          className={`w-full flex items-start gap-3 px-3 py-2 text-left transition-colors ${
            idx === selectedIndex
              ? 'bg-primary/10 text-primary'
              : 'text-foreground hover:bg-accent'
          }`}
          onMouseDown={(e) => {
            e.preventDefault() // prevent textarea blur
            onSelect(cmd)
          }}
          onMouseEnter={() => onSelectedIndexChange(idx)}
        >
          <span className="text-sm font-mono text-muted-foreground w-16 flex-shrink-0">
            {cmd.command}
          </span>
          <span className="flex flex-col min-w-0">
            <span className="text-sm font-medium">{cmd.label}</span>
            <span className="text-xs text-muted-foreground">{cmd.description}</span>
          </span>
        </button>
      ))}
    </div>
  )
}

export { SLASH_COMMANDS }
