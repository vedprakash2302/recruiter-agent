'use client'

import EmailApprovalQueue from '../../components/EmailApprovalQueue'

export default function QueuePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 p-4 md:p-6">
      <div className="max-w-7xl mx-auto">
        <EmailApprovalQueue />
      </div>
    </div>
  )
}