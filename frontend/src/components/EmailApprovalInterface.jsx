'use client'

import React, { useState, useRef, useEffect } from 'react';

// Mock data for demonstration
const mockEmailData = {
  to: "sarah.johnson@techcorp.com",
  subject: "Exciting Software Engineer Opportunity at InnovateTech",
  generatedContent: `Dear Sarah,

I hope this email finds you well. I came across your impressive profile and experience in full-stack development, particularly your work with React and Node.js at DataFlow Solutions.

We have an exciting Software Engineer position at InnovateTech that aligns perfectly with your background. The role involves:

• Leading frontend development using React and TypeScript
• Building scalable backend APIs with Node.js
• Collaborating with cross-functional teams on innovative projects
• Mentoring junior developers

Your experience with microservices architecture and cloud deployment would be invaluable to our growing team. We offer competitive compensation, flexible remote work, and excellent growth opportunities.

Would you be interested in discussing this opportunity further? I'd love to schedule a brief call to learn more about your career goals.

Best regards,
Alex Thompson
Senior Technical Recruiter
InnovateTech Solutions`,
  context: {
    candidateName: "Sarah Johnson",
    currentCompany: "DataFlow Solutions",
    position: "Software Engineer",
    skills: ["React", "Node.js", "TypeScript", "Microservices"]
  }
};

const mockEmailThread = [
  {
    id: 1,
    sender: "alex.thompson@innovatetech.com",
    timestamp: "2025-06-07 10:30:00",
    content: "Initial outreach email sent",
    type: "sent"
  },
  {
    id: 2,
    sender: "sarah.johnson@techcorp.com",
    timestamp: "2025-06-07 14:45:00",
    content: "Hi Alex, thank you for reaching out. I'm definitely interested in learning more about this opportunity. When would be a good time for a call?",
    type: "received"
  }
];

