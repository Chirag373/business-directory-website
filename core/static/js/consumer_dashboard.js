document.addEventListener('DOMContentLoaded', function() {
  // Tab Navigation
  initTabNavigation();
  
  // Profile Progress Bar
  updateProfileProgress();
  
  // Location Dropdown Dependencies
  initLocationDropdowns();
  
  // Form Submission Handlers
  initFormHandlers();
  
  // Offer Cards Interaction
  initOfferCards();
  
  // Filter Functionality
  initFilters();
  
  // Notification Slider
  initNotificationSlider();
  
  // Mobile Dashboard Sidebar
  initMobileDashboardSidebar();
});

/**
 * Initialize tab navigation functionality
 */
function initTabNavigation() {
  const tabButtons = document.querySelectorAll('.tab-button');
  const contentSections = document.querySelectorAll('.dashboard-content');
  
  tabButtons.forEach(button => {
    button.addEventListener('click', () => {
      // Remove active class from all buttons and sections
      tabButtons.forEach(btn => btn.classList.remove('active'));
      contentSections.forEach(section => section.classList.remove('active'));
      
      // Add active class to clicked button
      button.classList.add('active');
      
      // Show corresponding content section
      const tabName = button.getAttribute('data-tab');
      document.getElementById(`${tabName}-section`).classList.add('active');
    });
  });
}

/**
 * Update profile progress bar based on filled fields
 */
function updateProfileProgress() {
  const profileFields = document.querySelectorAll('.profile-form input, .profile-form select');
  const progressBar = document.getElementById('profile-progress');
  const percentageDisplay = document.querySelector('.completion-percentage');
  
  if (progressBar) {
    // Count filled fields for real implementation
    // This is a simple demo calculation
    let filledCount = 0;
    profileFields.forEach(field => {
      if (field.value && field.value.trim() !== '') {
        filledCount++;
      }
    });
    
    const totalFields = profileFields.length;
    const completionPercentage = Math.round((filledCount / totalFields) * 100);
    
    progressBar.style.width = `${completionPercentage}%`;
    percentageDisplay.textContent = `${completionPercentage}%`;
  }
  
  // Add input event listeners to update progress in real-time
  profileFields.forEach(field => {
    field.addEventListener('input', updateProfileProgress);
  });
}

/**
 * Initialize cascading location dropdowns (State -> County -> City)
 */
function initLocationDropdowns() {
  const stateSelect = document.getElementById('state');
  const countySelect = document.getElementById('county');
  const citySelect = document.getElementById('city');
  
  if (!stateSelect || !countySelect || !citySelect) return;
  
  // Sample data - in a real app, this would come from an API call
  const locationData = {
    'CA': {
      name: 'California',
      counties: {
        'LAC': {
          name: 'Los Angeles County',
          cities: ['Los Angeles', 'Long Beach', 'Pasadena']
        },
        'SDC': {
          name: 'San Diego County',
          cities: ['San Diego', 'Chula Vista', 'Oceanside']
        }
      }
    },
    'TX': {
      name: 'Texas',
      counties: {
        'HC': {
          name: 'Harris County',
          cities: ['Houston', 'Pasadena', 'Baytown']
        },
        'DC': {
          name: 'Dallas County',
          cities: ['Dallas', 'Irving', 'Garland']
        }
      }
    }
  };
  
  // Populate states dropdown
  Object.keys(locationData).forEach(stateCode => {
    const option = document.createElement('option');
    option.value = stateCode;
    option.textContent = locationData[stateCode].name;
    stateSelect.appendChild(option);
  });
  
  // Handle state selection change
  stateSelect.addEventListener('change', function() {
    const selectedState = this.value;
    
    // Reset and disable county and city dropdowns if no state selected
    if (!selectedState) {
      countySelect.innerHTML = '<option value="">Select a County</option>';
      citySelect.innerHTML = '<option value="">Select a City</option>';
      countySelect.disabled = true;
      citySelect.disabled = true;
      return;
    }
    
    // Enable and populate county dropdown
    countySelect.disabled = false;
    countySelect.innerHTML = '<option value="">Select a County</option>';
    citySelect.innerHTML = '<option value="">Select a City</option>';
    citySelect.disabled = true;
    
    const counties = locationData[selectedState].counties;
    Object.keys(counties).forEach(countyCode => {
      const option = document.createElement('option');
      option.value = countyCode;
      option.textContent = counties[countyCode].name;
      countySelect.appendChild(option);
    });
  });
  
  // Handle county selection change
  countySelect.addEventListener('change', function() {
    const selectedState = stateSelect.value;
    const selectedCounty = this.value;
    
    // Reset and disable city dropdown if no county selected
    if (!selectedCounty) {
      citySelect.innerHTML = '<option value="">Select a City</option>';
      citySelect.disabled = true;
      return;
    }
    
    // Enable and populate city dropdown
    citySelect.disabled = false;
    citySelect.innerHTML = '<option value="">Select a City</option>';
    
    const cities = locationData[selectedState].counties[selectedCounty].cities;
    cities.forEach(city => {
      const option = document.createElement('option');
      option.value = city.toLowerCase().replace(/\s/g, '_');
      option.textContent = city;
      citySelect.appendChild(option);
    });
  });
}

