import { render, screen } from '@testing-library/react'
import { SourceCitations } from '../source-citations'

describe('SourceCitations', () => {
  it('renders nothing when no sources provided', () => {
    const { container } = render(<SourceCitations sources={[]} />)
    expect(container.firstChild).toBeNull()
  })

  it('displays curated sources correctly', () => {
    const sources = ['AWS Documentation', 'Study Guide Chapter 5', 'Practice Exam Questions']
    
    render(<SourceCitations sources={sources} mode="rag" />)
    
    expect(screen.getByText('Curated Study Materials:')).toBeInTheDocument()
    expect(screen.getByText('AWS Documentation')).toBeInTheDocument()
    expect(screen.getByText('Study Guide Chapter 5')).toBeInTheDocument()
    expect(screen.getByText('Practice Exam Questions')).toBeInTheDocument()
  })

  it('separates curated and Claude sources in enhanced mode', () => {
    const sources = [
      'AWS Documentation',
      'Claude General Knowledge',
      'Study Guide',
      'Claude AWS Knowledge Base'
    ]
    
    render(<SourceCitations sources={sources} mode="enhanced" />)
    
    expect(screen.getByText('Curated Study Materials:')).toBeInTheDocument()
    expect(screen.getByText('Additional Context:')).toBeInTheDocument()
    
    // Curated sources
    expect(screen.getByText('AWS Documentation')).toBeInTheDocument()
    expect(screen.getByText('Study Guide')).toBeInTheDocument()
    
    // Claude sources
    expect(screen.getByText('Claude General Knowledge')).toBeInTheDocument()
    expect(screen.getByText('Claude AWS Knowledge Base')).toBeInTheDocument()
  })

  it('shows priority note for enhanced mode', () => {
    const sources = ['AWS Documentation', 'Claude General Knowledge']
    
    render(<SourceCitations sources={sources} mode="enhanced" />)
    
    expect(screen.getByText('Note: Prioritize curated materials for certification preparation')).toBeInTheDocument()
  })

  it('only shows curated sources in RAG mode', () => {
    const sources = ['AWS Documentation', 'Claude General Knowledge']
    
    render(<SourceCitations sources={sources} mode="rag" />)
    
    expect(screen.getByText('Curated Study Materials:')).toBeInTheDocument()
    expect(screen.queryByText('Additional Context:')).not.toBeInTheDocument()
    expect(screen.getByText('AWS Documentation')).toBeInTheDocument()
    expect(screen.queryByText('Claude General Knowledge')).not.toBeInTheDocument()
  })

  it('handles empty sources array', () => {
    const { container } = render(<SourceCitations sources={[]} mode="rag" />)
    expect(container.firstChild).toBeNull()
  })

  it('handles undefined sources', () => {
    const { container } = render(<SourceCitations sources={undefined as any} mode="rag" />)
    expect(container.firstChild).toBeNull()
  })

  it('applies correct styling for curated sources', () => {
    const sources = ['AWS Documentation']
    
    render(<SourceCitations sources={sources} mode="rag" />)
    
    const curatedSection = screen.getByText('Curated Study Materials:').closest('.bg-blue-50')
    expect(curatedSection).toHaveClass('bg-blue-50', 'border-blue-200')
  })

  it('applies correct styling for Claude sources', () => {
    const sources = ['Claude General Knowledge']
    
    render(<SourceCitations sources={sources} mode="enhanced" />)
    
    const claudeSection = screen.getByText('Additional Context:').closest('.bg-amber-50')
    expect(claudeSection).toHaveClass('bg-amber-50', 'border-amber-200')
  })
})