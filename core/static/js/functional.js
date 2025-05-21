document.addEventListener("DOMContentLoaded", function () {
  // Sidebar toggle for mobile only
  const hamburger = document.querySelector(".hamburger");
  const sidebar = document.querySelector(".sidebar");
  const overlay = document.querySelector(".overlay");
  const closeSidebar = document.querySelector(".close-sidebar");
  const body = document.body;
  
  function toggleSidebar() {
    // Toggle visibility classes
    sidebar.classList.toggle("show");
    overlay.classList.toggle("show");
    
    // Prevent body scrolling when sidebar is open
    if (sidebar.classList.contains("show")) {
      body.style.overflow = "hidden";
    } else {
      body.style.overflow = "";
    }
  }

  // Check if we're on a mobile device
  function isMobileViewport() {
    return window.innerWidth <= 768; // Matches the CSS media query breakpoint
  }

  if (hamburger) {
    hamburger.addEventListener("click", function(e) {
      e.stopPropagation();
      toggleSidebar();
    });
  }
  
  if (closeSidebar) {
    closeSidebar.addEventListener("click", function(e) {
      e.stopPropagation();
      toggleSidebar();
    });
  }
  
  if (overlay) {
    overlay.addEventListener("click", toggleSidebar);
  }
  
  // Close sidebar when clicking on menu items (on mobile)
  const sidebarLinks = document.querySelectorAll(".sidebar-menu a");
  sidebarLinks.forEach(link => {
    link.addEventListener("click", function() {
      if (sidebar.classList.contains("show")) {
        toggleSidebar();
      }
    });
  });
  
  // Close sidebar when pressing Escape key
  document.addEventListener("keydown", function(e) {
    if (e.key === "Escape" && sidebar.classList.contains("show")) {
      toggleSidebar();
    }
  });
  
  // Handle window resize - close sidebar when switching to desktop
  window.addEventListener("resize", function() {
    if (!isMobileViewport() && sidebar.classList.contains("show")) {
      toggleSidebar();
    }
  });

  // Ensure sidebar is reset to proper state on page load
  if (sidebar) {
    sidebar.classList.remove("show");
  }
  if (overlay) {
    overlay.classList.remove("show");
  }

  // Card flip functionality with improved animations
  const flipLabels = document.querySelectorAll(".flip-label");
  const cards = document.querySelectorAll(".business-card");

  flipLabels.forEach((label) => {
    label.addEventListener("click", function (e) {
      e.stopPropagation(); // Prevent the click from bubbling up
      const cardId = this.getAttribute("data-card");
      const card = document.getElementById(cardId);

      if (card.style.transform === "rotateY(180deg)") {
        card.style.transform = "rotateY(0deg)";
        this.textContent = "Back Side";
        card.classList.remove("clicked");
      } else {
        card.style.transform = "rotateY(180deg)";
        this.textContent = "Front Side";
        card.classList.add("clicked");
      }
    });
  });

  // Touch device detection
  const isTouchDevice = () => {
    return (
      "ontouchstart" in window ||
      navigator.maxTouchPoints > 0 ||
      navigator.msMaxTouchPoints > 0
    );
  };

  if (!isTouchDevice()) {
    // Only apply hover effects on non-touch devices
    cards.forEach((card) => {
      const wrapper = card.closest(".business-card-wrapper");

      wrapper.addEventListener("mouseenter", function () {
        if (!card.classList.contains("clicked")) {
          card.style.transform = "rotateY(180deg)";
          this.querySelector(".flip-label").textContent = "Front Side";
        }
      });

      wrapper.addEventListener("mouseleave", function () {
        if (!card.classList.contains("clicked")) {
          card.style.transform = "rotateY(0deg)";
          this.querySelector(".flip-label").textContent = "Back Side";
        }
      });
    });
  }

  // State, County, City dependent dropdown with enhanced user experience
  const stateSelect = document.getElementById("state");
  const countySelect = document.getElementById("county");
  const citySelect = document.getElementById("city");
  const searchBtn = document.querySelector(".search-btn");
  
  if (stateSelect) {
    // Mock data for dropdown interactions
    const mockData = {
      "CA": {
        name: "California",
        counties: [
          { id: "ca-1", name: "Los Angeles" },
          { id: "ca-2", name: "San Francisco" },
          { id: "ca-3", name: "San Diego" }
        ]
      },
      "NY": {
        name: "New York",
        counties: [
          { id: "ny-1", name: "Manhattan" },
          { id: "ny-2", name: "Brooklyn" },
          { id: "ny-3", name: "Queens" }
        ]
      },
      "TX": {
        name: "Texas",
        counties: [
          { id: "tx-1", name: "Harris" },
          { id: "tx-2", name: "Dallas" },
          { id: "tx-3", name: "Travis" }
        ]
      },
      "FL": {
        name: "Florida",
        counties: [
          { id: "fl-1", name: "Miami-Dade" },
          { id: "fl-2", name: "Broward" },
          { id: "fl-3", name: "Palm Beach" }
        ]
      }
    };

    const mockCities = {
      "ca-1": ["Los Angeles", "Long Beach", "Pasadena"],
      "ca-2": ["San Francisco", "Oakland", "Berkeley"],
      "ca-3": ["San Diego", "Chula Vista", "Oceanside"],
      "ny-1": ["Manhattan", "Midtown", "Upper East Side"],
      "ny-2": ["Brooklyn Heights", "Williamsburg", "Park Slope"],
      "ny-3": ["Astoria", "Long Island City", "Flushing"],
      "tx-1": ["Houston", "Spring", "Katy"],
      "tx-2": ["Dallas", "Irving", "Richardson"],
      "tx-3": ["Austin", "Round Rock", "Cedar Park"],
      "fl-1": ["Miami", "Coral Gables", "Hialeah"],
      "fl-2": ["Fort Lauderdale", "Hollywood", "Pompano Beach"],
      "fl-3": ["West Palm Beach", "Boca Raton", "Delray Beach"]
    };

    // Function to populate dropdown with options
    function populateDropdown(select, options, defaultText = "Select an option") {
      select.innerHTML = `<option value="">${defaultText}</option>`;
      
      options.forEach(option => {
        if (typeof option === 'object') {
          const optElement = document.createElement('option');
          optElement.value = option.id;
          optElement.textContent = option.name;
          select.appendChild(optElement);
        } else {
          const optElement = document.createElement('option');
          optElement.value = option.toLowerCase().replace(/\s+/g, '-');
          optElement.textContent = option;
          select.appendChild(optElement);
        }
      });
      
      // Add fade-in animation
      select.classList.add('animated');
      setTimeout(() => {
        select.classList.remove('animated');
      }, 500);
    }

    // State change event - Enable and populate county dropdown
    stateSelect.addEventListener("change", function () {
      if (this.value) {
        const state = mockData[this.value];
        if (state) {
          countySelect.removeAttribute("disabled");
          populateDropdown(countySelect, state.counties, "Select County");
        }
      } else {
        countySelect.setAttribute("disabled", "disabled");
        countySelect.innerHTML = '<option value="">Select County</option>';
        citySelect.setAttribute("disabled", "disabled");
        citySelect.innerHTML = '<option value="">Select City</option>';
      }
      
      // Update search button state
      updateSearchButtonState();
    });

    // County change event - Enable and populate city dropdown
    if (countySelect) {
      countySelect.addEventListener("change", function () {
        if (this.value) {
          const cities = mockCities[this.value];
          if (cities) {
            citySelect.removeAttribute("disabled");
            populateDropdown(citySelect, cities, "Select City");
          }
        } else {
          citySelect.setAttribute("disabled", "disabled");
          citySelect.innerHTML = '<option value="">Select City</option>';
        }
        
        // Update search button state
        updateSearchButtonState();
      });
    }
    
    // City change event - Update search button state
    if (citySelect) {
      citySelect.addEventListener("change", function() {
        updateSearchButtonState();
      });
    }
    
    // Update search button visual state based on selections
    function updateSearchButtonState() {
      const hasStateValue = stateSelect.value !== "";
      
      if (hasStateValue) {
        searchBtn.classList.add("active");
      } else {
        searchBtn.classList.remove("active");
      }
    }
    
    // Search button click event
    if (searchBtn) {
      searchBtn.addEventListener("click", function() {
        if (stateSelect.value) {
          const stateText = stateSelect.options[stateSelect.selectedIndex].text;
          let searchMessage = `Searching in ${stateText}`;
          
          if (countySelect.value) {
            const countyText = countySelect.options[countySelect.selectedIndex].text;
            searchMessage += `, ${countyText} County`;
            
            if (citySelect.value) {
              const cityText = citySelect.options[citySelect.selectedIndex].text;
              searchMessage += `, ${cityText}`;
            }
          }
          
          // Show a notification toast
          showNotification(searchMessage);
        }
      });
    }
  }
  
  // Simple notification toast system
  function showNotification(message) {
    const notification = document.createElement('div');
    notification.className = 'notification-toast';
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    // Trigger animation
    setTimeout(() => {
      notification.classList.add('show');
    }, 10);
    
    // Remove after delay
    setTimeout(() => {
      notification.classList.remove('show');
      setTimeout(() => {
        document.body.removeChild(notification);
      }, 300);
    }, 3000);
  }
  
  // Add animation to elements when they come into view
  function animateOnScroll() {
    const elements = document.querySelectorAll('.business-card-wrapper');
    
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('animate-in');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1 });
    
    elements.forEach(element => {
      observer.observe(element);
    });
  }
  
  // Initialize animation on scroll
  animateOnScroll();
  
  // Make global for category items
  window.showNotification = showNotification;
});

// Add CSS for notification toast
document.addEventListener('DOMContentLoaded', function() {
  const style = document.createElement('style');
  style.textContent = `
    .notification-toast {
      position: fixed;
      bottom: -60px;
      left: 50%;
      transform: translateX(-50%);
      background-color: var(--primary-color);
      color: white;
      padding: 12px 24px;
      border-radius: 4px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.15);
      z-index: 1000;
      opacity: 0;
      transition: all 0.3s ease;
    }
    
    .notification-toast.show {
      bottom: 20px;
      opacity: 1;
    }
    
    .animated {
      animation: fadeIn 0.5s ease;
    }
    
    .business-card-wrapper {
      opacity: 0;
      transform: translateY(20px);
    }
    
    .business-card-wrapper.animate-in {
      animation: cardFadeIn 0.5s ease forwards;
    }
    
    @keyframes cardFadeIn {
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }
  `;
  document.head.appendChild(style);
});