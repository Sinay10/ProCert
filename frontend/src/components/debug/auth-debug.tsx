'use client'

import { useSession, signOut } from 'next-auth/react'
import { useState } from 'react'
import { apiClient, API_ENDPOINTS } from '@/lib/api-client'

export function AuthDebug() {
  const { data: session, status } = useSession()
  const [testResult, setTestResult] = useState<string>('')
  const [isLoading, setIsLoading] = useState(false)

  const testApiCall = async () => {
    setIsLoading(true)
    setTestResult('')
    
    try {
      console.log('Testing API call with session:', session)
      
      const response = await apiClient.post(API_ENDPOINTS.CHAT_MESSAGE, {
        message: 'Test message',
        mode: 'rag'
      })
      
      setTestResult(`✅ Success: ${JSON.stringify(response, null, 2)}`)
    } catch (error: any) {
      console.error('API test failed:', error)
      setTestResult(`❌ Axios Error: ${error?.response?.status} - ${error?.response?.data?.message || error?.message}
      
Full error: ${JSON.stringify({
        message: error?.message,
        code: error?.code,
        status: error?.response?.status,
        statusText: error?.response?.statusText,
        data: error?.response?.data,
        config: {
          url: error?.config?.url,
          method: error?.config?.method,
          headers: error?.config?.headers
        }
      }, null, 2)}`)
    } finally {
      setIsLoading(false)
    }
  }

  const testFetchCall = async () => {
    setIsLoading(true)
    setTestResult('')
    
    try {
      console.log('Testing fetch API call...')
      
      const headers: Record<string, string> = {
        'Content-Type': 'application/json'
      }
      
      if (session?.accessToken) {
        headers.Authorization = `Bearer ${session.accessToken}`
      }
      
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/chat/message`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          message: 'Test message',
          mode: 'rag'
        })
      })
      
      const data = await response.text()
      
      setTestResult(`✅ Fetch Success: 
Status: ${response.status}
Data: ${data}`)
    } catch (error: any) {
      console.error('Fetch test failed:', error)
      setTestResult(`❌ Fetch Error: ${error?.message}`)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="p-6 bg-gray-100 rounded-lg">
      <h3 className="text-lg font-bold mb-4">Authentication Debug</h3>
      
      <div className="space-y-4">
        <div>
          <strong>Session Status:</strong> {status}
        </div>
        
        <div>
          <strong>Session Data:</strong>
          <pre className="bg-white p-2 rounded text-sm overflow-auto">
            {JSON.stringify(session, null, 2)}
          </pre>
        </div>
        
        <div>
          <strong>API Base URL (NEXT_PUBLIC):</strong> {process.env.NEXT_PUBLIC_API_BASE_URL}
        </div>
        
        <div>
          <strong>API Base URL (API_BASE_URL):</strong> {process.env.API_BASE_URL}
        </div>
        
        <div className="space-x-2">
          <button
            onClick={testApiCall}
            disabled={isLoading || !session}
            className="px-4 py-2 bg-blue-600 text-white rounded disabled:bg-gray-400"
          >
            {isLoading ? 'Testing...' : 'Test Axios'}
          </button>
          <button
            onClick={testFetchCall}
            disabled={isLoading || !session}
            className="px-4 py-2 bg-green-600 text-white rounded disabled:bg-gray-400"
          >
            {isLoading ? 'Testing...' : 'Test Fetch'}
          </button>
          <button
            onClick={() => signOut()}
            className="px-4 py-2 bg-red-600 text-white rounded"
          >
            Sign Out
          </button>
        </div>
        
        {testResult && (
          <div>
            <strong>Test Result:</strong>
            <pre className="bg-white p-2 rounded text-sm overflow-auto whitespace-pre-wrap">
              {testResult}
            </pre>
          </div>
        )}
      </div>
    </div>
  )
}