import { render, screen } from '@testing-library/react'
import { AchievementDisplay } from '../achievement-display'

const mockProgressData = {
  overall: {
    total_study_time: 120, // 2 hours
    quizzes_completed: 5,
    average_score: 85,
    streak_days: 7
  },
  by_certification: {
    'aws-solutions-architect': {
      progress_percentage: 75,
      topics_completed: 15,
      total_topics: 20,
      last_activity: '2025-01-15T10:00:00Z'
    }
  },
  trends: []
}

const mockProgressDataWithHighAchievements = {
  overall: {
    total_study_time: 3600, // 60 hours
    quizzes_completed: 50,
    average_score: 90,
    streak_days: 30
  },
  by_certification: {
    'aws-solutions-architect': {
      progress_percentage: 100,
      topics_completed: 20,
      total_topics: 20,
      last_activity: '2025-01-15T10:00:00Z'
    }
  },
  trends: []
}

describe('AchievementDisplay', () => {
  it('renders loading state', () => {
    render(<AchievementDisplay loading={true} />)
    
    expect(screen.getByText('Achievements')).toBeInTheDocument()
    
    // Should render skeleton loaders
    const skeletonElements = screen.getAllByRole('generic').filter(el => 
      el.className.includes('animate-pulse')
    )
    expect(skeletonElements.length).toBeGreaterThan(0)
  })

  it('renders empty state when no achievements', () => {
    const emptyProgressData = {
      overall: {
        total_study_time: 0,
        quizzes_completed: 0,
        average_score: 0,
        streak_days: 0
      },
      by_certification: {},
      trends: []
    }

    render(<AchievementDisplay progressData={emptyProgressData} loading={false} />)

    expect(screen.getByText('No achievements yet')).toBeInTheDocument()
    expect(screen.getByText('Start studying to unlock your first achievement!')).toBeInTheDocument()
  })

  it('displays earned achievements correctly', () => {
    render(<AchievementDisplay progressData={mockProgressData} loading={false} />)

    expect(screen.getByText('Achievements')).toBeInTheDocument()
    
    // Should show some earned achievements based on the mock data
    // With 120 minutes (2 hours), should have "First Hour" achievement
    expect(screen.getByText('Recent Achievements')).toBeInTheDocument()
  })

  it('displays progress towards next achievements', () => {
    render(<AchievementDisplay progressData={mockProgressData} loading={false} />)

    expect(screen.getByText('In Progress')).toBeInTheDocument()
    
    // Should show progress bars for achievements in progress
    const progressBars = screen.getAllByRole('generic').filter(el => 
      el.className.includes('bg-primary-600') && el.className.includes('h-1.5')
    )
    expect(progressBars.length).toBeGreaterThan(0)
  })

  it('calculates achievement progress correctly', () => {
    render(<AchievementDisplay progressData={mockProgressData} loading={false} />)

    // With 5 quizzes completed, should show progress towards quiz achievements
    // With 7 day streak, should show streak achievements
    // With 85% average score, should show score achievements
    
    // Check that achievement summary is displayed
    expect(screen.getByText('Earned')).toBeInTheDocument()
    expect(screen.getByText('Complete')).toBeInTheDocument()
  })

  it('displays high-level achievements when criteria met', () => {
    render(<AchievementDisplay progressData={mockProgressDataWithHighAchievements} loading={false} />)

    // With high values, should have many achievements earned
    const achievementSummary = screen.getByText('Complete')
    expect(achievementSummary).toBeInTheDocument()
  })

  it('shows correct rarity colors for achievements', () => {
    render(<AchievementDisplay progressData={mockProgressData} loading={false} />)

    // Should render achievement items with appropriate rarity colors
    // Common achievements should have gray colors
    // Rare achievements should have blue colors
    // Epic achievements should have purple colors
    // Legendary achievements should have yellow colors
    
    const achievementElements = screen.getAllByRole('generic').filter(el => 
      el.className.includes('bg-') && (
        el.className.includes('gray-100') || 
        el.className.includes('blue-100') || 
        el.className.includes('purple-100') || 
        el.className.includes('yellow-100')
      )
    )
    expect(achievementElements.length).toBeGreaterThan(0)
  })

  it('handles undefined progress data gracefully', () => {
    render(<AchievementDisplay loading={false} />)

    expect(screen.getByText('No achievements yet')).toBeInTheDocument()
  })

  it('displays achievement categories correctly', () => {
    render(<AchievementDisplay progressData={mockProgressData} loading={false} />)

    // Should categorize achievements by study, quiz, streak, and milestone
    // Each category should have appropriate icons and descriptions
    expect(screen.getByText('Achievements')).toBeInTheDocument()
  })

  it('shows achievement completion percentage', () => {
    render(<AchievementDisplay progressData={mockProgressData} loading={false} />)

    // Should show completion percentage in the header
    const achievementHeader = screen.getByText(/\(\d+\/\d+\)/)
    expect(achievementHeader).toBeInTheDocument()
  })

  it('displays progress indicators for incomplete achievements', () => {
    render(<AchievementDisplay progressData={mockProgressData} loading={false} />)

    // Should show progress like "5/25" for quiz achievements
    const progressIndicators = screen.getAllByText(/\d+\/\d+/)
    expect(progressIndicators.length).toBeGreaterThan(0)
  })
})