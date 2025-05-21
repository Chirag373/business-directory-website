document.addEventListener('DOMContentLoaded', function() {
  // Initialize tabs
  initTabs();
  
  // Initialize business card flip
  initBusinessCard();
  
  // Initialize mobile sidebar
  initMobileSidebar();
  
  // Initialize form interactions
  initFormInteractions();
  
  // Initialize countdown timer
  initCountdownTimer();
  
  // Only initialize overview chart on load
  const overviewChart = document.getElementById('performance-chart');
  if (overviewChart) {
    renderOverviewChart(overviewChart);
  }
});

/**
 * Initialize tab navigation
 */
function initTabs() {
  const tabButtons = document.querySelectorAll('.tab-button');
  const sidebarTabButtons = document.querySelectorAll('.sidebar-tab-button');
  const sections = document.querySelectorAll('.dashboard-content');
  
  // Track if performance charts have been initialized
  let performanceChartsInitialized = false;
  
  function setActiveTab(tabId) {
    // Remove active class from all tabs and sections
    tabButtons.forEach(tab => tab.classList.remove('active'));
    sidebarTabButtons.forEach(tab => tab.classList.remove('active'));
    sections.forEach(section => section.classList.remove('active'));
    
    // Add active class to clicked tab and corresponding section
    document.querySelectorAll(`.tab-button[data-tab="${tabId}"]`).forEach(tab => tab.classList.add('active'));
    document.querySelectorAll(`.sidebar-tab-button[data-tab="${tabId}"]`).forEach(tab => tab.classList.add('active'));
    
    const activeSection = document.getElementById(`${tabId}-section`);
    activeSection.classList.add('active');
    
    // If performance tab is activated, render all charts
    if (tabId === 'performance') {
      // Only initialize charts once
      if (!performanceChartsInitialized) {
        setTimeout(function() {
          renderAllPerformanceCharts();
          performanceChartsInitialized = true;
        }, 300);
      }
    }
  }
  
  // Add click event to tab buttons
  tabButtons.forEach(button => {
    button.addEventListener('click', function() {
      const tabId = this.getAttribute('data-tab');
      setActiveTab(tabId);
    });
  });
  
  // Add click event to sidebar tab buttons
  sidebarTabButtons.forEach(button => {
    button.addEventListener('click', function() {
      const tabId = this.getAttribute('data-tab');
      setActiveTab(tabId);
      closeSidebar();
    });
  });
}

/**
 * Initialize business card flip functionality
 */
function initBusinessCard() {
  const cardWrapper = document.getElementById('business-card-wrapper');
  const flipButton = document.getElementById('flip-card-btn');
  
  if (cardWrapper && flipButton) {
    flipButton.addEventListener('click', function() {
      cardWrapper.classList.toggle('flipped');
    });
  }
}

/**
 * Initialize mobile sidebar
 */
function initMobileSidebar() {
  const hamburgerButton = document.querySelector('.dashboard-hamburger');
  const closeButton = document.querySelector('.close-sidebar');
  const sidebar = document.querySelector('.dashboard-sidebar');
  const overlay = document.querySelector('.dashboard-overlay');
  
  function openSidebar() {
    sidebar.classList.add('active');
    overlay.classList.add('active');
    document.body.style.overflow = 'hidden';
  }
  
  function closeSidebar() {
    sidebar.classList.remove('active');
    overlay.classList.remove('active');
    document.body.style.overflow = '';
  }
  
  if (hamburgerButton) {
    hamburgerButton.addEventListener('click', openSidebar);
  }
  
  if (closeButton) {
    closeButton.addEventListener('click', closeSidebar);
  }
  
  if (overlay) {
    overlay.addEventListener('click', closeSidebar);
  }
  
  // Make closeSidebar function globally available
  window.closeSidebar = closeSidebar;
}

// Store chart instances to properly destroy them when necessary
const chartInstances = {
  overview: null,
  engagement: null,
  category: null,
  comparison: null
};

/**
 * Render the overview chart on the main dashboard
 */
