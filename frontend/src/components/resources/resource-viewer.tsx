'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { 
  X, 
  Download, 
  ZoomIn, 
  ZoomOut, 
  RotateCw,
  FileText
} from 'lucide-react'

interface ResourceViewerProps {
  resourceName: string
  resourceUrl: string
  onClose: () => void
}

export function ResourceViewer({ resourceName, resourceUrl, onClose }: ResourceViewerProps) {
  const [zoom, setZoom] = useState(100)

  const handleZoomIn = () => {
    setZoom(prev => Math.min(prev + 25, 200))
  }

  const handleZoomOut = () => {
    setZoom(prev => Math.max(prev - 25, 50))
  }

  const handleDownload = () => {
    // In a real implementation, this would trigger the download
    const link = document.createElement('a')
    link.href = resourceUrl
    link.download = resourceName
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-6xl h-full max-h-[90vh] flex flex-col">
        <CardHeader className="flex-shrink-0 border-b">
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center space-x-2">
              <FileText className="h-5 w-5" />
              <span className="truncate">{resourceName}</span>
            </CardTitle>
            
            <div className="flex items-center space-x-2">
              {/* Viewer Controls */}
              <div className="flex items-center space-x-1 border rounded-lg p-1">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleZoomOut}
                  disabled={zoom <= 50}
                >
                  <ZoomOut className="h-4 w-4" />
                </Button>
                <span className="text-sm px-2 min-w-[60px] text-center">
                  {zoom}%
                </span>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleZoomIn}
                  disabled={zoom >= 200}
                >
                  <ZoomIn className="h-4 w-4" />
                </Button>
              </div>
              
              <Button
                variant="outline"
                size="sm"
                onClick={handleDownload}
              >
                <Download className="h-4 w-4 mr-1" />
                Download
              </Button>
              
              <Button
                variant="outline"
                size="sm"
                onClick={onClose}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardHeader>
        
        <CardContent className="flex-1 p-0 overflow-hidden">
          <div className="h-full flex items-center justify-center bg-gray-100">
            {/* PDF Viewer Placeholder */}
            <div className="text-center p-8">
              <FileText className="h-16 w-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                Document Viewer
              </h3>
              <p className="text-gray-600 mb-4">
                In a full implementation, this would display the PDF content using a library like PDF.js
              </p>
              <div className="space-y-2 text-sm text-gray-500">
                <p>Resource: {resourceName}</p>
                <p>Zoom: {zoom}%</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}