import React, { useEffect, useState } from 'react';
import axios from 'axios';

interface PendingEmail {
  id: string;
  to: string;
  subject: string;
  content: string;
  created_at: string;
}

export const EmailApprovalQueue: React.FC = () => {
  const [pendingEmails, setPendingEmails] = useState<PendingEmail[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchPendingEmails = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/email/pending');
      setPendingEmails(response.data.pending_emails);
    } catch (error) {
      console.error('Error fetching pending emails:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPendingEmails();
    // Polling every 10 seconds for new emails
    const interval = setInterval(fetchPendingEmails, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleApproval = async (emailId: string, approved: boolean) => {
    try {
      await axios.post('http://localhost:8000/api/email/approve', {
        id: emailId,
        approved
      });
      // Remove the approved/rejected email from the list
      setPendingEmails(pendingEmails.filter(email => email.id !== emailId));
    } catch (error) {
      console.error('Error updating email approval:', error);
    }
  };

  if (loading) {
    return <div className="flex justify-center items-center p-4">Loading...</div>;
  }

  return (
    <div className="container mx-auto p-4">
      <h2 className="text-2xl font-bold mb-4">Pending Email Approvals</h2>
      {pendingEmails.length === 0 ? (
        <p className="text-gray-500">No pending emails</p>
      ) : (
        <div className="space-y-4">
          {pendingEmails.map((email) => (
            <div key={email.id} className="border rounded-lg p-4 bg-white shadow">
              <div className="mb-2">
                <span className="font-semibold">To:</span> {email.to}
              </div>
              <div className="mb-2">
                <span className="font-semibold">Subject:</span> {email.subject}
              </div>
              <div className="mb-4">
                <span className="font-semibold">Content:</span>
                <p className="mt-1 text-gray-600">{email.content}</p>
              </div>
              <div className="flex space-x-2">
                <button
                  onClick={() => handleApproval(email.id, true)}
                  className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
                >
                  Approve
                </button>
                <button
                  onClick={() => handleApproval(email.id, false)}
                  className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
                >
                  Reject
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
