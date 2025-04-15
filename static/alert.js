// Custom Alert Function
function showAlert(message) {
    const alertModal = document.getElementById('customAlert');
    const alertMessage = document.getElementById('alertMessage');
    const closeButton = document.getElementById('alertClose');
    
    alertMessage.textContent = message;
    alertModal.style.display = 'flex';
    
    // Close button event
    closeButton.onclick = function() {
        alertModal.style.display = 'none';
    }
    
    // Close when clicking outside the alert box
    alertModal.onclick = function(e) {
        if (e.target === alertModal) {
            alertModal.style.display = 'none';
        }
    }
}

// Make the function available globally
window.showAlert = showAlert;