const EmailApprovalInterface = () => {
  const [emailContent, setEmailContent] = useState(mockEmailData.generatedContent);
  const [improvementText, setImprovementText] = useState('');
  const [emailSent, setEmailSent] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [emailThread, setEmailThread] = useState(mockEmailThread);
  const [showThread, setShowThread] = useState(false);
  const improvementRef = useRef(null);

  // Mock function to simulate AI improvement
  const handleImproveEmail = async () => {
    if (!improvementText.trim()) return;
    
    setIsGenerating(true);
    
    // Simulate API call delay
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // Mock improved content based on user input
    let improvedContent = emailContent;
    
    if (improvementText.toLowerCase().includes('shorter')) {
      improvedContent = `Dear Sarah,

I came across your impressive full-stack development experience at DataFlow Solutions and believe you'd be perfect for our Software Engineer role at InnovateTech.

Key highlights:
• Lead React/TypeScript frontend development
• Build Node.js backend APIs
• Mentor team members
• Remote-friendly environment

Your microservices and cloud experience would be invaluable. Interested in a quick call to discuss?

Best regards,
Alex Thompson
Senior Technical Recruiter
InnovateTech Solutions`;
    } else if (improvementText.toLowerCase().includes('formal')) {
      improvedContent = emailContent.replace('I hope this email finds you well.', 'I trust this correspondence finds you in good health and spirits.');
    } else if (improvementText.toLowerCase().includes('benefits')) {
      improvedContent = emailContent.replace(
        'We offer competitive compensation, flexible remote work, and excellent growth opportunities.',
        'We offer competitive compensation ($120K-150K), flexible remote work, comprehensive health benefits, 4 weeks PTO, professional development budget, and excellent growth opportunities.'
      );
    }
    
    setEmailContent(improvedContent);
    setImprovementText('');
    setIsGenerating(false);
  };

  const handleSendEmail = () => {
    setEmailSent(true);
    // Simulate email being sent and thread updates
    setTimeout(() => {
      setShowThread(true);
    }, 1000);
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleString('en-GB', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 p-4 md:p-6">
      <div className="max-w-6xl mx-auto space-y-6">
        
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
                AI Recruiter Email Approval
              </h1>
              <p className="text-slate-600 font-medium">Review and approve AI-generated recruitment emails</p>
            </div>
          </div>

          {/* Email Metadata */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            <div className="bg-slate-50 rounded-xl p-4 border border-slate-200">
              <label className="text-sm font-semibold text-slate-700 mb-2 block">Recipient</label>
              <p className="text-slate-900 font-medium">{mockEmailData.to}</p>
              <p className="text-sm text-slate-600 mt-1">{mockEmailData.context.candidateName} • {mockEmailData.context.currentCompany}</p>
            </div>
            <div className="bg-slate-50 rounded-xl p-4 border border-slate-200">
              <label className="text-sm font-semibold text-slate-700 mb-2 block">Subject</label>
              <p className="text-slate-900 font-medium">{mockEmailData.subject}</p>
            </div>
          </div>

          {/* Skills Tags */}
          <div className="mb-6">
            <label className="text-sm font-semibold text-slate-700 mb-3 block">Candidate Skills</label>
            <div className="flex flex-wrap gap-2">
              {mockEmailData.context.skills.map((skill, index) => (
                <span 
                  key={index}
                  className="px-3 py-1.5 bg-blue-100 text-blue-800 rounded-full text-sm font-medium border border-blue-200"
                >
                  {skill}
                </span>
              ))}
            </div>
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
                  Generated Email Content
                </h2>
              </div>
              <div className="p-6">
                <textarea
                  value={emailContent}
                  onChange={(e) => setEmailContent(e.target.value)}
                  className="w-full h-96 p-4 border border-slate-300 rounded-xl resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 text-slate-700 leading-relaxed"
                  placeholder="Email content will appear here..."
                  disabled={emailSent}
                />
              </div>
            </div>

            {/* Improvement Controls */}
            <div className="bg-white rounded-2xl shadow-xl border border-slate-200 overflow-hidden">
              <div className="bg-gradient-to-r from-indigo-600 to-purple-600 p-6">
                <h3 className="text-xl font-bold text-white flex items-center gap-3">
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clipRule="evenodd" />
                  </svg>
                  Email Improvement Assistant
                </h3>
                <p className="text-indigo-100 mt-2">Request specific improvements to the email content</p>
              </div>
              <div className="p-6">
                <div className="mb-4">
                  <textarea
                    ref={improvementRef}
                    value={improvementText}
                    onChange={(e) => setImprovementText(e.target.value)}
                    placeholder="Describe how you'd like to improve the email (e.g., 'make it shorter', 'add more details about benefits', 'make it more formal')..."
                    className="w-full h-24 p-4 border border-slate-300 rounded-xl resize-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all duration-200"
                    disabled={emailSent || isGenerating}
                  />
                </div>
                
                {/* Improvement Suggestions */}
                <div className="mb-4">
                  <p className="text-sm font-medium text-slate-700 mb-2">Quick suggestions:</p>
                  <div className="flex flex-wrap gap-2">
                    {['make it shorter', 'add benefits details', 'make it more formal'].map((suggestion) => (
                      <button
                        key={suggestion}
                        onClick={() => setImprovementText(suggestion)}
                        disabled={emailSent || isGenerating}
                        className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-sm transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {suggestion}
                      </button>
                    ))}
                  </div>
                </div>

                <button
                  onClick={handleImproveEmail}
                  disabled={!improvementText.trim() || emailSent || isGenerating}
                  className="w-full bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 disabled:from-slate-400 disabled:to-slate-500 text-white font-semibold py-3 px-6 rounded-xl transition-all duration-200 disabled:cursor-not-allowed flex items-center justify-center gap-2 shadow-lg hover:shadow-xl"
                >
                  {isGenerating ? (
                    <>
                      <svg className="w-5 h-5 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                      </svg>
                      Improving Email...
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

            {/* Send Email Button */}
            <div className="bg-white rounded-2xl shadow-xl border border-slate-200 p-6">
              <button
                onClick={handleSendEmail}
                disabled={emailSent}
                className={`w-full font-bold py-4 px-8 rounded-xl transition-all duration-300 flex items-center justify-center gap-3 text-lg shadow-lg hover:shadow-xl ${
                  emailSent
                    ? 'bg-green-100 text-green-800 border border-green-200 cursor-not-allowed'
                    : 'bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white transform hover:scale-[1.02]'
                }`}
              >
                {emailSent ? (
                  <>
                    <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                    Email Sent Successfully
                  </>
                ) : (
                  <>
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                    </svg>
                    Send Email
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Email Thread Viewer */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-2xl shadow-xl border border-slate-200 overflow-hidden h-fit">
              <div className="bg-gradient-to-r from-emerald-600 to-green-600 p-6">
                <h3 className="text-xl font-bold text-white flex items-center gap-3">
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clipRule="evenodd" />
                  </svg>
                  Gmail Thread Viewer
                </h3>
                <p className="text-emerald-100 mt-2">Live conversation updates</p>
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
                              {message.sender.charAt(0).toUpperCase()}
                            </div>
                            <div>
                              <p className="text-sm font-semibold text-slate-800">
                                {message.type === 'sent' ? 'You' : mockEmailData.context.candidateName}
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
                          Monitoring for new replies from {mockEmailData.context.candidateName}
                        </p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>

            {/* Action Summary */}
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
                    <p className="text-green-600 text-sm">Candidate outreach completed</p>
                  </div>
                </div>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-green-700">Recipient:</span>
                    <span className="font-medium text-green-800">{mockEmailData.to}</span>
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

export default EmailApprovalInterface;