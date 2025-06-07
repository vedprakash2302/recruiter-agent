'use client'

import Link from 'next/link'

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      {/* Hero Section */}
      <div className="pt-16 pb-20 px-4 md:px-6">
        <div className="max-w-6xl mx-auto text-center">
          
          {/* Main Heading */}
          <div className="mb-12">
            <h1 className="text-4xl md:text-6xl font-bold mb-6">
              <span className="bg-gradient-to-r from-slate-800 via-blue-800 to-indigo-800 bg-clip-text text-transparent">
                AI-Powered Recruitment
              </span>
              <br />
              <span className="bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                Platform
              </span>
            </h1>
            <p className="text-xl md:text-2xl text-slate-600 max-w-3xl mx-auto leading-relaxed">
              Streamline your recruitment process with intelligent resume analysis and automated email generation
            </p>
          </div>

          {/* Feature Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-16">
            
            {/* Upload Resume Card */}
            <Link href="/upload-resume" className="group">
              <div className="bg-white rounded-2xl shadow-xl border border-slate-200 p-8 transform transition-all duration-300 hover:scale-105 hover:shadow-2xl">
                <div className="w-16 h-16 bg-gradient-to-r from-green-600 to-emerald-600 rounded-2xl flex items-center justify-center mx-auto mb-6 group-hover:scale-110 transition-transform duration-300">
                  <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                </div>
                <h2 className="text-2xl font-bold text-slate-800 mb-4">Upload Resume</h2>
                <p className="text-slate-600 mb-6 leading-relaxed">
                  Submit your resume with job descriptions for AI-powered analysis and personalized application suggestions
                </p>
                <div className="flex items-center justify-center text-green-600 font-semibold group-hover:text-green-700 transition-colors duration-200">
                  <span>Get Started</span>
                  <svg className="w-5 h-5 ml-2 transform group-hover:translate-x-1 transition-transform duration-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
                  </svg>
                </div>
              </div>
            </Link>

            {/* Email Interface Card */}
            <Link href="/email-interface" className="group">
              <div className="bg-white rounded-2xl shadow-xl border border-slate-200 p-8 transform transition-all duration-300 hover:scale-105 hover:shadow-2xl">
                <div className="w-16 h-16 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-2xl flex items-center justify-center mx-auto mb-6 group-hover:scale-110 transition-transform duration-300">
                  <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 3.26a2 2 0 001.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                </div>
                <h2 className="text-2xl font-bold text-slate-800 mb-4">Email Interface</h2>
                <p className="text-slate-600 mb-6 leading-relaxed">
                  Generate, improve, and manage recruitment emails with Groq AI assistance and approval workflows
                </p>
                <div className="flex items-center justify-center text-blue-600 font-semibold group-hover:text-blue-700 transition-colors duration-200">
                  <span>Create Emails</span>
                  <svg className="w-5 h-5 ml-2 transform group-hover:translate-x-1 transition-transform duration-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
                  </svg>
                </div>
              </div>
            </Link>
          </div>

          {/* Features Overview */}
          <div className="bg-white rounded-2xl shadow-xl border border-slate-200 p-8 md:p-12">
            <h3 className="text-2xl font-bold text-slate-800 mb-8">Platform Features</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              
              <div className="text-center">
                <div className="w-12 h-12 bg-purple-100 text-purple-600 rounded-xl flex items-center justify-center mx-auto mb-4">
                  <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <h4 className="font-bold text-slate-800 mb-2">AI Analysis</h4>
                <p className="text-slate-600 text-sm">Advanced AI algorithms analyze resumes and job requirements for optimal matching</p>
              </div>
              
              <div className="text-center">
                <div className="w-12 h-12 bg-yellow-100 text-yellow-600 rounded-xl flex items-center justify-center mx-auto mb-4">
                  <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clipRule="evenodd" />
                  </svg>
                </div>
                <h4 className="font-bold text-slate-800 mb-2">Smart Automation</h4>
                <p className="text-slate-600 text-sm">Automated email generation and improvement suggestions powered by Groq AI</p>
              </div>
              
              <div className="text-center">
                <div className="w-12 h-12 bg-green-100 text-green-600 rounded-xl flex items-center justify-center mx-auto mb-4">
                  <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                </div>
                <h4 className="font-bold text-slate-800 mb-2">Approval Workflow</h4>
                <p className="text-slate-600 text-sm">Streamlined approval process with email queue management and tracking</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}