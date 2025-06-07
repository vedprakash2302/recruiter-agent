// Email API Service - Connects frontend to Groq-powered backend
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class EmailService {
  // Generate email using Groq LLM
  static async generateEmail(emailRequest) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/email/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(emailRequest),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error generating email:', error);
      throw error;
    }
  }

  // Improve email using Groq LLM
  static async improveEmail(emailContent, improvementRequest, context = {}) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/email/improve`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email_content: emailContent,
          improvement_request: improvementRequest,
          context
        }),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error improving email:', error);
      throw error;
    }
  }

  // Submit email for approval queue
  static async submitForApproval(emailData) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/email/pending`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(emailData),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error submitting email for approval:', error);
      throw error;
    }
  }

  // Get pending emails
  static async getPendingEmails() {
    try {
      const response = await fetch(`${API_BASE_URL}/api/email/pending`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error fetching pending emails:', error);
      throw error;
    }
  }

  // Approve or reject email
  static async approveEmail(emailId, approved) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/email/approve`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          id: emailId,
          approved
        }),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error approving email:', error);
      throw error;
    }
  }

  // Send approved email
  static async sendEmail(emailData) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/email/send`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(emailData),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error sending email:', error);
      throw error;
    }
  }

  // Get email thread/conversation
  static async getEmailThread(emailId) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/email/thread/${emailId}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error fetching email thread:', error);
      throw error;
    }
  }
}

export default EmailService;