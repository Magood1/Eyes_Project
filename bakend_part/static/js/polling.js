document.addEventListener('DOMContentLoaded', () => {
    const checkDiagnosisStatus = (url, element) => {
        fetch(url, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest', // To identify AJAX requests in Django if needed
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'SUCCESS' || data.status === 'FAILURE') {
                // Status has changed, reload the page to show the result
                window.location.reload();
            }
        })
        .catch(error => console.error('Error polling for status:', error));
    };

    // Find all elements that need polling
    document.querySelectorAll('[data-poll-url]').forEach(element => {
        const url = element.dataset.pollUrl;
        // Poll every 5 seconds
        setInterval(() => checkDiagnosisStatus(url, element), 5000);
    });
});