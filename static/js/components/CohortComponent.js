// static/js/components/CohortComponent.js
document.addEventListener('alpine:init', () => {
    Alpine.data('CohortComponent', () => ({
        init() {
            // Initialize Chart.js or custom logic for cohort data
            console.log('CohortComponent initialized');
        },
    }));
});