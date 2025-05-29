document.addEventListener('DOMContentLoaded', function() {
  // Cached DOM elements
  const elements = {
    flipCard: document.getElementById('flip-card'),
    showFrontBtn: document.getElementById('show-front'),
    showBackBtn: document.getElementById('show-back'),
    frontInput: document.getElementById('card-front'),
    frontPreview: document.getElementById('front-preview'),
    backInput: document.getElementById('card-back'),
    backPreview: document.getElementById('back-preview'),
    blankBackCheckbox: document.getElementById('blank-back'),
    businessCardForm: document.querySelector('.business-card-form'),
    primaryButton: document.querySelector('.primary-button'),
    uploadContainers: document.querySelectorAll('.upload-container')
  };
  
  // Helper functions
  const helpers = {
    createModal: () => {
      const modal = document.createElement('div');
      modal.id = 'image-modal';
      modal.innerHTML = `
        <div class="modal-overlay">
          <div class="modal-content">
            <div class="modal-header">
              <h3 id="modal-title"></h3>
              <button class="modal-close">&times;</button>
            </div>
            <div class="modal-body">
              <img id="modal-image" alt="">
            </div>
          </div>
        </div>
      `;
      
      const modalStyles = document.createElement('style');
      modalStyles.textContent = `
        #image-modal{position:fixed;top:0;left:0;width:100%;height:100%;z-index:10000;display:none}
        .modal-overlay{position:absolute;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.8);display:flex;align-items:center;justify-content:center;padding:2rem}
        .modal-content{background:white;border-radius:var(--border-radius);max-width:90vw;max-height:90vh;overflow:hidden;box-shadow:var(--shadow-lg)}
        .modal-header{display:flex;justify-content:space-between;align-items:center;padding:1rem 1.5rem;border-bottom:1px solid var(--border-color)}
        .modal-close{background:none;border:none;font-size:1.5rem;cursor:pointer;color:var(--text-muted);padding:0.5rem;border-radius:50%;transition:var(--transition)}
        .modal-close:hover{background:var(--light-color);color:var(--dark-color)}
        .modal-body{padding:1.5rem;text-align:center}
        #modal-image{max-width:100%;max-height:70vh;object-fit:contain;border-radius:8px}
      `;
      
      document.head.appendChild(modalStyles);
      document.body.appendChild(modal);
      
      modal.querySelector('.modal-close').addEventListener('click', () => modal.style.display = 'none');
      modal.querySelector('.modal-overlay').addEventListener('click', (e) => {
        if (e.target === e.currentTarget) modal.style.display = 'none';
      });
      
      return modal;
    },
    
    simulateProgress: (progressBar, progressBarInner) => {
      progressBar.style.display = 'block';
      progressBarInner.style.width = '0%';
      
      let progress = 0;
      const progressInterval = setInterval(() => {
        progress += Math.random() * 30;
        if (progress >= 100) {
          progress = 100;
          clearInterval(progressInterval);
          setTimeout(() => progressBar.style.display = 'none', 500);
        }
        progressBarInner.style.width = progress + '%';
      }, 100);
    },
    
    setupImagePreview: (input, preview, title) => {
      if (!input || !preview) return;
      
      input.addEventListener('change', function() {
        const file = this.files[0];
        if (!file) return;
        
        const uploadContainer = this.closest('.upload-container');
        const progressBar = uploadContainer.querySelector('.upload-progress');
        const progressBarInner = uploadContainer.querySelector('.progress-bar');
        
        if (progressBar && progressBarInner) {
          helpers.simulateProgress(progressBar, progressBarInner);
        }
        
        const reader = new FileReader();
        reader.onload = (e) => {
          preview.innerHTML = `
            <img src="${e.target.result}" alt="Business card ${title.toLowerCase()}" class="preview-image">
            <div class="preview-overlay">
              <i class="fas fa-expand-alt"></i>
            </div>
          `;
          
          preview.querySelector('.preview-overlay').addEventListener('click', () => {
            helpers.openImageModal(e.target.result, `Business Card ${title}`);
          });
        };
        reader.readAsDataURL(file);
      });
    },
    
    openImageModal: (src, title) => {
      let modal = document.getElementById('image-modal') || helpers.createModal();
      document.getElementById('modal-title').textContent = title;
      document.getElementById('modal-image').src = src;
      modal.style.display = 'block';
    },
    
    showToast: (message, type = 'info') => {
      if (!document.getElementById('toast-styles')) {
        const toastStyles = document.createElement('style');
        toastStyles.id = 'toast-styles';
        toastStyles.textContent = `
          .toast{position:fixed;top:2rem;right:2rem;background:white;padding:1rem 1.5rem;border-radius:var(--border-radius);box-shadow:var(--shadow-lg);display:flex;align-items:center;gap:0.75rem;z-index:9999;animation:slideInRight 0.3s ease-out;border-left:4px solid var(--primary-color)}
          .toast.toast-success{border-left-color:var(--success-color)}
          .toast i{color:var(--success-color)}
          @keyframes slideInRight{from{transform:translateX(100%);opacity:0}to{transform:translateX(0);opacity:1}}
        `;
        document.head.appendChild(toastStyles);
      }
      
      const toast = document.createElement('div');
      toast.className = `toast toast-${type}`;
      toast.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : 'info-circle'}"></i>
        <span>${message}</span>
      `;
      
      document.body.appendChild(toast);
      
      setTimeout(() => {
        toast.style.animation = 'slideInRight 0.3s ease-out reverse';
        setTimeout(() => document.body.removeChild(toast), 300);
      }, 3000);
    }
  };
  
  // Initialize image preview functionality
  helpers.setupImagePreview(elements.frontInput, elements.frontPreview, 'Front');
  helpers.setupImagePreview(elements.backInput, elements.backPreview, 'Back');
  
  // Setup blank back checkbox functionality
  if (elements.blankBackCheckbox && elements.backInput && elements.backPreview) {
    elements.blankBackCheckbox.addEventListener('change', function() {
      elements.backInput.disabled = this.checked;
      const container = this.closest('.blank-back-container');
      
      if (this.checked) {
        elements.backInput.value = '';
        elements.backPreview.innerHTML = '<div class="blank-back-indicator"><i class="fas fa-square"></i><span>Blank back side</span></div>';
        container.style.background = 'rgba(40, 167, 69, 0.05)';
        container.style.borderColor = 'var(--primary-color)';
      } else {
        container.style.background = 'white';
        container.style.borderColor = 'var(--border-color)';
        
        if (!elements.backInput.files || !elements.backInput.files[0]) {
          elements.backPreview.innerHTML = '<div class="preview-placeholder"><i class="fas fa-image"></i><span class="preview-text">Back side preview will appear here</span></div>';
        }
      }
    });
  }
  
  // Setup flip card functionality
  if (elements.flipCard && elements.showFrontBtn && elements.showBackBtn) {
    elements.showFrontBtn.addEventListener('click', () => {
      elements.flipCard.classList.remove('flipped');
      elements.showFrontBtn.classList.add('active');
      elements.showBackBtn.classList.remove('active');
    });
    
    elements.showBackBtn.addEventListener('click', () => {
      elements.flipCard.classList.add('flipped');
      elements.showBackBtn.classList.add('active');
      elements.showFrontBtn.classList.remove('active');
    });
  }
  
  // Enhanced button ripple effect
  if (elements.primaryButton) {
    elements.primaryButton.addEventListener('click', function(e) {
      const ripple = this.querySelector('.button-ripple');
      const rect = this.getBoundingClientRect();
      const size = Math.max(rect.width, rect.height);
      const x = e.clientX - rect.left - size / 2;
      const y = e.clientY - rect.top - size / 2;
      
      ripple.style.width = ripple.style.height = size + 'px';
      ripple.style.left = x + 'px';
      ripple.style.top = y + 'px';
      ripple.classList.add('animate');
      
      setTimeout(() => ripple.classList.remove('animate'), 600);
    });
  }
  
  // Drag and drop functionality
  elements.uploadContainers.forEach(container => {
    const input = container.querySelector('.file-input');
    const events = ['dragenter', 'dragover', 'dragleave', 'drop'];
    
    events.forEach(event => {
      container.addEventListener(event, e => {
        e.preventDefault();
        e.stopPropagation();
      });
    });
    
    ['dragenter', 'dragover'].forEach(event => {
      container.addEventListener(event, () => {
        container.style.borderColor = 'var(--primary-color)';
        container.style.background = 'rgba(40, 167, 69, 0.1)';
        container.style.transform = 'scale(1.02)';
      });
    });
    
    ['dragleave', 'drop'].forEach(event => {
      container.addEventListener(event, () => {
        container.style.borderColor = 'var(--border-color)';
        container.style.background = 'white';
        container.style.transform = 'scale(1)';
      });
    });
    
    container.addEventListener('drop', e => {
      const files = e.dataTransfer.files;
      if (files.length > 0) {
        input.files = files;
        input.dispatchEvent(new Event('change'));
      }
    });
  });
  
  // Handle form submission
  if (elements.businessCardForm && window.handymanDashboard) {
    elements.businessCardForm.addEventListener('submit', function(e) {
      e.preventDefault();
      
      const submitBtn = this.querySelector('.primary-button');
      const originalText = submitBtn.innerHTML;
      submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> <span>Uploading...</span>';
      submitBtn.disabled = true;
      
      window.handymanDashboard.handleBusinessCardSubmit(e);
      
      setTimeout(() => {
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
        
        if (elements.flipCard) {
          elements.flipCard.classList.remove('flipped');
          elements.showFrontBtn.classList.add('active');
          elements.showBackBtn.classList.remove('active');
        }
        
        helpers.showToast('Business card updated successfully!', 'success');
      }, 2000);
    });
  }
}); 