import { useQuery, useMutation } from '@tanstack/react-query'
import { Loader2, Sparkles } from 'lucide-react'
import { templateService } from '@/services/custom-agents'

interface TemplateGridProps {
  onTemplateUsed: () => void
}

export function TemplateGrid({ onTemplateUsed }: TemplateGridProps) {
  const { data: templates = [], isLoading } = useQuery({
    queryKey: ['agent-templates'],
    queryFn: () => templateService.listTemplates(),
  })

  const createMutation = useMutation({
    mutationFn: (category: string) => templateService.createFromTemplate(category),
    onSuccess: () => {
      onTemplateUsed()
    },
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 text-primary animate-spin" />
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {templates.map((template) => (
        <div
          key={template.category}
          className="bg-card border border-border rounded-lg p-6 hover:border-primary/50 transition-all hover:shadow-lg"
        >
          {/* Header */}
          <div className="flex items-start gap-3 mb-4">
            <div className="text-4xl">{template.icon}</div>
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-foreground">{template.name}</h3>
              <p className="text-sm text-muted-foreground mt-1 line-clamp-3">
                {template.description}
              </p>
            </div>
          </div>

          {/* Model Info */}
          <div className="mb-4">
            <div className="flex items-center gap-2 text-xs text-muted-foreground mb-2">
              <span className="font-mono bg-background px-2 py-1 rounded">
                {template.model_name.split('-').slice(0, 2).join('-')}
              </span>
              <span>•</span>
              <span>Temp: {template.temperature}</span>
            </div>
          </div>

          {/* Tools */}
          {template.enabled_tools && template.enabled_tools.length > 0 && (
            <div className="mb-4">
              <div className="text-xs text-muted-foreground mb-2">Tools:</div>
              <div className="flex flex-wrap gap-1">
                {template.enabled_tools.map((tool) => (
                  <span
                    key={tool}
                    className="text-xs bg-primary/10 text-primary px-2 py-0.5 rounded"
                  >
                    {tool}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Use Template Button */}
          <button
            onClick={() => createMutation.mutate(template.category)}
            disabled={createMutation.isPending}
            className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50"
          >
            <Sparkles className="w-4 h-4" />
            {createMutation.isPending ? 'Creating...' : 'Use Template'}
          </button>
        </div>
      ))}

      {templates.length === 0 && (
        <div className="col-span-full text-center py-12 text-muted-foreground">
          No templates available
        </div>
      )}
    </div>
  )
}
