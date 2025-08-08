import React, { useState, useEffect } from 'react'
import { useAuth } from '../contexts/AuthContext'
import axios from 'axios'

const API_BASE_URL = (import.meta as any).env.VITE_API_URL || 'http://localhost:8000'

interface AboutContent {
  id: string
  title: string
  content: string
  updated_at: string
}

export const AboutPage: React.FC = () => {
  const { user } = useAuth()
  const [aboutContent, setAboutContent] = useState<AboutContent | null>(null)
  const [loading, setLoading] = useState(true)
  const [editing, setEditing] = useState(false)
  const [editTitle, setEditTitle] = useState('')
  const [editContent, setEditContent] = useState('')

  const isAdmin = user?.membership_type === 'enterprise' && user?.email === 'admin@linkware.com'

  useEffect(() => {
    fetchAboutContent()
  }, [])

  const fetchAboutContent = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/content/about`)
      setAboutContent(response.data)
      setEditTitle(response.data.title)
      setEditContent(response.data.content)
    } catch (error) {
      console.error('Error fetching about content:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    if (!isAdmin) return

    try {
      const token = localStorage.getItem('token')
      const response = await axios.put(
        `${API_BASE_URL}/api/content/about`,
        {
          title: editTitle,
          content: editContent
        },
        {
          headers: {
            Authorization: `Bearer ${token}`
          }
        }
      )
      setAboutContent(response.data)
      setEditing(false)
    } catch (error) {
      console.error('Error updating about content:', error)
    }
  }

  const handleCancel = () => {
    setEditTitle(aboutContent?.title || '')
    setEditContent(aboutContent?.content || '')
    setEditing(false)
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-white">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {isAdmin && (
          <div className="mb-6 flex justify-end">
            {!editing ? (
              <button
                onClick={() => setEditing(true)}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
              >
                Edit Content
              </button>
            ) : (
              <div className="space-x-2">
                <button
                  onClick={handleSave}
                  className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors"
                >
                  Save
                </button>
                <button
                  onClick={handleCancel}
                  className="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700 transition-colors"
                >
                  Cancel
                </button>
              </div>
            )}
          </div>
        )}

        <div className="prose prose-lg max-w-none">
          {editing && isAdmin ? (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Title
                </label>
                <input
                  type="text"
                  value={editTitle}
                  onChange={(e) => setEditTitle(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Content
                </label>
                <textarea
                  value={editContent}
                  onChange={(e) => setEditContent(e.target.value)}
                  rows={20}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
          ) : (
            <>
              <h1 className="text-4xl font-bold text-gray-900 mb-8">
                {aboutContent?.title || 'About Us'}
              </h1>
              <div className="text-gray-700 whitespace-pre-wrap">
                {aboutContent?.content || 'Content not available.'}
              </div>
              {aboutContent?.updated_at && (
                <p className="text-sm text-gray-500 mt-8">
                  Last updated: {new Date(aboutContent.updated_at).toLocaleDateString()}
                </p>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}
