import React, { useState, useEffect } from 'react'
import { useAuth } from '../contexts/AuthContext'
import axios from 'axios'

const API_BASE_URL = (import.meta as any).env.VITE_API_URL || 'http://localhost:8000'

interface AboutContent {
  id: string
  title: string
  content: string
  image_url?: string
  updated_at: string
}

export const AboutPage: React.FC = () => {
  const { user } = useAuth()
  const [aboutContent, setAboutContent] = useState<AboutContent | null>(null)
  const [loading, setLoading] = useState(true)
  const [editing, setEditing] = useState(false)
  const [editTitle, setEditTitle] = useState('')
  const [editContent, setEditContent] = useState('')
  const [editImageUrl, setEditImageUrl] = useState<string | null>(null)
  const [imageFile, setImageFile] = useState<File | null>(null)
  const [imagePreview, setImagePreview] = useState<string | null>(null)
  const [uploading, setUploading] = useState(false)

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
      setEditImageUrl(response.data.image_url || null)
    } catch (error) {
      console.error('Error fetching about content:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleImageUpload = async (file: File): Promise<string | null> => {
    if (!isAdmin) return null

    try {
      setUploading(true)
      const token = localStorage.getItem('token')
      const formData = new FormData()
      formData.append('file', file)

      const response = await axios.post(
        `${API_BASE_URL}/api/content/about/upload-image`,
        formData,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'multipart/form-data'
          }
        }
      )

      return response.data.image_url
    } catch (error) {
      console.error('Error uploading image:', error)
      return null
    } finally {
      setUploading(false)
    }
  }

  const handleSave = async () => {
    if (!isAdmin) return

    try {
      let finalImageUrl = editImageUrl

      if (imageFile) {
        const uploadedImageUrl = await handleImageUpload(imageFile)
        if (uploadedImageUrl) {
          finalImageUrl = uploadedImageUrl
        }
      }

      const token = localStorage.getItem('token')
      const response = await axios.put(
        `${API_BASE_URL}/api/content/about`,
        {
          title: editTitle,
          content: editContent,
          image_url: finalImageUrl
        },
        {
          headers: {
            Authorization: `Bearer ${token}`
          }
        }
      )
      setAboutContent(response.data)
      setEditing(false)
      setImageFile(null)
      setImagePreview(null)
    } catch (error) {
      console.error('Error updating about content:', error)
    }
  }

  const handleCancel = () => {
    setEditTitle(aboutContent?.title || '')
    setEditContent(aboutContent?.content || '')
    setEditImageUrl(aboutContent?.image_url || null)
    setImageFile(null)
    setImagePreview(null)
    setEditing(false)
  }

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
      if (!allowedTypes.includes(file.type)) {
        alert('Invalid file type. Only JPEG, PNG, GIF, and WebP are allowed.')
        return
      }

      const maxSize = 5 * 1024 * 1024 // 5MB
      if (file.size > maxSize) {
        alert('File too large. Maximum size is 5MB.')
        return
      }

      setImageFile(file)
      
      const reader = new FileReader()
      reader.onload = (e) => {
        setImagePreview(e.target?.result as string)
      }
      reader.readAsDataURL(file)
    }
  }

  const handleRemoveImage = () => {
    setEditImageUrl(null)
    setImageFile(null)
    setImagePreview(null)
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
                  disabled={uploading}
                  className={`px-4 py-2 rounded-lg transition-colors text-white ${uploading ? 'bg-gray-400 cursor-not-allowed' : 'bg-green-600 hover:bg-green-700'}`}
                >
                  {uploading ? 'Uploading...' : 'Save'}
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
                  rows={15}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Image
                </label>
                <div className="space-y-4">
                  {/* Current or preview image */}
                  {(imagePreview || editImageUrl) && (
                    <div className="relative">
                      <img
                        src={imagePreview || `${API_BASE_URL}${editImageUrl}`}
                        alt="About us"
                        className="max-w-md max-h-64 object-contain border border-gray-300 rounded-lg"
                      />
                      <button
                        type="button"
                        onClick={handleRemoveImage}
                        className="absolute top-2 right-2 bg-red-600 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm hover:bg-red-700"
                      >
                        ×
                      </button>
                    </div>
                  )}
                  
                  {/* File input */}
                  <div>
                    <input
                      type="file"
                      accept="image/jpeg,image/jpg,image/png,image/gif,image/webp"
                      onChange={handleImageChange}
                      className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      Supported formats: JPEG, PNG, GIF, WebP. Max size: 5MB.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <>
              <h1 className="text-4xl font-bold text-gray-900 mb-8">
                {aboutContent?.title || 'About Us'}
              </h1>
              
              {aboutContent?.image_url && (
                <div className="mb-8">
                  <img
                    src={`${API_BASE_URL}${aboutContent.image_url}`}
                    alt="About us"
                    className="max-w-full h-auto rounded-lg shadow-lg"
                  />
                </div>
              )}
              
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
