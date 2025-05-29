/**
 * Handyman Dashboard Jobs Management
 * Handles loading and interacting with job requests
 */
class JobsManager {
  constructor() {
    this.jobsContainer = document.querySelector('.jobs-container');
    this.pendingCountBadge = document.getElementById('pending-jobs-count');
    // Only use dummy data if specifically configured to do so
    this.useDummyData = window.USE_DUMMY_DATA === true; 
    this.initEventListeners();
  }

  /**
   * Initialize event listeners for job actions
   */
  initEventListeners() {
    // Use event delegation for job action buttons
    if (this.jobsContainer) {
      this.jobsContainer.addEventListener('click', (e) => {
        const actionBtn = e.target.closest('.job-action-btn');
        if (!actionBtn) return;
        
        const jobId = actionBtn.dataset.jobId;
        const action = actionBtn.dataset.action;
        
        if (action === 'accept' || action === 'decline') {
          this.updateJobStatus(jobId, action, actionBtn);
        } else if (actionBtn.classList.contains('details')) {
          this.showJobDetails(jobId);
        }
      });
    }
  }

  /**
   * Load job requests from the server
   */
  async loadJobRequests() {
    if (!this.jobsContainer) return;

    // If using dummy data and static content already exists, just update the pending count
    if (this.useDummyData && this.jobsContainer.querySelector('.job-card')) {
      // Extract job data from the static HTML
      const jobs = this.extractJobsFromDOM();
      this.updatePendingCount(jobs);
      return;
    }

    // If not using dummy data or no static content exists, show loading state
    this.jobsContainer.innerHTML = '<div class="loading"><i class="fas fa-spinner fa-spin"></i> Loading job requests...</div>';

    try {
      // If using dummy data, simulate a delay for a more realistic experience
      if (this.useDummyData) {
        await new Promise(resolve => setTimeout(resolve, 1000));
        // Return to existing static content or generate it dynamically
        const staticContent = document.createElement('div');
        staticContent.innerHTML = this.generateDummyJobs();
        this.jobsContainer.innerHTML = staticContent.innerHTML;
        const jobs = this.extractJobsFromDOM();
        this.updatePendingCount(jobs);
      } else {
        // Real API call
        const url = new URL(jobRequestsUrl);
        // Add timestamp to prevent caching
        url.searchParams.append('_', Date.now());
        
        const response = await fetch(url, {
          headers: { 
            'X-Requested-With': 'XMLHttpRequest',
            'Cache-Control': 'no-cache'
          }
        });

        if (!response.ok) {
          throw new Error(`Server responded with status: ${response.status}`);
        }

        const data = await response.json();
        
        // Render jobs
        this.renderJobs(data.jobs || []);
        
        // Update pending count
        this.updatePendingCount(data.jobs || []);
      }
    } catch (error) {
      console.error('Error loading jobs:', error);
      this.jobsContainer.innerHTML = `
        <div class="error">
          <i class="fas fa-exclamation-circle"></i> 
          Failed to load job requests. Please try again.
          <button class="retry-button" onclick="window.handymanDashboard.jobsManager.loadJobRequests()">
            <i class="fas fa-sync"></i> Retry
          </button>
        </div>
      `;
    }
  }

  /**
   * Render job cards in the container
   * @param {Array} jobs - Array of job objects
   */
  renderJobs(jobs) {
    if (!this.jobsContainer) return;

    if (!jobs || jobs.length === 0) {
      this.jobsContainer.innerHTML = `
        <div class="empty-jobs">
          <div class="empty-state-illustration">
            <i class="fas fa-briefcase"></i>
          </div>
          <h3>No job requests found</h3>
          <p>New job requests will appear here when customers contact you!</p>
        </div>
      `;
      return;
    }

    this.jobsContainer.innerHTML = jobs.map(job => this.createJobCard(job)).join('');
  }

  /**
   * Create HTML for a job card
   * @param {Object} job - Job object
   * @returns {string} HTML string for job card
   */
  createJobCard(job) {
    const statusClass = job.status.toLowerCase();
    const statusText = job.status.charAt(0).toUpperCase() + job.status.slice(1);
    
    return `
      <div class="job-card ${statusClass}">
        <div class="job-header">
          <div class="job-info">
            <h4>${job.service_name}</h4>
            <p class="client-name"><i class="fas fa-user"></i> ${job.client_name}</p>
          </div>
          <div class="job-status">
            <span class="status-badge ${statusClass}">${statusText}</span>
          </div>
        </div>
        <div class="job-details">
          <div class="job-detail-item">
            <i class="fas fa-calendar"></i>
            <span>${job.scheduled_date} at ${job.scheduled_time}</span>
          </div>
          <div class="job-detail-item">
            <i class="fas fa-map-marker-alt"></i>
            <span>${job.address}</span>
          </div>
          <div class="job-description">
            <p>${job.description}</p>
          </div>
        </div>
        <div class="job-actions">
          ${job.status === 'pending' ? `
            <button class="job-action-btn accept" data-job-id="${job.id}" data-action="accept">
              <i class="fas fa-check"></i> Accept
            </button>
            <button class="job-action-btn decline" data-job-id="${job.id}" data-action="decline">
              <i class="fas fa-times"></i> Decline
            </button>
          ` : ''}
          <button class="job-action-btn details" data-job-id="${job.id}">
            <i class="fas fa-info-circle"></i> Details
          </button>
        </div>
      </div>
    `;
  }

