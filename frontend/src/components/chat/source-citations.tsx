'use client'

interface SourceCitationsProps {
  sources: string[]
  mode?: 'rag' | 'enhanced'
}

export function SourceCitations({ sources, mode }: SourceCitationsProps) {
  if (!sources || sources.length === 0) return null

  // Separate curated content from Claude's knowledge
  const curatedSources = sources.filter(source => 
    !source.toLowerCase().includes('claude') && 
    !source.toLowerCase().includes('general knowledge')
  )
  
  const claudeSources = sources.filter(source => 
    source.toLowerCase().includes('claude') || 
    source.toLowerCase().includes('general knowledge')
  )

  return (
    <div className="text-xs space-y-2">
      {/* Curated content sources */}
      {curatedSources.length > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-md p-2">
          <div className="flex items-center gap-1 mb-1">
            <svg className="w-3 h-3 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zm0 4a1 1 0 011-1h12a1 1 0 011 1v6a1 1 0 01-1 1H4a1 1 0 01-1-1V8z" clipRule="evenodd" />
            </svg>
            <span className="font-medium text-blue-800">Curated Study Materials:</span>
          </div>
          <ul className="space-y-1">
            {curatedSources.map((source, index) => (
              <li key={index} className="text-blue-700 flex items-start gap-1">
                <span className="text-blue-400 mt-0.5">•</span>
                <span className="flex-1">{source}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Claude's knowledge sources (only in enhanced mode) */}
      {mode === 'enhanced' && claudeSources.length > 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded-md p-2">
          <div className="flex items-center gap-1 mb-1">
            <svg className="w-3 h-3 text-amber-600" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
            </svg>
            <span className="font-medium text-amber-800">Additional Context:</span>
          </div>
          <ul className="space-y-1">
            {claudeSources.map((source, index) => (
              <li key={index} className="text-amber-700 flex items-start gap-1">
                <span className="text-amber-400 mt-0.5">•</span>
                <span className="flex-1">{source}</span>
              </li>
            ))}
          </ul>
          <div className="mt-1 text-amber-600 text-xs italic">
            Note: Prioritize curated materials for certification preparation
          </div>
        </div>
      )}

      {/* Mode indicator when no specific sources */}
      {sources.length === 0 && mode && (
        <div className="text-secondary-500 italic">
          Response generated using {mode === 'rag' ? 'curated study materials' : 'enhanced mode with additional context'}
        </div>
      )}
    </div>
  )
}