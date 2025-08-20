'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { 
  BookOpen, 
  Search, 
  Filter,
  FileText,
  Award,
  Users,
  Clock,
  ChevronRight,
  Brain,
  Database,
  Shield,
  Network,
  Cpu,
  Sparkles,
  Cloud,
  Building,
  Code,
  Settings,
  Crown,
  Zap,
  Lock
} from 'lucide-react'
import { CertificationResourceList } from './certification-resource-list'

// AWS Certification types based on the backend structure
const CERTIFICATIONS = [
  {
    id: 'general',
    name: 'General AWS Content',
    description: 'General AWS content and mixed materials',
    level: 'Mixed',
    color: 'bg-gray-100 text-gray-800',
    icon: BookOpen
  },
  {
    id: 'ccp',
    name: 'AWS Certified Cloud Practitioner',
    description: 'Entry-level certification covering basic AWS cloud concepts',
    level: 'Foundational',
    color: 'bg-green-100 text-green-800',
    icon: Cloud
  },
  {
    id: 'aip',
    name: 'AWS Certified AI Practitioner',
    description: 'AI and machine learning fundamentals on AWS',
    level: 'Foundational',
    color: 'bg-purple-100 text-purple-800',
    icon: Sparkles
  },
  {
    id: 'saa',
    name: 'AWS Certified Solutions Architect Associate',
    description: 'Designing distributed systems and architectures on AWS',
    level: 'Associate',
    color: 'bg-blue-100 text-blue-800',
    icon: Building
  },
  {
    id: 'dva',
    name: 'AWS Certified Developer Associate',
    description: 'Developing and maintaining applications on AWS',
    level: 'Associate',
    color: 'bg-blue-100 text-blue-800',
    icon: Code
  },
  {
    id: 'soa',
    name: 'AWS Certified SysOps Administrator Associate',
    description: 'Operating and managing systems on AWS',
    level: 'Associate',
    color: 'bg-blue-100 text-blue-800',
    icon: Settings
  },
  {
    id: 'mla',
    name: 'AWS Certified Machine Learning Engineer Associate',
    description: 'Implementing and maintaining ML solutions on AWS',
    level: 'Associate',
    color: 'bg-blue-100 text-blue-800',
    icon: Brain
  },
  {
    id: 'dea',
    name: 'AWS Certified Data Engineer Associate',
    description: 'Designing and implementing data solutions on AWS',
    level: 'Associate',
    color: 'bg-blue-100 text-blue-800',
    icon: Database
  },
  {
    id: 'dop',
    name: 'AWS Certified DevOps Engineer Professional',
    description: 'Advanced DevOps practices and automation on AWS',
    level: 'Professional',
    color: 'bg-red-100 text-red-800',
    icon: Zap
  },
  {
    id: 'sap',
    name: 'AWS Certified Solutions Architect Professional',
    description: 'Advanced architectural design and complex solutions on AWS',
    level: 'Professional',
    color: 'bg-red-100 text-red-800',
    icon: Crown
  },
  {
    id: 'mls',
    name: 'AWS Certified Machine Learning Specialty',
    description: 'Specialized machine learning implementations on AWS',
    level: 'Specialty',
    color: 'bg-yellow-100 text-yellow-800',
    icon: Cpu
  },
  {
    id: 'scs',
    name: 'AWS Certified Security Specialty',
    description: 'Specialized security implementations and best practices on AWS',
    level: 'Specialty',
    color: 'bg-yellow-100 text-yellow-800',
    icon: Shield
  },
  {
    id: 'ans',
    name: 'AWS Certified Advanced Networking Specialty',
    description: 'Advanced networking concepts and implementations on AWS',
    level: 'Specialty',
    color: 'bg-yellow-100 text-yellow-800',
    icon: Network
  }
]

export function ResourcesBrowser() {
  const [selectedCertification, setSelectedCertification] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [levelFilter, setLevelFilter] = useState<string>('all')

  const filteredCertifications = CERTIFICATIONS.filter(cert => {
    const matchesSearch = cert.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         cert.description.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesLevel = levelFilter === 'all' || cert.level === levelFilter
    return matchesSearch && matchesLevel
  })

  const levels = ['all', 'Foundational', 'Associate', 'Professional', 'Specialty', 'Mixed']

  if (selectedCertification) {
    const certification = CERTIFICATIONS.find(c => c.id === selectedCertification)
    return (
      <div className="space-y-6">
        <div className="flex items-center space-x-4">
          <Button
            variant="outline"
            onClick={() => setSelectedCertification(null)}
            className="flex items-center space-x-2"
          >
            <ChevronRight className="h-4 w-4 rotate-180" />
            <span>Back to Certifications</span>
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-secondary-900">{certification?.name}</h1>
            <p className="text-secondary-600">{certification?.description}</p>
          </div>
        </div>
        
        <CertificationResourceList certificationId={selectedCertification} />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-secondary-900">Resources</h1>
        <p className="text-secondary-600 mt-2">
          Browse AWS certification documentation and study materials organized by certification type
        </p>
      </div>

      {/* Search and Filter Controls */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-secondary-400" />
          <Input
            placeholder="Search certifications..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
        
        <div className="flex items-center space-x-2">
          <Filter className="h-4 w-4 text-secondary-500" />
          <select
            value={levelFilter}
            onChange={(e) => setLevelFilter(e.target.value)}
            className="px-3 py-2 border border-secondary-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          >
            {levels.map(level => (
              <option key={level} value={level}>
                {level === 'all' ? 'All Levels' : level}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Certification Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredCertifications.map((certification) => {
          const Icon = certification.icon
          return (
            <Card 
              key={certification.id}
              className="cursor-pointer hover:shadow-lg transition-shadow duration-200"
              onClick={() => setSelectedCertification(certification.id)}
            >
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="p-2 bg-primary-100 rounded-lg">
                      <Icon className="h-5 w-5 text-primary-600" />
                    </div>
                    <div className="flex-1">
                      <Badge className={certification.color} variant="secondary">
                        {certification.level}
                      </Badge>
                    </div>
                  </div>
                  <ChevronRight className="h-5 w-5 text-secondary-400" />
                </div>
                <CardTitle className="text-lg leading-tight">
                  {certification.name}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-secondary-600 text-sm leading-relaxed">
                  {certification.description}
                </p>
                
                <div className="mt-4 flex items-center justify-between text-xs text-secondary-500">
                  <span className="flex items-center space-x-1">
                    <BookOpen className="h-3 w-3" />
                    <span>Study Materials</span>
                  </span>
                  <span className="flex items-center space-x-1">
                    <FileText className="h-3 w-3" />
                    <span>Documentation</span>
                  </span>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {filteredCertifications.length === 0 && (
        <div className="text-center py-12">
          <BookOpen className="h-12 w-12 text-secondary-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-secondary-900 mb-2">No certifications found</h3>
          <p className="text-secondary-600">
            Try adjusting your search terms or filter criteria
          </p>
        </div>
      )}
    </div>
  )
}