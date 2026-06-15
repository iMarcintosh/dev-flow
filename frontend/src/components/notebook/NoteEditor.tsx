import { useState, useRef, useEffect, useCallback } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { Pin, Tag, Eye, EyeOff, Trash2, Loader2, Check } from 'lucide-react'
import { useDebounce } from '@/hooks/useDebounce'
import { useUpdateNote, useDeleteNote } from '@/services/noteQueries'
import { SlashCommandPalette, SLASH_COMMANDS } from './SlashCommandPalette'
import { TagEditor } from './TagEditor'
import type { Note, SlashCommand } from '@/types/note'

interface NoteEditorProps {
  note: Note
  onDeleted: () => void
}

type SaveState = 'saved' | 'saving' | 'unsaved'

export function NoteEditor({ note, onDeleted }: NoteEditorProps) {
  const [title, setTitle] = useState(note.title)
  const [content, setContent] = useState(note.content)
  const [tags, setTags] = useState<string[]>(note.tags)
  const [isPinned, setIsPinned] = useState(note.is_pinned)
  const [showPreview, setShowPreview] = useState(false)
  const [showTagEditor, setShowTagEditor] = useState(false)
  const [saveState, setSaveState] = useState<SaveState>('saved')

  // Slash command palette state
  const [showPalette, setShowPalette] = useState(false)
  const [paletteQuery, setPaletteQuery] = useState('')
  const [palettePosition, setPalettePosition] = useState({ top: 0, left: 0 })
  const [paletteSelectedIndex, setPaletteSelectedIndex] = useState(0)
  const [slashStart, setSlashStart] = useState<number>(-1)

  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const updateNote = useUpdateNote()
  const deleteNote = useDeleteNote()

  const debouncedTitle = useDebounce(title, 1500)
  const debouncedContent = useDebounce(content, 1500)
  const debouncedTags = useDebounce(tags, 1500)

  // Auto-save when debounced values change (but not on initial mount)
  const isFirstRender = useRef(true)
  useEffect(() => {
    if (isFirstRender.current) {
      isFirstRender.current = false
      return
    }
    setSaveState('saving')
    updateNote.mutate(
      {
        id: note.id,
        data: { title: debouncedTitle, content: debouncedContent, tags: debouncedTags },
      },
      {
        onSuccess: () => setSaveState('saved'),
        onError: () => setSaveState('unsaved'),
      }
    )
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debouncedTitle, debouncedContent, debouncedTags])

  // Auto-resize textarea to content height
  useEffect(() => {
    if (textareaRef.current && !showPreview) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`
    }
  }, [content, showPreview])

  // Mark as unsaved when user types
  const handleTitleChange = (value: string) => {
    setTitle(value)
    setSaveState('unsaved')
  }
  const handleContentChange = (value: string) => {
    setContent(value)
    setSaveState('unsaved')
  }
  const handleTagsChange = (newTags: string[]) => {
    setTags(newTags)
    setSaveState('unsaved')
  }

  const handlePinToggle = () => {
    const newPinned = !isPinned
    setIsPinned(newPinned)
    updateNote.mutate({ id: note.id, data: { is_pinned: newPinned } })
  }

  const handleDelete = async () => {
    if (!confirm('Delete this note? This cannot be undone.')) return
    await deleteNote.mutateAsync(note.id)
    onDeleted()
  }

  // Slash command detection
  const handleTextareaKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (showPalette) {
        if (e.key === 'ArrowDown') {
          e.preventDefault()
          const filtered = SLASH_COMMANDS.filter(
            (cmd) =>
              cmd.command.slice(1).startsWith(paletteQuery.toLowerCase()) ||
              cmd.label.toLowerCase().includes(paletteQuery.toLowerCase())
          )
          setPaletteSelectedIndex((i) => Math.min(i + 1, filtered.length - 1))
          return
        }
        if (e.key === 'ArrowUp') {
          e.preventDefault()
          setPaletteSelectedIndex((i) => Math.max(i - 1, 0))
          return
        }
        if (e.key === 'Enter') {
          e.preventDefault()
          const filtered = SLASH_COMMANDS.filter(
            (cmd) =>
              cmd.command.slice(1).startsWith(paletteQuery.toLowerCase()) ||
              cmd.label.toLowerCase().includes(paletteQuery.toLowerCase())
          )
          if (filtered[paletteSelectedIndex]) {
            insertSlashCommand(filtered[paletteSelectedIndex])
          }
          return
        }
        if (e.key === 'Escape') {
          e.preventDefault()
          setShowPalette(false)
          return
        }
      }

      // Bullet/numbered list continuation on Enter
      if (e.key === 'Enter' && !showPalette) {
        const textarea = e.currentTarget
        const cursorPos = textarea.selectionStart
        const textBeforeCursor = content.slice(0, cursorPos)
        const lastNewline = textBeforeCursor.lastIndexOf('\n')
        const currentLine = textBeforeCursor.slice(lastNewline + 1)

        const bulletMatch = currentLine.match(/^(- )(.*)$/)
        const numberedMatch = currentLine.match(/^(\d+)\. (.*)$/)

        if (bulletMatch) {
          e.preventDefault()
          if (bulletMatch[2] === '') {
            // Empty bullet — end the list
            const newContent = content.slice(0, lastNewline + 1) + content.slice(cursorPos)
            setContent(newContent)
            setSaveState('unsaved')
            requestAnimationFrame(() => {
              if (textareaRef.current) {
                textareaRef.current.setSelectionRange(lastNewline + 1, lastNewline + 1)
              }
            })
          } else {
            // Continue bullet list
            const insert = '\n- '
            const newContent = content.slice(0, cursorPos) + insert + content.slice(cursorPos)
            setContent(newContent)
            setSaveState('unsaved')
            const newCursor = cursorPos + insert.length
            requestAnimationFrame(() => {
              if (textareaRef.current) {
                textareaRef.current.setSelectionRange(newCursor, newCursor)
              }
            })
          }
          return
        }

        if (numberedMatch) {
          e.preventDefault()
          const num = parseInt(numberedMatch[1], 10)
          if (numberedMatch[2] === '') {
            // Empty numbered item — end the list
            const newContent = content.slice(0, lastNewline + 1) + content.slice(cursorPos)
            setContent(newContent)
            setSaveState('unsaved')
            requestAnimationFrame(() => {
              if (textareaRef.current) {
                textareaRef.current.setSelectionRange(lastNewline + 1, lastNewline + 1)
              }
            })
          } else {
            // Continue numbered list
            const insert = `\n${num + 1}. `
            const newContent = content.slice(0, cursorPos) + insert + content.slice(cursorPos)
            setContent(newContent)
            setSaveState('unsaved')
            const newCursor = cursorPos + insert.length
            requestAnimationFrame(() => {
              if (textareaRef.current) {
                textareaRef.current.setSelectionRange(newCursor, newCursor)
              }
            })
          }
          return
        }
      }
    },
    [showPalette, paletteQuery, paletteSelectedIndex, content]
  )

  const handleTextareaChange = useCallback(
    (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      const value = e.target.value
      handleContentChange(value)

      const textarea = e.target
      const cursorPos = textarea.selectionStart
      const textBeforeCursor = value.slice(0, cursorPos)
      const lastNewline = textBeforeCursor.lastIndexOf('\n')
      const currentLine = textBeforeCursor.slice(lastNewline + 1)

      // Detect slash at start of line
      const slashMatch = currentLine.match(/^\/(\w*)$/)
      if (slashMatch) {
        const query = slashMatch[1]
        const slashPos = cursorPos - currentLine.length
        setSlashStart(slashPos)
        setPaletteQuery(query)
        setPaletteSelectedIndex(0)

        // Calculate position from textarea
        if (textareaRef.current) {
          const rect = textareaRef.current.getBoundingClientRect()
          // Approximate position (line height ~20px, char width ~8px)
          const lineNumber = textBeforeCursor.split('\n').length - 1
          setPalettePosition({
            top: rect.top + lineNumber * 20 + 24,
            left: rect.left + (lastNewline === -1 ? 0 : 0),
          })
        }
        setShowPalette(true)
      } else {
        setShowPalette(false)
        setSlashStart(-1)
      }
    },
    [handleContentChange]
  )

  const insertSlashCommand = useCallback(
    (command: SlashCommand) => {
      if (!textareaRef.current || slashStart === -1) return
      const textarea = textareaRef.current
      const cursorPos = textarea.selectionStart
      const before = content.slice(0, slashStart)
      const after = content.slice(cursorPos)

      let newContent: string
      let newCursorPos: number

      if (command.blockType === 'code') {
        newContent = before + '```\n\n```' + after
        newCursorPos = slashStart + 4 // place cursor between the ticks
      } else if (command.blockType === 'divider') {
        newContent = before + '\n---\n' + after
        newCursorPos = slashStart + 5
      } else {
        newContent = before + command.prefix + after
        newCursorPos = slashStart + command.prefix.length
      }

      setContent(newContent)
      setSaveState('unsaved')
      setShowPalette(false)
      setSlashStart(-1)

      // Restore focus and cursor
      requestAnimationFrame(() => {
        if (textareaRef.current) {
          textareaRef.current.focus()
          textareaRef.current.setSelectionRange(newCursorPos, newCursorPos)
        }
      })
    },
    [content, slashStart]
  )

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    })
  }

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <div className="flex items-center gap-2 px-4 py-2 border-b border-border flex-shrink-0">
        <button
          onClick={handlePinToggle}
          title={isPinned ? 'Unpin note' : 'Pin note'}
          className={`p-1.5 rounded-md transition-colors ${
            isPinned
              ? 'text-amber-400 bg-amber-400/10'
              : 'text-muted-foreground hover:text-foreground hover:bg-accent'
          }`}
        >
          <Pin className="w-4 h-4" />
        </button>
        <button
          onClick={() => setShowTagEditor(!showTagEditor)}
          title="Edit tags"
          className={`p-1.5 rounded-md transition-colors ${
            showTagEditor
              ? 'text-primary bg-primary/10'
              : 'text-muted-foreground hover:text-foreground hover:bg-accent'
          }`}
        >
          <Tag className="w-4 h-4" />
        </button>
        <button
          onClick={() => setShowPreview(!showPreview)}
          title={showPreview ? 'Edit mode' : 'Preview mode'}
          className={`p-1.5 rounded-md transition-colors ${
            showPreview
              ? 'text-primary bg-primary/10'
              : 'text-muted-foreground hover:text-foreground hover:bg-accent'
          }`}
        >
          {showPreview ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
        </button>

        <div className="flex-1" />

        {/* Save indicator */}
        <div className="flex items-center gap-1.5 text-xs">
          {saveState === 'saving' && (
            <span className="flex items-center gap-1 text-muted-foreground">
              <Loader2 className="w-3 h-3 animate-spin" />
              Saving...
            </span>
          )}
          {saveState === 'saved' && (
            <span className="flex items-center gap-1 text-muted-foreground">
              <Check className="w-3 h-3" />
              Saved
            </span>
          )}
          {saveState === 'unsaved' && (
            <span className="text-amber-400 text-xs">Unsaved</span>
          )}
        </div>

        <span className="text-xs text-muted-foreground">{formatDate(note.updated_at)}</span>

        <button
          onClick={handleDelete}
          title="Delete note"
          className="p-1.5 rounded-md text-muted-foreground hover:text-red-400 hover:bg-red-400/10 transition-colors"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>

      {/* Tag Editor (collapsible) */}
      {showTagEditor && (
        <div className="px-4 py-2 border-b border-border">
          <TagEditor tags={tags} onChange={handleTagsChange} />
        </div>
      )}

      {/* Title */}
      <div className="px-6 pt-4 pb-2 flex-shrink-0">
        <input
          type="text"
          value={title}
          onChange={(e) => handleTitleChange(e.target.value)}
          placeholder="Untitled"
          className="w-full bg-transparent text-2xl font-semibold text-foreground placeholder:text-muted-foreground outline-none"
        />
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto px-6 pb-6 relative">
        {showPreview ? (
          <MarkdownPreview content={content} />
        ) : (
          <textarea
            ref={textareaRef}
            value={content}
            onChange={handleTextareaChange}
            onKeyDown={handleTextareaKeyDown}
            placeholder="Start writing... Type / for commands"
            className="w-full min-h-[200px] bg-transparent text-sm text-foreground placeholder:text-muted-foreground outline-none resize-none font-mono leading-relaxed"
          />
        )}
      </div>

      {/* Slash Command Palette */}
      {showPalette && (
        <SlashCommandPalette
          query={paletteQuery}
          position={palettePosition}
          onSelect={insertSlashCommand}
          onClose={() => setShowPalette(false)}
          selectedIndex={paletteSelectedIndex}
          onSelectedIndexChange={setPaletteSelectedIndex}
        />
      )}
    </div>
  )
}

function MarkdownPreview({ content }: { content: string }) {
  return (
    <div className="prose prose-invert prose-sm max-w-none">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          code({ node, inline, className, children, ...props }: any) {
            const match = /language-(\w+)/.exec(className || '')
            const language = match ? match[1] : ''
            const codeString = String(children).replace(/\n$/, '')
            return !inline && language ? (
              <div className="my-3 rounded-lg overflow-hidden border border-border">
                <div className="flex items-center px-4 py-2 bg-muted border-b border-border">
                  <span className="text-xs font-medium text-muted-foreground uppercase">{language}</span>
                </div>
                <SyntaxHighlighter
                  language={language}
                  style={vscDarkPlus}
                  showLineNumbers
                  customStyle={{ margin: 0, borderRadius: 0, fontSize: '0.8125rem', padding: '1rem' }}
                >
                  {codeString}
                </SyntaxHighlighter>
              </div>
            ) : (
              <code className="px-1.5 py-0.5 rounded bg-muted text-sm font-mono" {...props}>
                {children}
              </code>
            )
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  )
}