  /**
   * Update the pending jobs count badge
   * @param {Array} jobs - Array of job objects
   */
  updatePendingCount(jobs) {
    if (!this.pendingCountBadge) return;
    
    const pendingCount = jobs.filter(job => job.status === 'pending').length;
    this.pendingCountBadge.textContent = pendingCount;
    
    // Show/hide the badge based on count
    this.pendingCountBadge.style.display = pendingCount > 0 ? 'inline-flex' : 'none';
    
    // Update all other badges in the sidebar
    const sidebarBadges = document.querySelectorAll('.sidebar-tab-button .jobs-badge');
    sidebarBadges.forEach(badge => {
      badge.textContent = pendingCount;
      badge.style.display = pendingCount > 0 ? 'inline-flex' : 'none';
    });
  }

  /**
   * Update job status (accept/decline)
   * @param {number} jobId - ID of the job
   * @param {string} action - Action to perform (accept/decline)
   * @param {HTMLElement} button - Button element that was clicked
   */
  async updateJobStatus(jobId, action, button) {
    if (!jobId || !action) return;
    
    // Disable button and show loading
    const originalButtonText = button.innerHTML;
    button.disabled = true;
    button.innerHTML = `<i class="fas fa-spinner fa-spin"></i> ${action === 'accept' ? 'Accepting' : 'Declining'}...`;
    
    // Get all buttons in this job card
    const jobCard = button.closest('.job-card');
    const allButtons = jobCard.querySelectorAll('.job-action-btn');
    allButtons.forEach(btn => btn.disabled = true);
    
    try {
      // If using dummy data, simulate a delay and update the UI directly
      if (this.useDummyData) {
        await new Promise(resolve => setTimeout(resolve, 1500));
        
        // Simulate successful response
        const newStatus = action === 'accept' ? 'accepted' : 'declined';
        const message = action === 'accept' ? 'Job request accepted' : 'Job request declined';
        
        // Update the job card status
        jobCard.className = `job-card ${newStatus}`;
        const statusBadge = jobCard.querySelector('.status-badge');
        if (statusBadge) {
          statusBadge.className = `status-badge ${newStatus}`;
          statusBadge.textContent = newStatus.charAt(0).toUpperCase() + newStatus.slice(1);
        }
        
        // Remove accept/decline buttons
        const actionButtons = jobCard.querySelectorAll('.job-action-btn.accept, .job-action-btn.decline');
        actionButtons.forEach(btn => btn.remove());
        
        // Show success message
        showToast(message, 'success');
        
        // Update pending count
        const jobs = this.extractJobsFromDOM();
        this.updatePendingCount(jobs);
      } else {
        // Real API call
        const formData = new FormData();
        formData.append('job_id', jobId);
        formData.append('action', action);
        formData.append('csrfmiddlewaretoken', getCsrfToken());
        
        const response = await fetch(jobRequestsUrl, {
          method: 'POST',
          body: formData,
          headers: {
            'X-Requested-With': 'XMLHttpRequest'
          }
        });
        
        if (!response.ok) {
          throw new Error(`Server responded with status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.status === 'success') {
          // Show success message
          showToast(data.message, 'success');
          
          // Update the job card immediately for better UX
          const newStatus = action === 'accept' ? 'accepted' : 'declined';
          
          // Update the job card status
          jobCard.className = `job-card ${newStatus}`;
          const statusBadge = jobCard.querySelector('.status-badge');
          if (statusBadge) {
            statusBadge.className = `status-badge ${newStatus}`;
            statusBadge.textContent = newStatus.charAt(0).toUpperCase() + newStatus.slice(1);
          }
          
          // Remove accept/decline buttons
          const actionButtons = jobCard.querySelectorAll('.job-action-btn.accept, .job-action-btn.decline');
          actionButtons.forEach(btn => btn.remove());
          
          // Update pending count
          const jobs = this.extractJobsFromDOM();
          this.updatePendingCount(jobs);
        } else {
          // Show error message
          showToast(data.message || 'An error occurred', 'error');
          
          // Reset button state
          button.disabled = false;
          button.innerHTML = originalButtonText;
          allButtons.forEach(btn => btn.disabled = false);
        }
      }
    } catch (error) {
      console.error('Error updating job status:', error);
      showToast('An error occurred while updating job status', 'error');
      
      // Reset button state
      button.disabled = false;
      button.innerHTML = originalButtonText;
      allButtons.forEach(btn => btn.disabled = false);
    }
  }

  /**
   * Show detailed job information (placeholder for future implementation)
   * @param {number} jobId - ID of the job
   */
  showJobDetails(jobId) {
    // Placeholder for job details modal/popup
    // This would be implemented later to show more detailed job information
    console.log(`Show details for job ${jobId}`);
    showToast('Job details feature coming soon!', 'info');
  }

  /**
   * Extract job data from existing DOM elements
   * Used for dummy data mode to work with static HTML
   */
  extractJobsFromDOM() {
    const jobCards = this.jobsContainer.querySelectorAll('.job-card');
    const jobs = [];
    
    jobCards.forEach(card => {
      const id = card.querySelector('.job-action-btn')?.dataset.jobId || '0';
      const service_name = card.querySelector('.job-info h4')?.textContent || '';
      const client_name = card.querySelector('.client-name')?.textContent.replace(/^[\s\uFEFF\xA0\u200B\u2028\u2029]+|[\s\uFEFF\xA0\u200B\u2028\u2029]+$/g, '') || '';
      const status = card.classList.contains('pending') ? 'pending' :
                    card.classList.contains('accepted') ? 'accepted' :
                    card.classList.contains('completed') ? 'completed' : 
                    card.classList.contains('declined') ? 'declined' : 'unknown';
      
      jobs.push({
        id,
        service_name,
        client_name,
        status
      });
    });
    
    return jobs;
  }

  /**
   * Generate HTML for dummy jobs (as fallback)
   * Only used if no static HTML is present and we're in dummy data mode
   */
  generateDummyJobs() {
    return `
      <div class="job-card pending">
        <div class="job-header">
          <div class="job-info">
            <h4>Plumbing Repair</h4>
            <p class="client-name"><i class="fas fa-user"></i> John Smith</p>
          </div>
          <div class="job-status">
            <span class="status-badge pending">Pending</span>
          </div>
        </div>
        <div class="job-details">
          <div class="job-detail-item">
            <i class="fas fa-calendar"></i>
            <span>2025-06-15 at 10:00</span>
          </div>
          <div class="job-detail-item">
            <i class="fas fa-map-marker-alt"></i>
            <span>123 Main St, Anytown, CA</span>
          </div>
          <div class="job-description">
            <p>Leaking pipe under kitchen sink. Water is collecting in the cabinet below. Need urgent repair.</p>
          </div>
        </div>
        <div class="job-actions">
          <button class="job-action-btn accept" data-job-id="1" data-action="accept">
            <i class="fas fa-check"></i> Accept
          </button>
          <button class="job-action-btn decline" data-job-id="1" data-action="decline">
            <i class="fas fa-times"></i> Decline
          </button>
          <button class="job-action-btn details" data-job-id="1">
            <i class="fas fa-info-circle"></i> Details
          </button>
        </div>
      </div>
      
      <div class="job-card pending">
        <div class="job-header">
          <div class="job-info">
            <h4>Electrical Installation</h4>
            <p class="client-name"><i class="fas fa-user"></i> Mary Johnson</p>
          </div>
          <div class="job-status">
            <span class="status-badge pending">Pending</span>
          </div>
        </div>
        <div class="job-details">
          <div class="job-detail-item">
            <i class="fas fa-calendar"></i>
            <span>2025-06-18 at 14:00</span>
          </div>
          <div class="job-detail-item">
            <i class="fas fa-map-marker-alt"></i>
            <span>456 Oak Ave, Anytown, CA</span>
          </div>
          <div class="job-description">
            <p>Install new light fixtures in living room. Three ceiling lights need to be replaced. Customer has purchased the fixtures already.</p>
          </div>
        </div>
        <div class="job-actions">
          <button class="job-action-btn accept" data-job-id="2" data-action="accept">
            <i class="fas fa-check"></i> Accept
          </button>
          <button class="job-action-btn decline" data-job-id="2" data-action="decline">
            <i class="fas fa-times"></i> Decline
          </button>
          <button class="job-action-btn details" data-job-id="2">
            <i class="fas fa-info-circle"></i> Details
          </button>
        </div>
      </div>
    `;
  }
}

/**
 * Helper function to get CSRF token
 * @returns {string} CSRF token
 */
function getCsrfToken() {
  return document.querySelector('[name=csrfmiddlewaretoken]').value;
}

/**
 * Helper function to show toast notifications
 * @param {string} message - Notification message
 * @param {string} type - Notification type (success, error, info)
 */
function showToast(message, type = 'info') {
  // Check if dashboard has a showToast method already
  if (typeof window.dashboard !== 'undefined' && typeof window.dashboard.showToast === 'function') {
    window.dashboard.showToast(message, type);
  } else {
    console.log(`${type.toUpperCase()}: ${message}`);
  }
}

// Export the JobsManager class for use in the main dashboard
window.JobsManager = JobsManager; 