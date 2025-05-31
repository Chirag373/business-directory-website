document.addEventListener('DOMContentLoaded', function() {
    const notificationIcon = document.getElementById('notification-icon');
    const notificationDropdown = document.getElementById('notification-dropdown');
    const notificationBadge = document.getElementById('notification-badge');

    if (!notificationIcon) return;

    // Function to fetch notifications
    function fetchNotifications() {
        fetch('/handyman/notifications/')
            .then(response => response.json())
            .then(data => {
                updateNotificationBadge(data.count);
                renderNotifications(data.notifications);
            })
            .catch(error => console.error('Error fetching notifications:', error));
    }

    // Update notification badge
    function updateNotificationBadge(count) {
        if (count > 0) {
            notificationBadge.textContent = count > 9 ? '9+' : count;
            notificationBadge.style.display = 'block';
        } else {
            notificationBadge.style.display = 'none';
        }
    }

    // Render notifications in dropdown
    function renderNotifications(notifications) {
        const notificationList = document.getElementById('notification-list');
        
        if (!notificationList) return;
        
        // Clear current notifications
        notificationList.innerHTML = '';
        
        if (notifications.length === 0) {
            notificationList.innerHTML = '<div class="notification-empty">No notifications yet</div>';
            return;
        }
        
        // Add new notifications
        notifications.forEach(notification => {
            const notificationItem = document.createElement('li');
            notificationItem.className = `notification-item ${!notification.is_read ? 'unread' : ''}`;
            notificationItem.dataset.id = notification.id;
            
            notificationItem.innerHTML = `
                <div class="notification-content">
                    <div class="notification-title">${notification.handyman_name}</div>
                    <div class="notification-message">${notification.message}</div>
                    <div class="notification-meta">
                        <span class="notification-time">${notification.date}</span>
                        <span class="notification-discount">${notification.discount}% Off</span>
                    </div>
                </div>
            `;
            
            notificationItem.addEventListener('click', function() {
                markAsRead(notification.id);
                this.classList.remove('unread');
            });
            
            notificationList.appendChild(notificationItem);
        });
    }

    // Mark notification as read
    function markAsRead(notificationId) {
        fetch(`/handyman/notifications/${notificationId}/read/`, {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Update badge count after marking as read
                const currentCount = parseInt(notificationBadge.textContent);
                if (currentCount > 1) {
                    updateNotificationBadge(currentCount - 1);
                } else {
                    updateNotificationBadge(0);
                }
            }
        })
        .catch(error => console.error('Error marking notification as read:', error));
    }

    // Toggle notification dropdown
    notificationIcon.addEventListener('click', function(e) {
        e.stopPropagation();
        notificationDropdown.classList.toggle('show');
        
        if (notificationDropdown.classList.contains('show')) {
            fetchNotifications();
        }
    });

    // Close dropdown when clicking outside
    document.addEventListener('click', function(e) {
        if (notificationDropdown.classList.contains('show') && 
            !notificationDropdown.contains(e.target) && 
            e.target !== notificationIcon) {
            notificationDropdown.classList.remove('show');
        }
    });

    // Initial fetch on page load
    fetchNotifications();

    // Refresh notifications every 2 minutes
    setInterval(fetchNotifications, 120000);
}); 