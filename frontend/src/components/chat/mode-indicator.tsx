'use client'

interface ModeIndicatorProps {
  mode: 'rag' | 'enhanced'
}

export function ModeIndicator({ mode }: ModeIndicatorProps) {
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${
      mode === 'rag' 
        ? 'bg-blue-100 text-blue-800' 
        : 'bg-amber-100 text-amber-800'
    }`}>
      <div className={`w-1.5 h-1.5 rounded-full ${
        mode === 'rag' ? 'bg-blue-600' : 'bg-amber-600'
      }`} />
      {mode === 'rag' ? 'Curated' : 'Enhanced'}
    </span>
  )
}