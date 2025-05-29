document.addEventListener('DOMContentLoaded', function() {
  // Cache DOM elements
  const cardWrappers = document.querySelectorAll('.business-card-wrapper');
  const searchForm = document.querySelector('.search-section form');
  const searchBtn = document.querySelector('.search-btn');
  const serviceInput = document.getElementById('service_description');
  const inputs = document.querySelectorAll('.search-box input');
  
  // Enhanced card interactions with event delegation
  cardWrappers.forEach(wrapper => {
    const card = wrapper.querySelector('.business-card');
    const cardId = card.id.replace('handyman-', '');
    const flipButtons = wrapper.querySelectorAll('.flip-label');
    const infoContainer = wrapper.querySelector('.card-back-info-container');
    
    // Click to flip card with improved event handling
    wrapper.addEventListener('click', function(e) {
      // Prevent flip if clicking on buttons, links or scrollable content area
      if (e.target.classList.contains('flip-label') || 
          e.target.classList.contains('card-website') ||
          e.target.tagName === 'A' ||
          isDescendantOf(e.target, infoContainer)) {
        return;
      }
      flipHandymanCard(cardId);
    });
    
    // Optimized wheel event handling for scrollable content
    if (infoContainer) {
      infoContainer.addEventListener('wheel', function(e) {
        if (card.classList.contains('flipped')) {
          const delta = e.deltaY || e.detail || e.wheelDelta;
          const scrollTop = infoContainer.scrollTop;
          const maxScroll = infoContainer.scrollHeight - infoContainer.clientHeight;
          
          if ((delta > 0 && scrollTop < maxScroll) || 
              (delta < 0 && scrollTop > 0) ||
              (scrollTop === 0 && delta < 0) ||
              (scrollTop >= maxScroll && delta > 0)) {
            e.stopPropagation();
          }
        }
      }, { passive: true });
      
      // Use event delegation for multiple events
      const stopEvents = ['click', 'touchstart', 'touchmove', 'mousedown', 'mousemove'];
      stopEvents.forEach(eventType => {
        infoContainer.addEventListener(eventType, function(e) {
          if (card.classList.contains('flipped')) {
            e.stopPropagation();
          }
        }, { passive: true });
      });
    }
    
    // Optimized flip buttons
    flipButtons.forEach(button => {
      button.addEventListener('click', function(e) {
        e.stopPropagation();
        flipHandymanCard(cardId);
      });
    });
    
    // Hover effects for desktop only
    if (window.matchMedia('(min-width: 769px)').matches) {
      wrapper.addEventListener('mouseenter', function() {
        this.style.transform = 'translateY(-5px)';
      });
      
      wrapper.addEventListener('mouseleave', function() {
        this.style.transform = 'translateY(0)';
      });
    }
  });
  
  // Helper function with improved performance
  function isDescendantOf(child, parent) {
    let node = child;
    while (node !== null && node !== document.body) {
      if (node === parent) return true;
      node = node.parentNode;
    }
    return false;
  }
  
  // Enhanced search form handling
  if (searchForm) {
    searchForm.addEventListener('submit', function() {
      searchBtn.classList.add('loading');
      searchBtn.disabled = true;
    });
  }
  
  // Optimize input handling with event delegation
  if (inputs.length) {
    const searchContainer = document.querySelector('.search-container');
    searchContainer.addEventListener('focusin', function(e) {
      if (e.target.tagName === 'INPUT') {
        e.target.parentElement.classList.add('focused');
      }
    });
    
    searchContainer.addEventListener('focusout', function(e) {
      if (e.target.tagName === 'INPUT') {
        e.target.parentElement.classList.remove('focused');
      }
    });
  }
  
  // Optimized search filtering
  if (serviceInput) {
    // Use debounce to improve performance during typing
    let debounceTimer;
    serviceInput.addEventListener('input', function() {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        const searchTerm = this.value.toLowerCase();
        const allCards = document.querySelectorAll('.business-card-wrapper');
        
        allCards.forEach(wrapper => {
          const card = wrapper.querySelector('.business-card');
          const title = card.querySelector('.card-title').textContent.toLowerCase();
          const description = card.querySelector('.card-description').textContent.toLowerCase();
          
          wrapper.style.display = 
            (searchTerm === '' || title.includes(searchTerm) || description.includes(searchTerm)) 
              ? 'block' : 'none';
        });
      }, 200);
    });
  }
  
  // Promotional notifications
  const promoCards = document.querySelectorAll('.promo-indicator.active');
  if (promoCards.length > 0) {
    setTimeout(() => {
      showNotification(`${promoCards.length} handymen with active promotions available!`, 'success');
    }, 1000);
  }
  
  // Mobile optimization with ResizeObserver instead of resize event
  const mobileOptimizer = new ResizeObserver(entries => {
    const isMobile = window.innerWidth <= 576;
    document.querySelectorAll('.business-card-wrapper').forEach(card => {
      card.style.width = isMobile ? '95%' : '';
    });
    
    const container = document.querySelector('.business-cards-container');
    const mainContainer = document.querySelector('.main-container');
    if (container) container.style.width = isMobile ? '95%' : '';
    if (mainContainer) mainContainer.style.width = isMobile ? '95%' : '';
  });
  
  mobileOptimizer.observe(document.body);
});

// Optimized flip function
function flipHandymanCard(handymanId) {
  const card = document.getElementById('handyman-' + handymanId);
  if (!card) return;
  
  card.classList.toggle('flipped');
  
  // Reset scroll with requestAnimationFrame for better performance
  if (!card.classList.contains('flipped')) {
    const infoContainer = card.querySelector('.card-back-info-container');
    if (infoContainer) {
      requestAnimationFrame(() => {
        infoContainer.scrollTo({
          top: 0,
          behavior: 'smooth'
        });
      });
    }
  }
  
  // Optimize animation handling
  if (card.classList.contains('flipped')) {
    card.classList.add('flipping');
    setTimeout(() => {
      card.classList.remove('flipping');
    }, 1500);
  }
  
  // Update flip labels
  const frontLabel = card.querySelector('.business-card-front .flip-label');
  const backLabel = card.querySelector('.business-card-back .flip-label');
  const newText = card.classList.contains('flipped') ? 'Front Side' : 'Back Side';
  
  setTimeout(() => {
    if (frontLabel) frontLabel.textContent = newText;
    if (backLabel) backLabel.textContent = newText;
  }, 300);
}

// Optimized smooth scroll function
function smoothScroll(target) {
  const element = document.querySelector(target);
  if (element) {
    element.scrollIntoView({
      behavior: 'smooth',
      block: 'start'
    });
  }
}

// Optimized notification function
function showNotification(message, type = 'info') {
  const notification = document.createElement('div');
  notification.className = `notification ${type}`;
  notification.textContent = message;
  
  // Map notification types to colors
  const colors = {
    success: 'var(--handyman-secondary)',
    error: 'var(--handyman-accent)',
    warning: '#f39c12',
    info: 'var(--handyman-primary)'
  };
  
  notification.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    background: ${colors[type] || colors.info};
    color: white;
    padding: 15px 20px;
    border-radius: 8px;
    box-shadow: var(--shadow-lg);
    z-index: 1000;
    animation: slideInRight 0.3s ease;
    max-width: 300px;
    font-weight: 500;
  `;
  
  document.body.appendChild(notification);
  
  // Use requestAnimationFrame for smoother animation
  setTimeout(() => {
    notification.style.animation = 'slideOutRight 0.3s ease';
    setTimeout(() => {
      notification.remove();
    }, 300);
  }, 3000);
} 