/**
 * Initialize form submission handlers
 */
function initFormHandlers() {
  // Profile Form
  const profileForm = document.querySelector('.profile-form');
  if (profileForm) {
    profileForm.addEventListener('submit', function(event) {
      event.preventDefault();
      
      // Display success message (in a real app, would save to backend)
      showToast('Profile updated successfully!', 'success');
      
      // Update last updated timestamp
      const now = new Date();
      const options = { 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
      };
      document.getElementById('last-updated-timestamp').textContent = now.toLocaleDateString('en-US', options);
    });
  }
  
  // Preferences Form
  const preferencesForm = document.querySelector('.preferences-form');
  if (preferencesForm) {
    preferencesForm.addEventListener('submit', function(event) {
      event.preventDefault();
      
      // Display success message
      showToast('Service preferences updated successfully!', 'success');
    });
  }
  
  // Notification Settings Form
  const notificationForm = document.querySelector('.notification-form');
  if (notificationForm) {
    notificationForm.addEventListener('submit', function(event) {
      event.preventDefault();
      
      // Display success message
      showToast('Notification settings saved successfully!', 'success');
    });
  }
}

/**
 * Initialize offer cards interaction
 */
function initOfferCards() {
  // Handle view details button click
  const viewDetailsButtons = document.querySelectorAll('.view-details-button');
  viewDetailsButtons.forEach(button => {
    button.addEventListener('click', function(event) {
      event.preventDefault();
      
      // Get the parent card and flip it
      const card = this.closest('.offer-card');
      const cardInner = card.querySelector('.offer-card-inner');
      cardInner.style.transform = 'rotateY(180deg)';
    });
  });
  
  // Handle back button click
  const backButtons = document.querySelectorAll('.back-to-front-button');
  backButtons.forEach(button => {
    button.addEventListener('click', function(event) {
      event.preventDefault();
      
      // Get the parent card and flip it back
      const card = this.closest('.offer-card');
      const cardInner = card.querySelector('.offer-card-inner');
      cardInner.style.transform = 'rotateY(0deg)';
    });
  });
  
  // Update countdowns for expiry dates
  updateCountdowns();
  setInterval(updateCountdowns, 60000); // Update every minute
}

/**
 * Update countdown timers for offer expiry dates
 */
function updateCountdowns() {
  const countdownElements = document.querySelectorAll('.countdown');
  const now = new Date();
  
  countdownElements.forEach(element => {
    const expiryDate = new Date(element.getAttribute('data-expiry'));
    const diffTime = expiryDate - now;
    
    if (diffTime <= 0) {
      element.textContent = 'Expired';
      element.style.color = 'var(--secondary-color)';
    } else {
      const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
      if (diffDays > 1) {
        element.textContent = `${diffDays} days`;
      } else if (diffDays === 1) {
        element.textContent = '1 day';
      } else {
        const diffHours = Math.floor(diffTime / (1000 * 60 * 60));
        element.textContent = `${diffHours} hours`;
      }
      
      // Change color to indicate urgency
      if (diffDays <= 3) {
        element.style.color = 'var(--danger-color)';
      } else if (diffDays <= 7) {
        element.style.color = 'var(--warning-color)';
      }
    }
  });
}

/**
 * Initialize filters for promotional offers
 */
function initFilters() {
  // For demo purposes - this would connect to real data in production
  const offerCards = document.querySelectorAll('.offer-card');
  const emptyState = document.querySelector('.empty-offers');
  
  // Category filter
  const categoryFilter = document.getElementById('category-filter');
  if (categoryFilter) {
    categoryFilter.addEventListener('change', applyFilters);
  }
  
  // Date filter
  const dateFilter = document.getElementById('date-filter');
  if (dateFilter) {
    dateFilter.addEventListener('change', applyFilters);
  }
  
  // Discount filter
  const discountFilter = document.getElementById('discount-filter');
  if (discountFilter) {
    discountFilter.addEventListener('change', applyFilters);
  }
  
  // Active filter
  const activeFilter = document.getElementById('active-filter');
  if (activeFilter) {
    activeFilter.addEventListener('change', applyFilters);
  }
  
  // Quick filter buttons
  const quickFilterButtons = document.querySelectorAll('.quick-filter-button');
  quickFilterButtons.forEach(button => {
    button.addEventListener('click', function() {
      const category = this.getAttribute('data-category');
      
      // Set the category filter dropdown to match the quick filter
      if (categoryFilter) {
        categoryFilter.value = category;
        applyFilters();
      }
    });
  });
  
  /**
   * Apply all active filters to the offer cards
   */
  function applyFilters() {
    let visibleCount = 0;
    
    offerCards.forEach(card => {
      // For this demo, we'll just use the one sample card we have
      // In a real app, we would apply actual filtering logic
      card.style.display = 'block';
      visibleCount++;
    });
    
    // Show/hide empty state
    if (emptyState) {
      if (visibleCount === 0) {
        emptyState.classList.remove('hidden');
      } else {
        emptyState.classList.add('hidden');
      }
    }
  }
}

