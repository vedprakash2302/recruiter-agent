'use client'

import React, { useState, useRef, useEffect } from 'react';
import EmailService from '../services/emailService';

const EmailInterface = ({ initialData = null, mode = 'create' }) => {
  // State management - no hardcoded values
  const [emailData, setEmailData] = useState({
    id: null,
    to: '',
    subject: '',
    content: '',
    candidateInfo: {
      name: '',
      currentCompany: '',
      position: '',
      skills: []
    },
    jobInfo: {
      title: '',
      company: '',
      requirements: [],
      benefits: []
    }
  });

  const [improvementRequest, setImprovementRequest] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [isImproving, setIsImproving] = useState(false);
  const [emailSent, setEmailSent] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [showThread, setShowThread] = useState(false);
  const [emailThread, setEmailThread] = useState([]);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  
  const improvementInputRef = useRef(null);

  // Initialize component with provided data
  useEffect(() => {
    if (initialData) {
      setEmailData(prev => ({ ...prev, ...initialData }));
    }
  }, [initialData]);

  // Generate new email using Groq
  const handleGenerateEmail = async () => {
    if (!emailData.candidateInfo.name || !emailData.jobInfo.title) {
      setError('Please provide candidate name and job title');
      return;
    }

    setIsGenerating(true);
    setError(null);

    try {
      const request = {
        candidate_name: emailData.candidateInfo.name,
        candidate_email: emailData.to,
        current_company: emailData.candidateInfo.currentCompany,
        current_position: emailData.candidateInfo.position,
        skills: emailData.candidateInfo.skills,
        job_title: emailData.jobInfo.title,
        job_company: emailData.jobInfo.company,
        job_requirements: emailData.jobInfo.requirements,
        job_benefits: emailData.jobInfo.benefits
      };

      const result = await EmailService.generateEmail(request);
      
      setEmailData(prev => ({
        ...prev,
        content: result.email_content,
        subject: result.subject || `${emailData.jobInfo.title} Opportunity at ${emailData.jobInfo.company}`
      }));
      
      setSuccess('Email generated successfully!');
    } catch (error) {
      setError('Failed to generate email: ' + error.message);
    } finally {
      setIsGenerating(false);
    }
  };

  // Improve email using Groq
  const handleImproveEmail = async () => {
    if (!improvementRequest.trim() || !emailData.content) {
      setError('Please provide improvement instructions and ensure email content exists');
      return;
    }

    setIsImproving(true);
    setError(null);

    try {
      const result = await EmailService.improveEmail(
        emailData.content,
        improvementRequest,
        {
          candidate_info: emailData.candidateInfo,
          job_info: emailData.jobInfo
        }
      );

      setEmailData(prev => ({
        ...prev,
        content: result.improved_content
      }));
      
      setImprovementRequest('');
      setSuccess('Email improved successfully!');
    } catch (error) {
      setError('Failed to improve email: ' + error.message);
    } finally {
      setIsImproving(false);
    }
  };

  // Submit email for approval
  const handleSubmitForApproval = async () => {
    if (!emailData.content || !emailData.to) {
      setError('Please ensure email content and recipient are provided');
      return;
    }

    try {
      const result = await EmailService.submitForApproval({
        id: emailData.id || Date.now().toString(),
        to: emailData.to,
        subject: emailData.subject,
        content: emailData.content,
        metadata: {
          candidateInfo: emailData.candidateInfo,
          jobInfo: emailData.jobInfo
        }
      });

      setSuccess('Email submitted for approval!');
      setEmailData(prev => ({ ...prev, id: result.id }));
    } catch (error) {
      setError('Failed to submit email for approval: ' + error.message);
    }
  };

  // Send email directly
  const handleSendEmail = async () => {
    if (emailSent || isSending) return;

    setIsSending(true);
    setError(null);

    try {
      const result = await EmailService.sendEmail({
        id: emailData.id || Date.now().toString(),
        to: emailData.to,
        subject: emailData.subject,
        content: emailData.content,
        metadata: {
          candidateInfo: emailData.candidateInfo,
          jobInfo: emailData.jobInfo
        }
      });

      setEmailSent(true);
      setSuccess('Email sent successfully!');
      
      // Load email thread after sending
      setTimeout(async () => {
        try {
          const threadData = await EmailService.getEmailThread(result.id);
          setEmailThread(threadData.messages || []);
          setShowThread(true);
        } catch (error) {
          console.warn('Could not load email thread:', error);
        }
      }, 1500);
    } catch (error) {
      setError('Failed to send email: ' + error.message);
    } finally {
      setIsSending(false);
    }
  };

  // Format timestamp for display
  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleString('en-GB', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // Clear messages after timeout
  useEffect(() => {
    if (error || success) {
      const timer = setTimeout(() => {
        setError(null);
        setSuccess(null);
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [error, success]);

  // Quick improvement suggestions
  const quickSuggestions = [
    'make it shorter and more concise',
    'add specific salary details', 
    'make it more personal and engaging',
    'use more formal language',
    'emphasize remote work benefits',
    'highlight growth opportunities'
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 p-4 md:p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        
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
            <div className="w-12 h-12 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 3.26a2 2 0 001.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
            </div>
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-slate-800 to-slate-600 bg-clip-text text-transparent">
                AI Recruiter Email Interface
              </h1>
              <p className="text-slate-600 font-medium">Generate, improve, and manage recruitment emails with Groq AI</p>
            </div>
          </div>

          {/* Input Forms */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            {/* Candidate Information */}
            <div className="bg-slate-50 rounded-xl p-6 border border-slate-200">
              <h3 className="text-lg font-bold text-slate-800 mb-4 flex items-center gap-2">
                <svg className="w-5 h-5 text-purple-600" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
                </svg>
                Candidate Information
              </h3>
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-semibold text-slate-700 block mb-1">Name</label>
                  <input
                    type="text"
                    value={emailData.candidateInfo.name}
                    onChange={(e) => setEmailData(prev => ({
                      ...prev,
                      candidateInfo: { ...prev.candidateInfo, name: e.target.value }
                    }))}
                    className="w-full p-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-slate-900 placeholder:text-slate-500"
                    placeholder="Candidate's full name"
                  />
                </div>
                <div>
                  <label className="text-sm font-semibold text-slate-700 block mb-1">Email</label>
                  <input
                    type="email"
                    value={emailData.to}
                    onChange={(e) => setEmailData(prev => ({ ...prev, to: e.target.value }))}
                    className="w-full p-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-slate-900 placeholder:text-slate-500"
                    placeholder="candidate@company.com"
                  />
                </div>
                <div>
                  <label className="text-sm font-semibold text-slate-700 block mb-1">Current Company</label>
                  <input
                    type="text"
                    value={emailData.candidateInfo.currentCompany}
                    onChange={(e) => setEmailData(prev => ({
                      ...prev,
                      candidateInfo: { ...prev.candidateInfo, currentCompany: e.target.value }
                    }))}
                    className="w-full p-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-slate-900 placeholder:text-slate-500"
                    placeholder="Current company name"
                  />
                </div>
                <div>
                  <label className="text-sm font-semibold text-slate-700 block mb-1">Current Position</label>
                  <input
                    type="text"
                    value={emailData.candidateInfo.position}
                    onChange={(e) => setEmailData(prev => ({
                      ...prev,
                      candidateInfo: { ...prev.candidateInfo, position: e.target.value }
                    }))}
                    className="w-full p-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-slate-900 placeholder:text-slate-500"
                    placeholder="Current job title"
                  />
                </div>
                <div>
                  <label className="text-sm font-semibold text-slate-700 block mb-1">Skills (comma-separated)</label>
                  <input
                    type="text"
                    value={emailData.candidateInfo.skills.join(', ')}
                    onChange={(e) => setEmailData(prev => ({
                      ...prev,
                      candidateInfo: {
                        ...prev.candidateInfo,
                        skills: e.target.value.split(',').map(skill => skill.trim()).filter(Boolean)
                      }
                    }))}
                    className="w-full p-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-slate-900 placeholder:text-slate-500"
                    placeholder="React, Node.js, Python, etc."
                  />
                </div>
              </div>
            </div>

            {/* Job Information */}
            <div className="bg-slate-50 rounded-xl p-6 border border-slate-200">
              <h3 className="text-lg font-bold text-slate-800 mb-4 flex items-center gap-2">
                <svg className="w-5 h-5 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M6 6V5a3 3 0 013-3h2a3 3 0 013 3v1h2a2 2 0 012 2v3.57A22.952 22.952 0 0110 13a22.95 22.95 0 01-8-1.43V8a2 2 0 012-2h2zm2-1a1 1 0 011-1h2a1 1 0 011 1v1H8V5zm1 5a1 1 0 011-1h.01a1 1 0 110 2H10a1 1 0 01-1-1z" clipRule="evenodd" />
                </svg>
                Job Information
              </h3>
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-semibold text-slate-700 block mb-1">Job Title</label>
                  <input
                    type="text"
                    value={emailData.jobInfo.title}
                    onChange={(e) => setEmailData(prev => ({
                      ...prev,
                      jobInfo: { ...prev.jobInfo, title: e.target.value }
                    }))}
                    className="w-full p-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-slate-900 placeholder:text-slate-500"
                    placeholder="Senior Software Engineer"
                  />
                </div>
                <div>
                  <label className="text-sm font-semibold text-slate-700 block mb-1">Company</label>
                  <input
                    type="text"
                    value={emailData.jobInfo.company}
                    onChange={(e) => setEmailData(prev => ({
                      ...prev,
                      jobInfo: { ...prev.jobInfo, company: e.target.value }
                    }))}
                    className="w-full p-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-slate-900 placeholder:text-slate-500"
                    placeholder="Company name"
                  />
                </div>
                <div>
                  <label className="text-sm font-semibold text-slate-700 block mb-1">Requirements (comma-separated)</label>
                  <input
                    type="text"
                    value={emailData.jobInfo.requirements.join(', ')}
                    onChange={(e) => setEmailData(prev => ({
                      ...prev,
                      jobInfo: {
                        ...prev.jobInfo,
                        requirements: e.target.value.split(',').map(req => req.trim()).filter(Boolean)
                      }
                    }))}
                    className="w-full p-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-slate-900 placeholder:text-slate-500"
                    placeholder="5+ years experience, React expertise, etc."
                  />
                </div>
                <div>
                  <label className="text-sm font-semibold text-slate-700 block mb-1">Benefits (comma-separated)</label>
                  <input
                    type="text"
                    value={emailData.jobInfo.benefits.join(', ')}
                    onChange={(e) => setEmailData(prev => ({
                      ...prev,
                      jobInfo: {
                        ...prev.jobInfo,
                        benefits: e.target.value.split(',').map(benefit => benefit.trim()).filter(Boolean)
                      }
                    }))}
                    className="w-full p-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-slate-900 placeholder:text-slate-500"
                    placeholder="Remote work, competitive salary, health benefits, etc."
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Generate Email Button */}
          <div className="flex justify-center">
            <button
              onClick={handleGenerateEmail}
              disabled={isGenerating || !emailData.candidateInfo.name || !emailData.jobInfo.title}
              className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 disabled:from-slate-400 disabled:to-slate-500 text-white font-semibold py-3 px-8 rounded-xl transition-all duration-200 disabled:cursor-not-allowed flex items-center gap-2 shadow-lg hover:shadow-xl"
            >
              {isGenerating ? (
                <>
                  <svg className="w-5 h-5 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  Generating with Groq AI...
                </>
              ) : (
                <>
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                  Generate Email with Groq AI
                </>
              )}
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Email Content & Controls */}
          <div className="lg:col-span-2 space-y-6">
            
            {/* Email Content */}
            <div className="bg-white rounded-2xl shadow-xl border border-slate-200 overflow-hidden">
              <div className="bg-gradient-to-r from-slate-800 to-slate-700 p-6">
                <h2 className="text-xl font-bold text-white flex items-center gap-3">
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M2.003 5.884L10 9.882l7.997-3.998A2 2 0 0016 4H4a2 2 0 00-1.997 1.884z" />
                    <path d="M18 8.118l-8 4-8-4V14a2 2 0 002 2h12a2 2 0 002-2V8.118z" />
                  </svg>
                  Email Content
                </h2>
              </div>
              <div className="p-6 space-y-4">
                <div>
                  <label className="text-sm font-semibold text-slate-700 block mb-2">Subject</label>
                  <input
                    type="text"
                    value={emailData.subject}
                    onChange={(e) => setEmailData(prev => ({ ...prev, subject: e.target.value }))}
                    className="w-full p-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-slate-900 placeholder:text-slate-500"
                    placeholder="Email subject line"
                    disabled={emailSent}
                  />
                </div>
                <div>
                  <label className="text-sm font-semibold text-slate-700 block mb-2">Content</label>
                  <textarea
                    value={emailData.content}
                    onChange={(e) => setEmailData(prev => ({ ...prev, content: e.target.value }))}
                    className="w-full h-96 p-4 border border-slate-300 rounded-xl resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 text-slate-900 placeholder:text-slate-500 leading-relaxed"
                    placeholder="Email content will appear here after generation..."
                    disabled={emailSent}
                  />
                </div>
              </div>
            </div>

            {/* Improvement Controls */}
            {emailData.content && (
              <div className="bg-white rounded-2xl shadow-xl border border-slate-200 overflow-hidden">
                <div className="bg-gradient-to-r from-indigo-600 to-purple-600 p-6">
                  <h3 className="text-xl font-bold text-white flex items-center gap-3">
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clipRule="evenodd" />
                    </svg>
                    Email Improvement Assistant
                  </h3>
                  <p className="text-indigo-100 mt-2">Request specific improvements powered by Groq AI</p>
                </div>
                <div className="p-6">
                  <div className="mb-4">
                    <textarea
                      ref={improvementInputRef}
                      value={improvementRequest}
                      onChange={(e) => setImprovementRequest(e.target.value)}
                      placeholder="Describe how you'd like to improve the email (e.g., 'make it shorter', 'add more details about benefits', 'make it more formal')..."
                      className="w-full h-24 p-4 border border-slate-300 rounded-xl resize-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all duration-200 text-slate-900 placeholder:text-slate-500"
                      disabled={emailSent || isImproving}
                    />
                  </div>
                  
                  {/* Improvement Suggestions */}
                  <div className="mb-4">
                    <p className="text-sm font-medium text-slate-700 mb-2">Quick suggestions:</p>
                    <div className="flex flex-wrap gap-2">
                      {quickSuggestions.map((suggestion) => (
                        <button
                          key={suggestion}
                          onClick={() => setImprovementRequest(suggestion)}
                          disabled={emailSent || isImproving}
                          className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-sm transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          {suggestion}
                        </button>
                      ))}
                    </div>
                  </div>

                  <button
                    onClick={handleImproveEmail}
                    disabled={!improvementRequest.trim() || emailSent || isImproving}
                    className="w-full bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 disabled:from-slate-400 disabled:to-slate-500 text-white font-semibold py-3 px-6 rounded-xl transition-all duration-200 disabled:cursor-not-allowed flex items-center justify-center gap-2 shadow-lg hover:shadow-xl"
                  >
                    {isImproving ? (
                      <>
                        <svg className="w-5 h-5 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                        </svg>
                        Improving with Groq AI...
                      </>
                    ) : (
                      <>
                        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clipRule="evenodd" />
                        </svg>
                        Improve Email
                      </>
                    )}
                  </button>
                </div>
              </div>
            )}

            {/* Action Buttons */}
            {emailData.content && (
              <div className="bg-white rounded-2xl shadow-xl border border-slate-200 p-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <button
                    onClick={handleSubmitForApproval}
                    disabled={emailSent}
                    className="bg-gradient-to-r from-yellow-500 to-orange-500 hover:from-yellow-600 hover:to-orange-600 disabled:from-slate-400 disabled:to-slate-500 text-white font-semibold py-3 px-6 rounded-xl transition-all duration-200 disabled:cursor-not-allowed flex items-center justify-center gap-2 shadow-lg hover:shadow-xl"
                  >
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    Submit for Approval
                  </button>
                  
                  <button
                    onClick={handleSendEmail}
                    disabled={emailSent || isSending}
                    className={`font-semibold py-3 px-6 rounded-xl transition-all duration-200 flex items-center justify-center gap-2 shadow-lg hover:shadow-xl ${
                      emailSent
                        ? 'bg-green-100 text-green-800 border border-green-200 cursor-not-allowed'
                        : 'bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white'
                    }`}
                  >
                    {emailSent ? (
                      <>
                        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                        Email Sent
                      </>
                    ) : isSending ? (
                      <>
                        <svg className="w-5 h-5 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                        </svg>
                        Sending...
                      </>
                    ) : (
                      <>
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                        </svg>
                        Send Email
                      </>
                    )}
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Email Thread Viewer */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-2xl shadow-xl border border-slate-200 overflow-hidden h-fit">
              <div className="bg-gradient-to-r from-emerald-600 to-green-600 p-6">
                <h3 className="text-xl font-bold text-white flex items-center gap-3">
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clipRule="evenodd" />
                  </svg>
                  Email Thread
                </h3>
                <p className="text-emerald-100 mt-2">Conversation monitoring</p>
              </div>

              <div className="p-6">
                {!showThread && !emailSent ? (
                  <div className="text-center py-12">
                    <svg className="w-16 h-16 mx-auto text-slate-300 mb-4" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clipRule="evenodd" />
                    </svg>
                    <p className="text-slate-500 font-medium">No conversation yet</p>
                    <p className="text-slate-400 text-sm mt-1">Thread will appear after sending email</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {emailThread.map((message) => (
                      <div
                        key={message.id}
                        className={`p-4 rounded-xl border-2 transition-all duration-200 ${
                          message.type === 'sent'
                            ? 'bg-blue-50 border-blue-200 ml-4'
                            : 'bg-green-50 border-green-200 mr-4'
                        }`}
                      >
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white text-sm font-bold ${
                              message.type === 'sent' ? 'bg-blue-600' : 'bg-green-600'
                            }`}>
                              {message.sender?.charAt(0).toUpperCase() || 'U'}
                            </div>
                            <div>
                              <p className="text-sm font-semibold text-slate-800">
                                {message.type === 'sent' ? 'You' : emailData.candidateInfo.name || 'Candidate'}
                              </p>
                              <p className="text-xs text-slate-500">{formatTimestamp(message.timestamp)}</p>
                            </div>
                          </div>
                          <div className={`px-2 py-1 rounded-full text-xs font-medium ${
                            message.type === 'sent'
                              ? 'bg-blue-100 text-blue-800'
                              : 'bg-green-100 text-green-800'
                          }`}>
                            {message.type === 'sent' ? 'Sent' : 'Received'}
                          </div>
                        </div>
                        <p className="text-slate-700 text-sm leading-relaxed">{message.content}</p>
                      </div>
                    ))}

                    {showThread && (
                      <div className="border-t pt-4 mt-6">
                        <div className="flex items-center gap-2 text-green-600 mb-2">
                          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                          <p className="text-sm font-medium">Active conversation</p>
                        </div>
                        <p className="text-xs text-slate-500">
                          Monitoring for new replies from {emailData.candidateInfo.name || 'candidate'}
                        </p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>

            {/* Email Status Summary */}
            {emailSent && (
              <div className="mt-6 bg-green-50 border border-green-200 rounded-2xl p-6">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 bg-green-600 rounded-full flex items-center justify-center">
                    <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div>
                    <h4 className="font-bold text-green-800">Email Sent Successfully</h4>
                    <p className="text-green-600 text-sm">Recruitment outreach completed</p>
                  </div>
                </div>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-green-700">Recipient:</span>
                    <span className="font-medium text-green-800">{emailData.to}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-green-700">Sent at:</span>
                    <span className="font-medium text-green-800">{formatTimestamp(new Date().toISOString())}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-green-700">Status:</span>
                    <span className="font-medium text-green-800">Delivered</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default EmailInterface;