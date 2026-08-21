function checkDbStatus() {
    fetch('/api/db_status')
        .then(response => {
            const dot = document.getElementById('db-status-dot');
            const text = document.getElementById('db-status-text');

            if (!dot || !text) return;

            if (response.ok) {
                dot.className = 'w-3 h-3 bg-green-500 rounded-full animate-pulse';
                text.textContent = 'SINCRO DB: ATTIVA';
            } else {
                dot.className = 'w-3 h-3 bg-red-500 rounded-full';
                text.textContent = 'SINCRO DB: OFFLINE';
            }
        })
        .catch(() => {
            const dot = document.getElementById('db-status-dot');
            const text = document.getElementById('db-status-text');
            if (dot && text) {
                dot.className = 'w-3 h-3 bg-red-500 rounded-full';
                text.textContent = 'SINCRO DB: OFFLINE';
            }
        });
}

document.addEventListener('DOMContentLoaded', () => {
    checkDbStatus();
    setInterval(checkDbStatus, 30000);
});