/**
 * Initialize notification slider functionality
 */
function initNotificationSlider() {
  const slider = document.getElementById('notification-limit');
  const sliderValue = document.getElementById('slider-value');
  
  if (slider && sliderValue) {
    slider.addEventListener('input', function() {
      sliderValue.textContent = this.value;
    });
  }
}

/**
 * Display a toast notification
 * @param {string} message - The message to display
 * @param {string} type - The type of notification (success, error, info)
 */
function showToast(message, type = 'info') {
  // Create toast container if it doesn't exist
  let toastContainer = document.querySelector('.toast-container');
  if (!toastContainer) {
    toastContainer = document.createElement('div');
    toastContainer.className = 'toast-container';
    document.body.appendChild(toastContainer);
    
    // Add toast container styles if not in CSS
    toastContainer.style.position = 'fixed';
    toastContainer.style.bottom = '20px';
    toastContainer.style.right = '20px';
    toastContainer.style.zIndex = '1000';
  }
  
  // Create toast
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  
  // Style the toast
  toast.style.backgroundColor = type === 'success' ? 'var(--success-color)' : 
                              type === 'error' ? 'var(--danger-color)' : 
                              'var(--primary-color)';
  toast.style.color = 'white';
  toast.style.padding = '10px 20px';
  toast.style.borderRadius = 'var(--border-radius)';
  toast.style.marginTop = '10px';
  toast.style.boxShadow = 'var(--box-shadow)';
  toast.style.opacity = '0';
  toast.style.transition = 'all 0.3s ease';
  
  // Add to container
  toastContainer.appendChild(toast);
  
  // Animate in
  setTimeout(() => {
    toast.style.opacity = '1';
  }, 10);
  
  // Remove after timeout
  setTimeout(() => {
    toast.style.opacity = '0';
    setTimeout(() => {
      toast.remove();
    }, 300);
  }, 3000);
}

/**
 * Initialize mobile dashboard sidebar functionality
 */
function initMobileDashboardSidebar() {
  const hamburgerButton = document.querySelector('.dashboard-hamburger');
  const dashboardSidebar = document.querySelector('.dashboard-sidebar');
  const dashboardOverlay = document.querySelector('.dashboard-overlay');
  const closeButton = document.querySelector('.dashboard-sidebar .close-sidebar');
  const sidebarButtons = document.querySelectorAll('.sidebar-tab-button');
  
  // Toggle sidebar when clicking hamburger button
  if (hamburgerButton) {
    hamburgerButton.addEventListener('click', () => {
      dashboardSidebar.classList.add('active');
      dashboardOverlay.classList.add('active');
      document.body.style.overflow = 'hidden'; // Prevent scrolling
    });
  }
  
  // Close sidebar when clicking the close button
  if (closeButton) {
    closeButton.addEventListener('click', closeSidebar);
  }
  
  // Close sidebar when clicking outside (on overlay)
  if (dashboardOverlay) {
    dashboardOverlay.addEventListener('click', closeSidebar);
  }
  
  // Handle sidebar tab button clicks
  sidebarButtons.forEach(button => {
    button.addEventListener('click', () => {
      // Get tab name
      const tabName = button.getAttribute('data-tab');
      
      // Update main tabs
      const mainTabButtons = document.querySelectorAll('.tab-button');
      mainTabButtons.forEach(btn => {
        if (btn.getAttribute('data-tab') === tabName) {
          btn.click(); // Trigger click on the corresponding main tab
        }
      });
      
      // Update sidebar active state
      sidebarButtons.forEach(btn => btn.classList.remove('active'));
      button.classList.add('active');
      
      // Close sidebar after selection
      closeSidebar();
    });
  });
  
  // Function to close the sidebar
  function closeSidebar() {
    dashboardSidebar.classList.remove('active');
    dashboardOverlay.classList.remove('active');
    document.body.style.overflow = ''; // Restore scrolling
  }
  
  // Close sidebar on window resize if screen becomes large
  window.addEventListener('resize', () => {
    if (window.innerWidth > 768 && dashboardSidebar.classList.contains('active')) {
      closeSidebar();
    }
  });
} 