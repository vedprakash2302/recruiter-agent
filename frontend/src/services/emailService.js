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
      const response = await fetch(`${API_BASE_URL}/improve`, {
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

  // Improve email with streaming using Groq LLM
  static async improveEmailStream(emailContent, improvementRequest, context = {}, callbacks = {}) {
    try {
      const response = await fetch(`${API_BASE_URL}/improve/stream`, {
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

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      try {
        while (true) {
          const { done, value } = await reader.read();
          
          if (done) break;
          
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          
          // Keep the last incomplete line in buffer
          buffer = lines.pop() || '';
          
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6));
                
                switch (data.type) {
                  case 'status':
                    callbacks.onStatus?.(data.message);
                    break;
                  case 'chunk':
                    callbacks.onChunk?.(data.content, data.accumulated);
                    break;
                  case 'complete':
                    callbacks.onComplete?.(data.final_content, data);
                    return data;
                  case 'error':
                    callbacks.onError?.(new Error(data.error));
                    throw new Error(data.error);
                }
              } catch (parseError) {
                console.warn('Failed to parse SSE data:', line, parseError);
              }
            }
          }
        }
      } finally {
        reader.releaseLock();
      }
      
    } catch (error) {
      console.error('Error in streaming email improvement:', error);
      callbacks.onError?.(error);
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
      const response = await fetch(`${API_BASE_URL}/send-email/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          to: emailData.to,
          subject: emailData.subject,
          message: emailData.content,
          sender: "me"
        }),
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
      const response = await fetch(`${API_BASE_URL}/emails/thread/${emailId}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error fetching email thread:', error);
      throw error;
    }
  }

  // Analyse resume using the new analyse endpoint
  static async analyseResume(filename) {
    try {
      const formData = new FormData();
      formData.append('filename', filename);

      const response = await fetch(`${API_BASE_URL}/analyse`, {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error analysing resume:', error);
      throw error;
    }
  }
}

export default EmailService;