'use client'

import React, { useState, useRef, useEffect } from 'react';

// AI Recruiter Email Approval Interface Component
const AIRecruiterEmailInterface = () => {
  // State management
  const [emailData, setEmailData] = useState({
    to: "candidate@techcompany.com",
    subject: "Exciting Opportunity - Senior Developer Position",
    content: `Dear [Candidate Name],

I hope this message finds you well. I came across your impressive profile and would like to discuss an exciting opportunity that aligns perfectly with your expertise.

We have an exceptional Senior Developer position at our innovative tech company that I believe would be an ideal match for your skills and career aspirations.

Key highlights of this role:
• Lead development of cutting-edge applications
• Work with modern tech stack (React, Node.js, AWS)
• Competitive salary and comprehensive benefits
• Remote-first culture with flexible work arrangements
• Opportunity to mentor junior developers and drive technical decisions

Your background in full-stack development and experience with scalable systems makes you an ideal candidate for this position.

Would you be interested in scheduling a brief call to discuss this opportunity further? I'd love to learn more about your current goals and how this role might fit into your career trajectory.

Best regards,
Alex Rivera
Senior Technical Recruiter
InnovateTech Solutions`,
    candidateInfo: {
      name: "Jordan Smith",
      currentCompany: "TechCorp Inc.",
      position: "Full Stack Developer",
      skills: ["React", "Node.js", "Python", "AWS", "Docker"]
    }
  });

  const [improvementRequest, setImprovementRequest] = useState('');
  const [isImproving, setIsImproving] = useState(false);
  const [emailSent, setEmailSent] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [showThread, setShowThread] = useState(false);
  const [emailThread, setEmailThread] = useState([]);
  
  const improvementInputRef = useRef(null);

  // Mock email thread data
  const mockThreadData = [
    {
      id: 1,
      sender: "alex.rivera@innovatetech.com",
      recipient: emailData.to,
      timestamp: new Date().toISOString(),
      content: "Initial recruitment email sent",
      type: "sent",
      status: "delivered"
    },
    {
      id: 2,
      sender: emailData.to,
      recipient: "alex.rivera@innovatetech.com", 
      timestamp: new Date(Date.now() + 3600000).toISOString(),
      content: "Hi Alex, thank you for reaching out! This opportunity sounds very interesting. I'd love to learn more about the team structure and the specific projects I'd be working on. When would be a good time for a call?",
      type: "received",
      status: "read"
    }
  ];

  // Handle AI-powered email improvement
  const handleImproveEmail = async () => {
    if (!improvementRequest.trim() || isImproving || emailSent) return;

    setIsImproving(true);
    
    // Simulate LangGraph AI processing
    await new Promise(resolve => setTimeout(resolve, 2500));

    let improvedContent = emailData.content;

    // Mock improvement logic based on user request
    if (improvementRequest.toLowerCase().includes('shorter')) {
      improvedContent = `Dear ${emailData.candidateInfo.name},

I came across your impressive profile at ${emailData.candidateInfo.currentCompany} and have an exciting Senior Developer opportunity that matches your expertise perfectly.

Key highlights:
• Lead cutting-edge application development
• Modern tech stack: React, Node.js, AWS
• Competitive package + remote-first culture
• Mentorship and technical leadership opportunities

Your full-stack development experience makes you an ideal fit. Interested in a quick call to discuss?

Best regards,
Alex Rivera
Senior Technical Recruiter`;
    } else if (improvementRequest.toLowerCase().includes('formal')) {
      improvedContent = improvedContent.replace(
        'I hope this message finds you well.',
        'I trust this correspondence finds you in excellent health and spirits.'
      ).replace(
        'Would you be interested in scheduling a brief call',
        'I would be honored to schedule a formal consultation'
      );
    } else if (improvementRequest.toLowerCase().includes('personal')) {
      improvedContent = improvedContent.replace(
        '[Candidate Name]',
        emailData.candidateInfo.name
      ).replace(
        'your expertise',
        `your ${emailData.candidateInfo.skills.slice(0, 2).join(' and ')} expertise`
      );
    } else if (improvementRequest.toLowerCase().includes('salary') || improvementRequest.toLowerCase().includes('compensation')) {
      improvedContent = improvedContent.replace(
        'Competitive salary and comprehensive benefits',
        'Competitive salary ($120K-160K) with equity, comprehensive health benefits, 4 weeks PTO, and $3K annual learning budget'
      );
    }

    setEmailData(prev => ({ ...prev, content: improvedContent }));
    setImprovementRequest('');
    setIsImproving(false);
  };

  // Handle email sending
  const handleSendEmail = async () => {
    if (emailSent || isSending) return;

    setIsSending(true);
    
    // Simulate email sending process
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    setEmailSent(true);
    setIsSending(false);
    
    // Show Gmail thread after sending
    setTimeout(() => {
      setEmailThread(mockThreadData);
      setShowThread(true);
    }, 1500);
  };

  // Format timestamp for display
  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // Quick improvement suggestions
  const quickSuggestions = [
    'make it shorter and more concise',
    'add specific salary details', 
    'make it more personal and engaging',
    'use more formal language'
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-purple-50 to-blue-50 p-6">
      <div className="max-w-7xl mx-auto space-y-8">
        
        {/* Header Section */}
        <div className="bg-white rounded-3xl shadow-2xl border border-slate-200 p-8">
          <div className="flex items-center gap-6 mb-8">
            <div className="w-16 h-16 bg-gradient-to-r from-purple-600 via-blue-600 to-indigo-600 rounded-2xl flex items-center justify-center shadow-xl">
              <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 3.26a2 2 0 001.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
            </div>
            <div>
              <h1 className="text-4xl font-black bg-gradient-to-r from-slate-800 via-purple-700 to-blue-700 bg-clip-text text-transparent">
                AI Recruiter Agent
              </h1>
              <p className="text-slate-600 text-lg font-semibold mt-2">Email Approval & Management Interface</p>
            </div>
          </div>

          {/* Candidate Information Card */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            <div className="bg-gradient-to-r from-slate-50 to-slate-100 rounded-2xl p-6 border border-slate-200">
              <h3 className="text-lg font-bold text-slate-800 mb-4 flex items-center gap-2">
                <svg className="w-5 h-5 text-purple-600" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
                </svg>
                Candidate Profile
              </h3>
              <div className="space-y-3">
                <div>
                  <label className="text-sm font-semibold text-slate-600">Name</label>
                  <p className="text-slate-900 font-bold">{emailData.candidateInfo.name}</p>
                </div>
                <div>
                  <label className="text-sm font-semibold text-slate-600">Current Position</label>
                  <p className="text-slate-900">{emailData.candidateInfo.position} at {emailData.candidateInfo.currentCompany}</p>
                </div>
              </div>
            </div>
            
            <div className="bg-gradient-to-r from-slate-50 to-slate-100 rounded-2xl p-6 border border-slate-200">
              <h3 className="text-lg font-bold text-slate-800 mb-4 flex items-center gap-2">
                <svg className="w-5 h-5 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M3 8l7.89 3.26a2 2 0 001.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
                Email Details
              </h3>
              <div className="space-y-3">
                <div>
                  <label className="text-sm font-semibold text-slate-600">To</label>
                  <p className="text-slate-900 font-medium">{emailData.to}</p>
                </div>
                <div>
                  <label className="text-sm font-semibold text-slate-600">Subject</label>
                  <p className="text-slate-900">{emailData.subject}</p>
                </div>
              </div>
            </div>
          </div>

          {/* Skills Tags */}
          <div>
            <h3 className="text-lg font-bold text-slate-800 mb-4">Technical Skills</h3>
            <div className="flex flex-wrap gap-3">
              {emailData.candidateInfo.skills.map((skill, index) => (
                <span 
                  key={index}
                  className="px-4 py-2 bg-gradient-to-r from-purple-100 to-blue-100 text-purple-800 rounded-full text-sm font-bold border border-purple-200 shadow-sm hover:shadow-md transition-shadow duration-200"
                >
                  {skill}
                </span>
              ))}
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
          
          {/* Email Content & Controls */}
          <div className="xl:col-span-2 space-y-8">
            
            {/* Email Content Editor */}
            <div className="bg-white rounded-3xl shadow-2xl border border-slate-200 overflow-hidden">
              <div className="bg-gradient-to-r from-slate-900 via-slate-800 to-slate-700 p-8">
                <h2 className="text-2xl font-black text-white flex items-center gap-3">
                  <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M2.003 5.884L10 9.882l7.997-3.998A2 2 0 0016 4H4a2 2 0 00-1.997 1.884z" />
                    <path d="M18 8.118l-8 4-8-4V14a2 2 0 002 2h12a2 2 0 002-2V8.118z" />
                  </svg>
                  AI-Generated Email Content
                </h2>
                <p className="text-slate-300 mt-2 font-medium">Review and edit the email before sending</p>
              </div>
              <div className="p-8">
                <textarea
                  value={emailData.content}
                  onChange={(e) => setEmailData(prev => ({ ...prev, content: e.target.value }))}
                  className="w-full h-96 p-6 border-2 border-slate-200 rounded-2xl resize-none focus:ring-4 focus:ring-purple-500/20 focus:border-purple-500 transition-all duration-300 text-slate-700 leading-relaxed text-base font-medium"
                  placeholder="AI-generated email content will appear here..."
                  disabled={emailSent}
                />
              </div>
            </div>

            {/* Email Improvement Assistant */}
            <div className="bg-white rounded-3xl shadow-2xl border border-slate-200 overflow-hidden">
              <div className="bg-gradient-to-r from-purple-600 via-indigo-600 to-blue-600 p-8">
                <h3 className="text-2xl font-black text-white flex items-center gap-3">
                  <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clipRule="evenodd" />
                  </svg>
                  LangGraph AI Improvement Engine
                </h3>
                <p className="text-purple-100 mt-2 font-medium">Request specific improvements to enhance your email</p>
              </div>
              <div className="p-8">
                <div className="mb-6">
                  <textarea
                    ref={improvementInputRef}
                    value={improvementRequest}
                    onChange={(e) => setImprovementRequest(e.target.value)}
                    placeholder="Describe how you'd like to improve the email (e.g., 'make it shorter', 'add salary details', 'make it more personal')..."
                    className="w-full h-32 p-6 border-2 border-slate-200 rounded-2xl resize-none focus:ring-4 focus:ring-purple-500/20 focus:border-purple-500 transition-all duration-300 text-slate-700 font-medium"
                    disabled={emailSent || isImproving}
                  />
                </div>
                
                {/* Quick Improvement Suggestions */}
                <div className="mb-6">
                  <p className="text-sm font-bold text-slate-700 mb-3">Quick Suggestions:</p>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {quickSuggestions.map((suggestion, index) => (
                      <button
                        key={index}
                        onClick={() => setImprovementRequest(suggestion)}
                        disabled={emailSent || isImproving}
                        className="px-4 py-3 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-sm font-semibold transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed hover:shadow-md"
                      >
                        {suggestion}
                      </button>
                    ))}
                  </div>
                </div>

                <button
                  onClick={handleImproveEmail}
                  disabled={!improvementRequest.trim() || emailSent || isImproving}
                  className="w-full bg-gradient-to-r from-purple-600 via-indigo-600 to-blue-600 hover:from-purple-700 hover:via-indigo-700 hover:to-blue-700 disabled:from-slate-400 disabled:to-slate-500 text-white font-black py-4 px-8 rounded-2xl transition-all duration-300 disabled:cursor-not-allowed flex items-center justify-center gap-3 text-lg shadow-xl hover:shadow-2xl transform hover:scale-[1.02]"
                >
                  {isImproving ? (
                    <>
                      <svg className="w-6 h-6 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                      </svg>
                      AI Processing...
                    </>
                  ) : (
                    <>
                      <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clipRule="evenodd" />
                      </svg>
                      Improve with AI
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* Send Email Button */}
            <div className="bg-white rounded-3xl shadow-2xl border border-slate-200 p-8">
              <button
                onClick={handleSendEmail}
                disabled={emailSent || isSending}
                className={`w-full font-black py-6 px-10 rounded-2xl transition-all duration-300 flex items-center justify-center gap-4 text-xl shadow-xl hover:shadow-2xl transform hover:scale-[1.02] ${
                  emailSent
                    ? 'bg-gradient-to-r from-green-100 to-emerald-100 text-green-800 border-2 border-green-200 cursor-not-allowed'
                    : isSending
                    ? 'bg-gradient-to-r from-blue-500 to-blue-600 text-white cursor-wait'
                    : 'bg-gradient-to-r from-green-600 via-emerald-600 to-green-700 hover:from-green-700 hover:via-emerald-700 hover:to-green-800 text-white'
                }`}
              >
                {emailSent ? (
                  <>
                    <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                    Email Sent Successfully!
                  </>
                ) : isSending ? (
                  <>
                    <svg className="w-8 h-8 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                    </svg>
                    Sending Email...
                  </>
                ) : (
                  <>
                    <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                    </svg>
                    Send Email
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Gmail Thread Viewer */}
          <div className="xl:col-span-1">
            <div className="bg-white rounded-3xl shadow-2xl border border-slate-200 overflow-hidden h-fit">
              <div className="bg-gradient-to-r from-emerald-600 via-green-600 to-teal-600 p-8">
                <h3 className="text-2xl font-black text-white flex items-center gap-3">
                  <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clipRule="evenodd" />
                  </svg>
                  Gmail Thread
                </h3>
                <p className="text-emerald-100 mt-2 font-medium">Live conversation monitoring</p>
              </div>

              <div className="p-8">
                {!showThread && !emailSent ? (
                  <div className="text-center py-16">
                    <svg className="w-20 h-20 mx-auto text-slate-300 mb-6" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clipRule="evenodd" />
                    </svg>
                    <p className="text-slate-500 font-bold text-lg">No Conversation Yet</p>
                    <p className="text-slate-400 mt-2">Thread will appear after sending email</p>
                  </div>
                ) : (
                  <div className="space-y-6">
                    {emailThread.map((message) => (
                      <div
                        key={message.id}
                        className={`p-6 rounded-2xl border-2 transition-all duration-300 hover:shadow-lg ${
                          message.type === 'sent'
                            ? 'bg-blue-50 border-blue-200 ml-6 shadow-blue-100'
                            : 'bg-green-50 border-green-200 mr-6 shadow-green-100'
                        }`}
                      >
                        <div className="flex items-start justify-between mb-4">
                          <div className="flex items-center gap-3">
                            <div className={`w-10 h-10 rounded-full flex items-center justify-center text-white text-sm font-black shadow-lg ${
                              message.type === 'sent' ? 'bg-blue-600' : 'bg-green-600'
                            }`}>
                              {message.sender.charAt(0).toUpperCase()}
                            </div>
                            <div>
                              <p className="text-sm font-black text-slate-800">
                                {message.type === 'sent' ? 'You' : emailData.candidateInfo.name}
                              </p>
                              <p className="text-xs text-slate-500 font-semibold">{formatTimestamp(message.timestamp)}</p>
                            </div>
                          </div>
                          <div className={`px-3 py-1 rounded-full text-xs font-bold ${
                            message.type === 'sent'
                              ? 'bg-blue-100 text-blue-800'
                              : 'bg-green-100 text-green-800'
                          }`}>
                            {message.type === 'sent' ? 'Sent' : 'Received'}
                          </div>
                        </div>
                        <p className="text-slate-700 leading-relaxed font-medium">{message.content}</p>
                      </div>
                    ))}

                    {showThread && (
                      <div className="border-t-2 border-slate-200 pt-6 mt-8">
                        <div className="flex items-center gap-3 text-green-600 mb-3">
                          <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                          <p className="font-bold">Active Monitoring</p>
                        </div>
                        <p className="text-xs text-slate-500 font-medium">
                          Watching for new replies from {emailData.candidateInfo.name}
                        </p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>

            {/* Email Status Summary */}
            {emailSent && (
              <div className="mt-8 bg-gradient-to-r from-green-50 to-emerald-50 border-2 border-green-200 rounded-3xl p-8 shadow-xl">
                <div className="flex items-center gap-4 mb-6">
                  <div className="w-12 h-12 bg-green-600 rounded-2xl flex items-center justify-center shadow-lg">
                    <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div>
                    <h4 className="font-black text-green-800 text-lg">Mission Accomplished!</h4>
                    <p className="text-green-600 font-semibold">Recruitment email successfully delivered</p>
                  </div>
                </div>
                <div className="space-y-3 text-sm font-semibold">
                  <div className="flex justify-between">
                    <span className="text-green-700">Recipient:</span>
                    <span className="text-green-800">{emailData.to}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-green-700">Delivered:</span>
                    <span className="text-green-800">{formatTimestamp(new Date().toISOString())}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-green-700">Status:</span>
                    <span className="text-green-800">✓ Delivered & Monitored</span>
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

export default AIRecruiterEmailInterface;