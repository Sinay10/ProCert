'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { 
  FileText, 
  Download, 
  Search, 
  Calendar,
  Database,
  AlertCircle,
  Loader2,
  Eye,
  BookOpen
} from 'lucide-react'
import { useSession } from 'next-auth/react'
import { apiClient, API_ENDPOINTS } from '@/lib/api-client'

interface ResourceFile {
  key: string
  name: string
  size: number
  lastModified: string
  contentType: string
  url?: string
}

interface CertificationResourceListProps {
  certificationId: string
}

export function CertificationResourceList({ certificationId }: CertificationResourceListProps) {
  const { data: session } = useSession()
  const [resources, setResources] = useState<ResourceFile[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')

  useEffect(() => {
    fetchResources()
  }, [certificationId])

  const fetchResources = async () => {
    if (!session?.accessToken) {
      setError('Authentication required')
      setLoading(false)
      return
    }

    try {
      setLoading(true)
      setError(null)

      // Call the resources API endpoint
      const data = await apiClient.get<{
        certification: string
        bucket: string
        resources: ResourceFile[]
        total: number
      }>(API_ENDPOINTS.RESOURCES(certificationId))
      
      setResources(data.resources || [])
    } catch (err: any) {
      console.error('Error fetching resources:', err)
      if (err.response?.status === 404) {
        setError(`No resources found for ${certificationId.toUpperCase()} certification`)
        setResources([])
      } else {
        setError('Failed to load resources. Please try again.')
      }
    } finally {
      setLoading(false)
    }
  }

  const filteredResources = resources.filter(resource =>
    resource.name.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
  }

  const getFileIcon = (contentType: string) => {
    if (contentType.includes('pdf')) return FileText
    if (contentType.includes('image')) return Eye
    return BookOpen
  }

  const handleViewResource = (resource: ResourceFile) => {
    // In a real implementation, this would generate a signed URL or open a viewer
    console.log('Viewing resource:', resource.name)
    // For now, just show an alert
    alert(`Viewing ${resource.name} - This would open the document viewer in a real implementation`)
  }

  const handleDownloadResource = (resource: ResourceFile) => {
    // In a real implementation, this would generate a signed download URL
    console.log('Downloading resource:', resource.name)
    alert(`Downloading ${resource.name} - This would start the download in a real implementation`)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin text-primary-600 mx-auto mb-4" />
          <p className="text-secondary-600">Loading resources...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <Card className="border-red-200 bg-red-50">
        <CardContent className="pt-6">
          <div className="flex items-center space-x-3">
            <AlertCircle className="h-5 w-5 text-red-600" />
            <div>
              <h3 className="text-sm font-medium text-red-800">Error Loading Resources</h3>
              <p className="text-sm text-red-700 mt-1">{error}</p>
            </div>
          </div>
          <Button 
            onClick={fetchResources}
            variant="outline"
            size="sm"
            className="mt-4"
          >
            Try Again
          </Button>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-secondary-400" />
        <Input
          placeholder="Search resources..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="pl-10"
        />
      </div>

      {/* Resource Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center space-x-2">
              <Database className="h-5 w-5 text-primary-600" />
              <div>
                <p className="text-2xl font-bold text-secondary-900">{resources.length}</p>
                <p className="text-sm text-secondary-600">Total Resources</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center space-x-2">
              <FileText className="h-5 w-5 text-blue-600" />
              <div>
                <p className="text-2xl font-bold text-secondary-900">
                  {resources.filter(r => r.contentType.includes('pdf')).length}
                </p>
                <p className="text-sm text-secondary-600">PDF Documents</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center space-x-2">
              <Download className="h-5 w-5 text-green-600" />
              <div>
                <p className="text-2xl font-bold text-secondary-900">
                  {formatFileSize(resources.reduce((total, r) => total + r.size, 0))}
                </p>
                <p className="text-sm text-secondary-600">Total Size</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Resources List */}
      <div className="space-y-4">
        {filteredResources.map((resource) => {
          const FileIcon = getFileIcon(resource.contentType)
          return (
            <Card key={resource.key} className="hover:shadow-md transition-shadow">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4 flex-1">
                    <div className="p-2 bg-primary-100 rounded-lg">
                      <FileIcon className="h-5 w-5 text-primary-600" />
                    </div>
                    
                    <div className="flex-1 min-w-0">
                      <h3 className="text-lg font-medium text-secondary-900 truncate">
                        {resource.name}
                      </h3>
                      <div className="flex items-center space-x-4 mt-1 text-sm text-secondary-600">
                        <span className="flex items-center space-x-1">
                          <Calendar className="h-3 w-3" />
                          <span>{formatDate(resource.lastModified)}</span>
                        </span>
                        <span>{formatFileSize(resource.size)}</span>
                        <Badge variant="secondary" className="text-xs">
                          {resource.contentType.split('/')[1].toUpperCase()}
                        </Badge>
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleViewResource(resource)}
                      className="flex items-center space-x-1"
                    >
                      <Eye className="h-4 w-4" />
                      <span>View</span>
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleDownloadResource(resource)}
                      className="flex items-center space-x-1"
                    >
                      <Download className="h-4 w-4" />
                      <span>Download</span>
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {filteredResources.length === 0 && resources.length > 0 && (
        <div className="text-center py-12">
          <Search className="h-12 w-12 text-secondary-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-secondary-900 mb-2">No resources found</h3>
          <p className="text-secondary-600">
            Try adjusting your search terms
          </p>
        </div>
      )}

      {resources.length === 0 && !loading && (
        <div className="text-center py-12">
          <FileText className="h-12 w-12 text-secondary-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-secondary-900 mb-2">No resources available</h3>
          <p className="text-secondary-600">
            Resources for this certification are not yet available
          </p>
        </div>
      )}
    </div>
  )
}