function renderOverviewChart(canvas) {
  // Destroy previous chart if it exists
  if (chartInstances.overview) {
    chartInstances.overview.destroy();
    chartInstances.overview = null;
  }
  
  try {
    const ctx = canvas.getContext('2d');
    const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
    
    chartInstances.overview = new Chart(ctx, {
      type: 'line',
      data: {
        labels: days,
        datasets: [
          {
            label: 'Profile Views',
            data: [45, 59, 80, 81, 56, 55, 72],
            borderColor: 'rgba(74, 108, 247, 0.7)',
            backgroundColor: 'rgba(74, 108, 247, 0.1)',
            tension: 0.3,
            pointBackgroundColor: 'rgba(74, 108, 247, 1)'
          },
          {
            label: 'Matches',
            data: [5, 7, 3, 8, 6, 9, 4],
            borderColor: 'rgba(40, 167, 69, 0.7)',
            backgroundColor: 'rgba(40, 167, 69, 0.1)',
            tension: 0.3,
            pointBackgroundColor: 'rgba(40, 167, 69, 1)'
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
          legend: {
            display: false
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            grid: {
              color: 'rgba(0, 0, 0, 0.05)'
            }
          },
          x: {
            grid: {
              display: false
            }
          }
        }
      }
    });
  } catch (error) {
    console.error('Error rendering overview chart:', error);
  }
}

/**
 * Render all charts in the performance tab
 */
function renderAllPerformanceCharts() {
  // First destroy any existing charts to prevent memory leaks
  destroyAllCharts(['engagement', 'category', 'comparison']);
  
  // Then render new charts
  const engagementCanvas = document.getElementById('engagement-chart');
  const categoryCanvas = document.getElementById('category-chart');
  const comparisonCanvas = document.getElementById('comparison-chart');
  
  if (engagementCanvas) renderEngagementChart(engagementCanvas);
  if (categoryCanvas) renderCategoryChart(categoryCanvas);
  if (comparisonCanvas) renderComparisonChart(comparisonCanvas);
}

/**
 * Destroy specific chart instances
 */
function destroyAllCharts(chartKeys) {
  chartKeys.forEach(key => {
    if (chartInstances[key]) {
      chartInstances[key].destroy();
      chartInstances[key] = null;
    }
  });
}

/**
 * Render the engagement chart
 */
function renderEngagementChart(canvas) {
  // Destroy previous chart if it exists
  if (chartInstances.engagement) {
    chartInstances.engagement.destroy();
    chartInstances.engagement = null;
  }
  
  try {
    const ctx = canvas.getContext('2d');
    const dates = ['02/15', '02/16', '02/17', '02/18', '02/19', '02/20', '02/21', 
                   '02/22', '02/23', '02/24', '02/25', '02/26', '02/27', '02/28'];
    
    chartInstances.engagement = new Chart(ctx, {
      type: 'line',
      data: {
        labels: dates,
        datasets: [
          {
            label: 'Profile Views',
            data: [45, 59, 80, 81, 56, 55, 72, 68, 83, 59, 72, 78, 65, 47],
            borderColor: 'rgba(74, 108, 247, 0.7)',
            backgroundColor: 'rgba(74, 108, 247, 0.1)',
            borderWidth: 2,
            tension: 0.3,
            fill: true
          },
          {
            label: 'Promotional Matches',
            data: [5, 7, 3, 8, 6, 9, 4, 2, 5, 6, 7, 3, 4, 3],
            borderColor: 'rgba(40, 167, 69, 0.7)',
            backgroundColor: 'rgba(40, 167, 69, 0.1)',
            borderWidth: 2,
            tension: 0.3,
            fill: true
          },
          {
            label: 'Website Clicks',
            data: [12, 15, 7, 9, 14, 17, 10, 8, 13, 15, 8, 6, 11, 13],
            borderColor: 'rgba(255, 193, 7, 0.7)',
            backgroundColor: 'rgba(255, 193, 7, 0.1)',
            borderWidth: 2,
            tension: 0.3,
            fill: true
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
          legend: {
            position: 'top'
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            grid: {
              color: 'rgba(0, 0, 0, 0.05)'
            }
          },
          x: {
            grid: {
              display: false
            }
          }
        }
      }
    });
  } catch (error) {
    console.error('Error rendering engagement chart:', error);
  }
}

/**
 * Render the category chart
 */
function renderCategoryChart(canvas) {
  // Destroy previous chart if it exists
  if (chartInstances.category) {
    chartInstances.category.destroy();
    chartInstances.category = null;
  }
  
  try {
    const ctx = canvas.getContext('2d');
    
    chartInstances.category = new Chart(ctx, {
      type: 'pie',
      data: {
        labels: ['Plumbing', 'Electrical', 'General Repairs', 'Flooring', 'Painting'],
        datasets: [{
          data: [40, 25, 15, 10, 10],
          backgroundColor: [
            'rgba(74, 108, 247, 0.7)',
            'rgba(40, 167, 69, 0.7)',
            'rgba(255, 193, 7, 0.7)',
            'rgba(220, 53, 69, 0.7)',
            'rgba(108, 117, 125, 0.7)'
          ],
          borderColor: [
            'rgba(74, 108, 247, 1)',
            'rgba(40, 167, 69, 1)',
            'rgba(255, 193, 7, 1)',
            'rgba(220, 53, 69, 1)',
            'rgba(108, 117, 125, 1)'
          ],
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
          legend: {
            position: 'right',
            labels: {
              boxWidth: 12,
              font: {
                size: 10
              }
            }
          }
        }
      }
    });
  } catch (error) {
    console.error('Error rendering category chart:', error);
  }
}

/**
 * Render the comparison chart
 */
function renderComparisonChart(canvas) {
  // Destroy previous chart if it exists
  if (chartInstances.comparison) {
    chartInstances.comparison.destroy();
    chartInstances.comparison = null;
  }
  
  try {
    const ctx = canvas.getContext('2d');
    
    chartInstances.comparison = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: ['Views', 'Matches', 'Clicks', 'Engagement'],
        datasets: [
          {
            label: 'Your Performance',
            data: [347, 28, 42, 15],
            backgroundColor: 'rgba(74, 108, 247, 0.7)',
            borderColor: 'rgba(74, 108, 247, 1)',
            borderWidth: 1
          },
          {
            label: 'Platform Average',
            data: [250, 20, 35, 12],
            backgroundColor: 'rgba(108, 117, 125, 0.3)',
            borderColor: 'rgba(108, 117, 125, 0.7)',
            borderWidth: 1
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
          legend: {
            position: 'top',
            labels: {
              boxWidth: 12,
              font: {
                size: 10
              }
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            grid: {
              color: 'rgba(0, 0, 0, 0.05)'
            }
          },
          x: {
            grid: {
              display: false
            }
          }
        }
      }
    });
  } catch (error) {
    console.error('Error rendering comparison chart:', error);
  }
}

/**
 * Initialize form interactions
 */
function initFormInteractions() {
  // Character counter for textareas
  const textareas = document.querySelectorAll('textarea');
  
  textareas.forEach(textarea => {
    const counterId = textarea.id + '-chars';
    const counter = document.getElementById(counterId);
    
    if (counter) {
      // Update initial count
      counter.textContent = textarea.value.length;
      
      // Add input event listener
      textarea.addEventListener('input', function() {
        counter.textContent = this.value.length;
      });
    }
  });
  
  // Service form preview
  const serviceDescription = document.getElementById('service-description');
  const servicePreviewText = document.getElementById('service-preview-text');
  const serviceKeywords = document.getElementById('service-keywords');
  const keywordPreview = document.getElementById('keyword-preview');
  
  if (serviceDescription && servicePreviewText) {
    serviceDescription.addEventListener('input', function() {
      servicePreviewText.textContent = this.value;
    });
  }
  
  if (serviceKeywords && keywordPreview) {
    serviceKeywords.addEventListener('input', function() {
      const keywords = this.value.split(',').map(keyword => keyword.trim()).filter(keyword => keyword);
      
      // Clear existing keyword tags
      keywordPreview.innerHTML = '';
      
      // Create new keyword tags
      keywords.forEach(keyword => {
        if (keyword) {
          const tag = document.createElement('span');
          tag.className = 'keyword-tag';
          tag.textContent = keyword;
          keywordPreview.appendChild(tag);
        }
      });
    });
  }
  
  // Promotion Status Toggle
  const promotionStatus = document.getElementById('promotion-status');
  const toggleLabel = document.querySelector('.toggle-label');
  
  if (promotionStatus && toggleLabel) {
    promotionStatus.addEventListener('change', function() {
      if (this.checked) {
        toggleLabel.textContent = 'Active';
        toggleLabel.style.color = 'var(--success-color)';
      } else {
        toggleLabel.textContent = 'Inactive';
        toggleLabel.style.color = 'var(--secondary-color)';
      }
    });
  }
}

/**
 * Initialize countdown timer
 */
function initCountdownTimer() {
  // Set a future date (example: 3 days, 12 hours, 45 minutes and 18 seconds from now)
  const now = new Date();
  const futureDate = new Date(now.getTime() + (3 * 24 * 60 * 60 * 1000) + (12 * 60 * 60 * 1000) + (45 * 60 * 1000) + (18 * 1000));
  
  // Elements
  const daysElement = document.getElementById('days-remaining');
  const hoursElement = document.getElementById('hours-remaining');
  const minutesElement = document.getElementById('minutes-remaining');
  const secondsElement = document.getElementById('seconds-remaining');
  const countdownElement = document.getElementById('promotion-countdown');
  
  if (!(daysElement && hoursElement && minutesElement && secondsElement) && !countdownElement) {
    return;
  }
  
  function updateCountdown() {
    const now = new Date().getTime();
    const distance = futureDate - now;
    
    // Time calculations
    const days = Math.floor(distance / (1000 * 60 * 60 * 24));
    const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
    const seconds = Math.floor((distance % (1000 * 60)) / 1000);
    
    // Update elements
    if (daysElement) daysElement.textContent = days;
    if (hoursElement) hoursElement.textContent = hours.toString().padStart(2, '0');
    if (minutesElement) minutesElement.textContent = minutes.toString().padStart(2, '0');
    if (secondsElement) secondsElement.textContent = seconds.toString().padStart(2, '0');
    
    // Update simple countdown text
    if (countdownElement) {
      let countdownText = '';
      
      if (days > 0) {
        countdownText += days + ' ' + (days === 1 ? 'day' : 'days');
      }
      
      if (hours > 0 || days > 0) {
        countdownText += (countdownText ? ', ' : '') + hours + ' ' + (hours === 1 ? 'hour' : 'hours');
      }
      
      if (minutes > 0 && days === 0) {
        countdownText += (countdownText ? ', ' : '') + minutes + ' ' + (minutes === 1 ? 'minute' : 'minutes');
      }
      
      if (seconds > 0 && days === 0 && hours === 0) {
        countdownText += (countdownText ? ', ' : '') + seconds + ' ' + (seconds === 1 ? 'second' : 'seconds');
      }
      
      countdownText += ' remaining';
      countdownElement.textContent = countdownText;
    }
    
    // If countdown is finished
    if (distance < 0) {
      clearInterval(countdownInterval);
      
      if (daysElement) daysElement.textContent = '0';
      if (hoursElement) hoursElement.textContent = '00';
      if (minutesElement) minutesElement.textContent = '00';
      if (secondsElement) secondsElement.textContent = '00';
      
      if (countdownElement) {
        countdownElement.textContent = 'EXPIRED';
      }
    }
  }
  
  // Update countdown immediately
  updateCountdown();
  
  // Update countdown every second
  const countdownInterval = setInterval(updateCountdown, 1000);
} 