// Enhanced Grant Application Admin JavaScript

document.addEventListener('DOMContentLoaded', function() {
    
    // Add helpful tooltips and enhancements to the approved amount field
    const approvedAmountField = document.querySelector('#id_approved_amount');
    if (approvedAmountField) {
        
        // Add real-time calculation hints
        approvedAmountField.addEventListener('input', function() {
            const requestedAmount = parseInt(document.querySelector('#id_amount_requested')?.value || 0);
            const approvedAmount = parseInt(this.value || 0);
            
            // Remove any existing alerts
            const existingAlert = document.querySelector('.approval-amount-alert');
            if (existingAlert) existingAlert.remove();
            
            if (approvedAmount && requestedAmount) {
                const difference = approvedAmount - requestedAmount;
                const percentage = ((approvedAmount / requestedAmount) * 100).toFixed(0);
                
                let alertClass = 'amount-alert ';
                let alertText = '';
                
                if (difference === 0) {
                    alertClass += 'full';
                    alertText = `✓ Full Amount (100%)`;
                } else if (difference > 0) {
                    alertClass += 'bonus';
                    alertText = `↗ ${percentage}% (+$${difference.toLocaleString()})`;
                } else {
                    alertClass += 'partial';
                    alertText = `↘ ${percentage}% (-$${Math.abs(difference).toLocaleString()})`;
                }
                
                const alert = document.createElement('span');
                alert.className = alertClass + ' approval-amount-alert';
                alert.textContent = alertText;
                
                this.parentNode.appendChild(alert);
            }
        });
        
        // Add quick amount buttons
        const quickAmountsContainer = document.createElement('div');
        quickAmountsContainer.innerHTML = `
            <div style="margin-top: 10px;">
                <strong>Quick Amounts:</strong>
                <button type="button" class="quick-amount-btn" data-action="25">25%</button>
                <button type="button" class="quick-amount-btn" data-action="50">50%</button>
                <button type="button" class="quick-amount-btn" data-action="75">75%</button>
                <button type="button" class="quick-amount-btn" data-action="100">100%</button>
                <button type="button" class="quick-amount-btn" data-action="custom">$10K</button>
                <button type="button" class="quick-amount-btn" data-action="custom2">$15K</button>
            </div>
        `;
        
        // Style the quick buttons
        const style = document.createElement('style');
        style.textContent = `
            .quick-amount-btn {
                background: #007bff;
                color: white;
                border: none;
                padding: 4px 8px;
                margin: 2px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 12px;
            }
            .quick-amount-btn:hover {
                background: #0056b3;
            }
        `;
        document.head.appendChild(style);
        
        approvedAmountField.parentNode.appendChild(quickAmountsContainer);
        
        // Add event listeners to quick amount buttons
        document.querySelectorAll('.quick-amount-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const action = this.dataset.action;
                const requestedAmount = parseInt(document.querySelector('#id_amount_requested')?.value || 0);
                
                let amount = 0;
                if (action === 'custom') {
                    amount = 10000;
                } else if (action === 'custom2') {
                    amount = 15000;
                } else {
                    const percentage = parseInt(action);
                    amount = Math.round(requestedAmount * (percentage / 100));
                }
                
                approvedAmountField.value = amount;
                approvedAmountField.dispatchEvent(new Event('input'));
            });
        });
    }
    
    // Highlight important fields when status changes to approved
    const statusField = document.querySelector('#id_status');
    if (statusField) {
        statusField.addEventListener('change', function() {
            if (this.value === 'approved') {
                const approvedAmountRow = document.querySelector('.field-approved_amount');
                if (approvedAmountRow) {
                    approvedAmountRow.style.animation = 'pulse 2s infinite';
                    approvedAmountRow.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            }
        });
    }
    
    // Add CSS animation
    const pulseStyle = document.createElement('style');
    pulseStyle.textContent = `
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.02); }
            100% { transform: scale(1); }
        }
    `;
    document.head.appendChild(pulseStyle);
    
    // Add confirmation for large amounts
    const form = document.querySelector('#grantapplication_form');
    if (form) {
        form.addEventListener('submit', function(e) {
            const approvedAmount = parseInt(document.querySelector('#id_approved_amount')?.value || 0);
            const status = document.querySelector('#id_status')?.value;
            
            if (status === 'approved' && approvedAmount > 50000) {
                if (!confirm(`You are approving $${approvedAmount.toLocaleString()}. This is a large amount. Are you sure?`)) {
                    e.preventDefault();
                }
            }
        });
    }
});