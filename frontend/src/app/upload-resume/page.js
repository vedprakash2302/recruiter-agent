'use client'

import React, { useState } from 'react'

const UploadResumePage = () => {
  const [formData, setFormData] = useState({
    jobUrl: '',
    resumeFile: null
  })
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)
  const [dragActive, setDragActive] = useState(false)

  // Handle URL input change
  const handleUrlChange = (e) => {
    setFormData(prev => ({
      ...prev,
      jobUrl: e.target.value
    }))
  }

  // Handle file selection
  const handleFileSelect = (file) => {
    if (file && file.type === 'application/pdf') {
      setFormData(prev => ({
        ...prev,
        resumeFile: file
      }))
      setError(null)
    } else {
      setError('Please select a PDF file only. Microsoft Word files are not supported.')
      setFormData(prev => ({
        ...prev,
        resumeFile: null
      }))
    }
  }

  // Handle file input change
  const handleFileChange = (e) => {
    const file = e.target.files[0]
    handleFileSelect(file)
  }

  // Handle drag events
  const handleDrag = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  // Handle drop
  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0])
    }
  }

  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!formData.jobUrl.trim() || !formData.resumeFile) {
      setError('Please provide both job URL and resume file')
      return
    }

    setIsSubmitting(true)
    setError(null)
    setSuccess(null)

    try {
      // Create FormData for file upload
      const uploadData = new FormData()
      uploadData.append('resume', formData.resumeFile)
      uploadData.append('jobUrl', formData.jobUrl.trim())

      const response = await fetch('/api/upload-resume', {
        method: 'POST',
        body: uploadData
      })

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`)
      }

      const result = await response.json()
      setSuccess('Resume uploaded successfully! Processing job application...')
      
      // Reset form
      setFormData({
        jobUrl: '',
        resumeFile: null
      })
      
      // Reset file input
      const fileInput = document.getElementById('resume-file-input')
      if (fileInput) fileInput.value = ''

    } catch (error) {
      console.error('Upload error:', error)
      setError('Failed to upload resume: ' + error.message)
    } finally {
      setIsSubmitting(false)
    }
  }

  // Format file size
  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 p-4 md:p-6">
      <div className="max-w-4xl mx-auto space-y-6">
        
        {/* Status Messages */}
        {(error || success) && (
          <div className={`rounded-xl border p-4 ${
            error 
              ? 'bg-red-50 border-red-200 text-red-800' 
              : 'bg-green-50 border-green-200 text-green-800'
          }`}>
            <div className="flex items-center gap-2">
              {error ? (
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
              ) : (
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
              )}
              <span className="font-medium">{error || success}</span>
            </div>
          </div>
        )}

        {/* Header */}
        <div className="bg-white rounded-2xl shadow-xl border border-slate-200 p-6 md:p-8">
          <div className="flex items-center gap-4 mb-6">
            <div className="w-12 h-12 bg-gradient-to-r from-green-600 to-emerald-600 rounded-xl flex items-center justify-center shadow-lg">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
            </div>
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-slate-800 to-slate-600 bg-clip-text text-transparent">
                Upload Resume
              </h1>
              <p className="text-slate-600 font-medium">Submit your resume with job URL for AI-powered analysis</p>
            </div>
          </div>

          {/* Upload Form */}
          <form onSubmit={handleSubmit} className="space-y-6">
            
            {/* Job URL Input */}
            <div className="bg-slate-50 rounded-xl p-6 border border-slate-200">
              <label htmlFor="job-url" className="text-lg font-bold text-slate-800 mb-4 flex items-center gap-2">
                <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.102m0 0l2.829-2.829m0 0a4 4 0 105.656-5.656l-4-4a4 4 0 00-5.656 0l-1.102 1.102" />
                </svg>
                Job Description URL
              </label>
              <input
                id="job-url"
                type="url"
                value={formData.jobUrl}
                onChange={handleUrlChange}
                className="w-full p-4 border border-slate-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 text-lg text-slate-900 placeholder:text-slate-500"
                placeholder="https://example.com/job-posting"
                required
                disabled={isSubmitting}
              />
              <p className="text-sm text-slate-500 mt-2">
                Paste the URL of the job description you're applying for
              </p>
            </div>

            {/* File Upload */}
            <div className="bg-slate-50 rounded-xl p-6 border border-slate-200">
              <label className="text-lg font-bold text-slate-800 mb-4 flex items-center gap-2">
                <svg className="w-5 h-5 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                Resume File (PDF Only)
              </label>
              
              {/* Drag & Drop Area */}
              <div
                className={`border-2 border-dashed rounded-xl p-8 text-center transition-all duration-200 ${
                  dragActive
                    ? 'border-blue-400 bg-blue-50'
                    : formData.resumeFile
                    ? 'border-green-400 bg-green-50'
                    : 'border-slate-300 hover:border-slate-400'
                }`}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
              >
                {formData.resumeFile ? (
                  <div className="space-y-4">
                    <svg className="w-16 h-16 mx-auto text-green-600" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clipRule="evenodd" />
                    </svg>
                    <div>
                      <p className="text-lg font-medium text-green-800">{formData.resumeFile.name}</p>
                      <p className="text-green-600">{formatFileSize(formData.resumeFile.size)}</p>
                    </div>
                    <button
                      type="button"
                      onClick={() => setFormData(prev => ({ ...prev, resumeFile: null }))}
                      className="text-red-600 hover:text-red-700 font-medium transition-colors duration-200"
                    >
                      Remove file
                    </button>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <svg className="w-16 h-16 mx-auto text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                    <div>
                      <p className="text-lg font-medium text-slate-700">
                        Drag & drop your PDF resume here
                      </p>
                      <p className="text-slate-500">or click to browse files</p>
                    </div>
                    <label className="inline-block">
                      <input
                        id="resume-file-input"
                        type="file"
                        accept=".pdf"
                        onChange={handleFileChange}
                        className="hidden"
                        disabled={isSubmitting}
                      />
                      <span className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-semibold py-3 px-6 rounded-xl transition-all duration-200 cursor-pointer inline-flex items-center gap-2 shadow-lg hover:shadow-xl">
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                        </svg>
                        Choose PDF File
                      </span>
                    </label>
                  </div>
                )}
              </div>
              
              <div className="mt-4 bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                <p className="text-yellow-800 text-sm font-medium flex items-center gap-2">
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                  Only PDF files are accepted. Microsoft Word files (.doc, .docx) are not supported.
                </p>
              </div>
            </div>

            {/* Submit Button */}
            <div className="flex justify-center pt-6">
              <button
                type="submit"
                disabled={!formData.jobUrl.trim() || !formData.resumeFile || isSubmitting}
                className="bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 disabled:from-slate-400 disabled:to-slate-500 text-white font-bold py-4 px-12 rounded-xl transition-all duration-200 disabled:cursor-not-allowed flex items-center gap-3 shadow-lg hover:shadow-xl text-lg"
              >
                {isSubmitting ? (
                  <>
                    <svg className="w-6 h-6 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                    Processing Application...
                  </>
                ) : (
                  <>
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                    </svg>
                    Submit Application
                  </>
                )}
              </button>
            </div>
          </form>
        </div>

        {/* Information Panel */}
        <div className="bg-white rounded-2xl shadow-xl border border-slate-200 p-6">
          <h2 className="text-xl font-bold text-slate-800 mb-4 flex items-center gap-2">
            <svg className="w-5 h-5 text-indigo-600" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
            </svg>
            How It Works
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center p-4 bg-slate-50 rounded-lg">
              <div className="w-12 h-12 bg-blue-100 text-blue-600 rounded-lg flex items-center justify-center mx-auto mb-3">
                <span className="font-bold text-lg">1</span>
              </div>
              <h3 className="font-semibold text-slate-800 mb-2">Upload Resume</h3>
              <p className="text-slate-600 text-sm">Submit your PDF resume and job description URL</p>
            </div>
            <div className="text-center p-4 bg-slate-50 rounded-lg">
              <div className="w-12 h-12 bg-green-100 text-green-600 rounded-lg flex items-center justify-center mx-auto mb-3">
                <span className="font-bold text-lg">2</span>
              </div>
              <h3 className="font-semibold text-slate-800 mb-2">AI Analysis</h3>
              <p className="text-slate-600 text-sm">Our AI analyzes your resume against job requirements</p>
            </div>
            <div className="text-center p-4 bg-slate-50 rounded-lg">
              <div className="w-12 h-12 bg-purple-100 text-purple-600 rounded-lg flex items-center justify-center mx-auto mb-3">
                <span className="font-bold text-lg">3</span>
              </div>
              <h3 className="font-semibold text-slate-800 mb-2">Get Results</h3>
              <p className="text-slate-600 text-sm">Receive personalized application suggestions</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default UploadResumePage