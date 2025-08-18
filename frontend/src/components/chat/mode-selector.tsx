'use client'

interface ModeSelectorProps {
  currentMode: 'rag' | 'enhanced'
  onModeChange: (mode: 'rag' | 'enhanced') => void
}

export function ModeSelector({ currentMode, onModeChange }: ModeSelectorProps) {
  return (
    <div>
      <label className="block text-sm font-medium text-secondary-700 mb-1">
        Response Mode
      </label>
      <div className="flex rounded-lg border border-secondary-300 overflow-hidden">
        <button
          onClick={() => onModeChange('rag')}
          className={`flex-1 px-4 py-2 text-sm font-medium transition-colors ${
            currentMode === 'rag'
              ? 'bg-blue-600 text-white'
              : 'bg-white text-secondary-700 hover:bg-secondary-50'
          }`}
        >
          <div className="flex items-center justify-center gap-2">
            <div className={`w-2 h-2 rounded-full ${
              currentMode === 'rag' ? 'bg-blue-200' : 'bg-blue-600'
            }`} />
            Curated Only
          </div>
        </button>
        
        <button
          onClick={() => onModeChange('enhanced')}
          className={`flex-1 px-4 py-2 text-sm font-medium transition-colors ${
            currentMode === 'enhanced'
              ? 'bg-amber-600 text-white'
              : 'bg-white text-secondary-700 hover:bg-secondary-50'
          }`}
        >
          <div className="flex items-center justify-center gap-2">
            <div className={`w-2 h-2 rounded-full ${
              currentMode === 'enhanced' ? 'bg-amber-200' : 'bg-amber-600'
            }`} />
            Enhanced
          </div>
        </button>
      </div>
      
      <div className="mt-1 text-xs text-secondary-600">
        {currentMode === 'rag' 
          ? 'Uses only curated study materials'
          : 'Includes additional AWS knowledge when needed'
        }
      </div>
    </div>
  )
}