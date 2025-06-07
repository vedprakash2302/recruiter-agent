'use client'

import React, { useEffect, useState } from 'react';
import EmailService from '../services/emailService';

export const EmailApprovalQueue = ({ onEmailSelect = null, autoRefresh = true }) => {
  const [pendingEmails, setPendingEmails] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [processingIds, setProcessingIds] = useState(new Set());

  const fetchPendingEmails = async () => {
    try {
      setError(null);
      const result = await EmailService.getPendingEmails();
      setPendingEmails(result.pending_emails || []);
    } catch (error) {
      console.error('Error fetching pending emails:', error);
      setError('Failed to load pending emails: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPendingEmails();
    
    if (autoRefresh) {
      // Polling every 10 seconds for new emails
      const interval = setInterval(fetchPendingEmails, 10000);
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  const handleApproval = async (emailId, approved) => {
    if (processingIds.has(emailId)) return;

    setProcessingIds(prev => new Set(prev).add(emailId));
    
    try {
      await EmailService.approveEmail(emailId, approved);
      
      // Remove the approved/rejected email from the list
      setPendingEmails(prev => prev.filter(email => email.id !== emailId));
      
      // Show success message briefly
      const action = approved ? 'approved' : 'rejected';
      console.log(`Email ${emailId} ${action} successfully`);
      
    } catch (error) {
      console.error('Error updating email approval:', error);
      setError(`Failed to ${approved ? 'approve' : 'reject'} email: ${error.message}`);
    } finally {
      setProcessingIds(prev => {
        const newSet = new Set(prev);
        newSet.delete(emailId);
        return newSet;
      });
    }
  };

  const handleEmailClick = (email) => {
    if (onEmailSelect) {
      onEmailSelect(email);
    }
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

  const truncateContent = (content, maxLength = 150) => {
    if (content.length <= maxLength) return content;
    return content.substring(0, maxLength) + '...';
  };

  if (loading) {
    return (
      <div className="bg-white rounded-2xl shadow-xl border border-slate-200 p-8">
        <div className="flex justify-center items-center py-12">
          <div className="flex items-center gap-3">
            <svg className="w-6 h-6 animate-spin text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            <span className="text-slate-600 font-medium">Loading pending emails...</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl shadow-xl border border-slate-200 overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-orange-600 to-red-600 p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            <h2 className="text-xl font-bold text-white">Email Approval Queue</h2>
          </div>
          <div className="flex items-center gap-2">
            <span className="px-3 py-1 bg-white/20 rounded-full text-white text-sm font-medium">
              {pendingEmails.length} pending
            </span>
            <button
              onClick={fetchPendingEmails}
              disabled={loading}
              className="p-2 bg-white/20 hover:bg-white/30 rounded-lg transition-colors duration-200"
              title="Refresh"
            >
              <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </button>
          </div>
        </div>
        {autoRefresh && (
          <p className="text-orange-100 text-sm mt-2">Auto-refreshing every 10 seconds</p>
        )}
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border-l-4 border-red-400 p-4 m-6 rounded">
          <div className="flex items-center">
            <svg className="w-5 h-5 text-red-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
            <span className="text-red-800 font-medium">{error}</span>
          </div>
        </div>
      )}

      {/* Content */}
      <div className="p-6">
        {pendingEmails.length === 0 ? (
          <div className="text-center py-12">
            <svg className="w-16 h-16 mx-auto text-slate-300 mb-4" fill="currentColor" viewBox="0 0 20 20">
              <path d="M2.003 5.884L10 9.882l7.997-3.998A2 2 0 0016 4H4a2 2 0 00-1.997 1.884z" />
              <path d="M18 8.118l-8 4-8-4V14a2 2 0 002 2h12a2 2 0 002-2V8.118z" />
            </svg>
            <p className="text-slate-500 font-medium text-lg">No pending emails</p>
            <p className="text-slate-400 text-sm mt-1">All emails have been processed</p>
          </div>
        ) : (
          <div className="space-y-4">
            {pendingEmails.map((email) => {
              const isProcessing = processingIds.has(email.id);
              const candidateInfo = email.metadata?.candidateInfo || {};
              const jobInfo = email.metadata?.jobInfo || {};
              
              return (
                <div 
                  key={email.id} 
                  className={`border rounded-xl p-6 bg-gradient-to-r from-slate-50 to-slate-100 shadow-sm hover:shadow-md transition-all duration-200 ${
                    onEmailSelect ? 'cursor-pointer hover:from-blue-50 hover:to-indigo-50' : ''
                  } ${isProcessing ? 'opacity-50' : ''}`}
                  onClick={() => handleEmailClick(email)}
                >
                  {/* Email Header */}
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <div className="w-8 h-8 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-full flex items-center justify-center">
                          <span className="text-white text-sm font-bold">
                            {candidateInfo.name?.charAt(0)?.toUpperCase() || email.to?.charAt(0)?.toUpperCase() || 'U'}
                          </span>
                        </div>
                        <div>
                          <h3 className="font-bold text-slate-800">
                            {candidateInfo.name || 'Unknown Candidate'}
                          </h3>
                          <p className="text-sm text-slate-600">
                            {candidateInfo.position || 'Position not specified'} 
                            {candidateInfo.currentCompany && ` at ${candidateInfo.currentCompany}`}
                          </p>
                        </div>
                      </div>
                      
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                        <div>
                          <span className="text-sm font-semibold text-slate-700">To:</span>
                          <p className="text-slate-900">{email.to}</p>
                        </div>
                        <div>
                          <span className="text-sm font-semibold text-slate-700">Job:</span>
                          <p className="text-slate-900">
                            {jobInfo.title || 'Job not specified'}
                            {jobInfo.company && ` at ${jobInfo.company}`}
                          </p>
                        </div>
                      </div>
                    </div>
                    
                    <div className="text-right ml-4">
                      <p className="text-xs text-slate-500">Created</p>
                      <p className="text-sm font-medium text-slate-700">
                        {formatTimestamp(email.created_at)}
                      </p>
                    </div>
                  </div>

                  {/* Skills */}
                  {candidateInfo.skills && candidateInfo.skills.length > 0 && (
                    <div className="mb-4">
                      <p className="text-sm font-semibold text-slate-700 mb-2">Skills:</p>
                      <div className="flex flex-wrap gap-2">
                        {candidateInfo.skills.slice(0, 5).map((skill, index) => (
                          <span 
                            key={index}
                            className="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs font-medium"
                          >
                            {skill}
                          </span>
                        ))}
                        {candidateInfo.skills.length > 5 && (
                          <span className="px-2 py-1 bg-slate-100 text-slate-600 rounded-full text-xs">
                            +{candidateInfo.skills.length - 5} more
                          </span>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Subject */}
                  <div className="mb-4">
                    <span className="text-sm font-semibold text-slate-700">Subject:</span>
                    <p className="text-slate-900 font-medium">{email.subject}</p>
                  </div>

                  {/* Content Preview */}
                  <div className="mb-6">
                    <span className="text-sm font-semibold text-slate-700 block mb-2">Content Preview:</span>
                    <div className="bg-white rounded-lg p-4 border border-slate-200">
                      <p className="text-slate-700 text-sm leading-relaxed">
                        {truncateContent(email.content)}
                      </p>
                      {email.content.length > 150 && (
                        <button 
                          className="text-blue-600 hover:text-blue-800 text-sm font-medium mt-2"
                          onClick={(e) => {
                            e.stopPropagation();
                            // Could implement a modal or expand functionality here
                          }}
                        >
                          View full content →
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="flex space-x-3">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleApproval(email.id, true);
                      }}
                      disabled={isProcessing}
                      className={`flex-1 px-4 py-3 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white rounded-lg font-semibold transition-all duration-200 flex items-center justify-center gap-2 shadow-lg hover:shadow-xl ${
                        isProcessing ? 'opacity-50 cursor-not-allowed' : ''
                      }`}
                    >
                      {isProcessing ? (
                        <>
                          <svg className="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                          </svg>
                          Processing...
                        </>
                      ) : (
                        <>
                          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                          </svg>
                          Approve & Send
                        </>
                      )}
                    </button>
                    
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleApproval(email.id, false);
                      }}
                      disabled={isProcessing}
                      className={`flex-1 px-4 py-3 bg-gradient-to-r from-red-600 to-pink-600 hover:from-red-700 hover:to-pink-700 text-white rounded-lg font-semibold transition-all duration-200 flex items-center justify-center gap-2 shadow-lg hover:shadow-xl ${
                        isProcessing ? 'opacity-50 cursor-not-allowed' : ''
                      }`}
                    >
                      {isProcessing ? (
                        <>
                          <svg className="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                          </svg>
                          Processing...
                        </>
                      ) : (
                        <>
                          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                          </svg>
                          Reject
                        </>
                      )}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default EmailApprovalQueue;