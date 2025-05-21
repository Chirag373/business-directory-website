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
  visitors: null,
  trafficSources: null,
  devices: null
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
            label: 'Product Impressions',
            data: [25, 37, 30, 35, 40, 28, 32],
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
  destroyAllCharts(['visitors', 'trafficSources', 'devices']);
  
  // Then render new charts
  const visitorsCanvas = document.getElementById('visitors-chart');
  const trafficSourcesCanvas = document.getElementById('traffic-sources-chart');
  const devicesCanvas = document.getElementById('devices-chart');
  
  if (visitorsCanvas) renderVisitorsChart(visitorsCanvas);
  if (trafficSourcesCanvas) renderTrafficSourcesChart(trafficSourcesCanvas);
  if (devicesCanvas) renderDevicesChart(devicesCanvas);
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
 * Render the visitors chart
 */
function renderVisitorsChart(canvas) {
  // Destroy previous chart if it exists
  if (chartInstances.visitors) {
    chartInstances.visitors.destroy();
    chartInstances.visitors = null;
  }
  
  try {
    const ctx = canvas.getContext('2d');
    const dates = ['02/15', '02/16', '02/17', '02/18', '02/19', '02/20', '02/21', 
                   '02/22', '02/23', '02/24', '02/25', '02/26', '02/27', '02/28'];
    
    chartInstances.visitors = new Chart(ctx, {
      type: 'line',
      data: {
        labels: dates,
        datasets: [
          {
            label: 'Profile Views',
            data: [45, 59, 80, 81, 56, 55, 72, 68, 73, 85, 82, 75, 67, 78],
            borderColor: 'rgba(74, 108, 247, 0.7)',
            backgroundColor: 'rgba(74, 108, 247, 0.1)',
            tension: 0.3,
            fill: true,
            pointBackgroundColor: 'rgba(74, 108, 247, 1)'
          },
          {
            label: 'Product Impressions',
            data: [25, 37, 30, 35, 40, 28, 32, 35, 30, 38, 42, 39, 36, 40],
            borderColor: 'rgba(40, 167, 69, 0.7)',
            backgroundColor: 'rgba(40, 167, 69, 0.1)',
            tension: 0.3,
            fill: true,
            pointBackgroundColor: 'rgba(40, 167, 69, 1)'
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
          mode: 'index',
          intersect: false,
        },
        plugins: {
          tooltip: {
            enabled: true
          },
          legend: {
            position: 'top',
            labels: {
              boxWidth: 12,
              padding: 15
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
    console.error('Error rendering visitors chart:', error);
  }
}

/**
 * Render the traffic sources chart
 */
function renderTrafficSourcesChart(canvas) {
  // Destroy previous chart if it exists
  if (chartInstances.trafficSources) {
    chartInstances.trafficSources.destroy();
    chartInstances.trafficSources = null;
  }
  
  try {
    const ctx = canvas.getContext('2d');
    
    chartInstances.trafficSources = new Chart(ctx, {
      type: 'pie',
      data: {
        labels: ['Search', 'Direct', 'Referral', 'Social'],
        datasets: [{
          data: [38, 29, 18, 15],
          backgroundColor: [
            'rgba(74, 108, 247, 0.7)',
            'rgba(40, 167, 69, 0.7)',
            'rgba(255, 193, 7, 0.7)',
            'rgba(108, 117, 125, 0.7)'
          ],
          borderColor: [
            'rgba(74, 108, 247, 1)',
            'rgba(40, 167, 69, 1)',
            'rgba(255, 193, 7, 1)',
            'rgba(108, 117, 125, 1)'
          ],
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'bottom',
            labels: {
              boxWidth: 12,
              padding: 15
            }
          }
        }
      }
    });
  } catch (error) {
    console.error('Error rendering traffic sources chart:', error);
  }
}

/**
 * Render the devices chart
 */
function renderDevicesChart(canvas) {
  // Destroy previous chart if it exists
  if (chartInstances.devices) {
    chartInstances.devices.destroy();
    chartInstances.devices = null;
  }
  
  try {
    const ctx = canvas.getContext('2d');
    
    chartInstances.devices = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: ['Desktop', 'Mobile', 'Tablet'],
        datasets: [{
          data: [55, 35, 10],
          backgroundColor: [
            'rgba(74, 108, 247, 0.7)',
            'rgba(40, 167, 69, 0.7)',
            'rgba(255, 193, 7, 0.7)'
          ],
          borderColor: [
            'rgba(74, 108, 247, 1)',
            'rgba(40, 167, 69, 1)',
            'rgba(255, 193, 7, 1)'
          ],
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '60%',
        plugins: {
          legend: {
            position: 'bottom',
            labels: {
              boxWidth: 12,
              padding: 15
            }
          }
        }
      }
    });
  } catch (error) {
    console.error('Error rendering devices chart:', error);
  }
}

/**
 * Initialize form interactions
 */
function initFormInteractions() {
  // Character counters for textareas
  const textareas = document.querySelectorAll('textarea');
  textareas.forEach(textarea => {
    const counterId = textarea.id + '-chars';
    const counter = document.getElementById(counterId);
    
    if (counter) {
      // Initialize counter on load
      counter.textContent = textarea.value.length;
      
      // Update counter on input
      textarea.addEventListener('input', function() {
        counter.textContent = textarea.value.length;
      });
    }
  });
  
  // Toggle switch labels
  const toggleSwitches = document.querySelectorAll('.switch input[type="checkbox"]');
  toggleSwitches.forEach(toggle => {
    const toggleLabel = toggle.closest('.toggle-container')?.querySelector('.toggle-label');
    
    if (toggleLabel) {
      // Set initial label text
      toggleLabel.textContent = toggle.checked ? 'Yes' : 'No';
      
      // Update label on change
      toggle.addEventListener('change', function() {
        toggleLabel.textContent = toggle.checked ? 'Yes' : 'No';
      });
    }
  });
  
  // Form validation
  const forms = document.querySelectorAll('form');
  forms.forEach(form => {
    form.addEventListener('submit', function(event) {
      event.preventDefault();
      
      // Add proper form validation here if needed
      
      // For now, just show a success message
      alert('Form submitted successfully!');
    });
  });
}

/**
 * Initialize countdown timer
 */
function initCountdownTimer() {
  const countdownElement = document.getElementById('promotion-countdown');
  
  if (countdownElement) {
    updateCountdown();
    setInterval(updateCountdown, 60000); // Update every minute
  }
  
  function updateCountdown() {
    // This is a demo countdown - in a real app, this would be calculated from the server's end date
    const endDate = new Date();
    endDate.setDate(endDate.getDate() + 7); // 7 days from now
    endDate.setHours(endDate.getHours() + 6); // plus 6 hours
    
    const now = new Date();
    const timeDiff = endDate - now;
    
    if (timeDiff <= 0) {
      countdownElement.textContent = 'Expired';
    } else {
      const days = Math.floor(timeDiff / (1000 * 60 * 60 * 24));
      const hours = Math.floor((timeDiff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
      
      countdownElement.textContent = `${days} days, ${hours} hours remaining`;
    }
  }
} 