document.addEventListener('DOMContentLoaded', function() {
    const hamburger = document.querySelector('.hamburger');
    const mobileNav = document.querySelector('.mobile-nav');
    const navLinks = document.querySelectorAll('.mobile-nav-links a');

    if (hamburger) {
        hamburger.addEventListener('click', function() {
            mobileNav.classList.toggle('open');
            hamburger.classList.toggle('open'); // Add a class to hamburger for animation if needed
        });
    }

    // Close mobile nav when a link is clicked
    navLinks.forEach(link => {
        link.addEventListener('click', function() {
            mobileNav.classList.remove('open');
            if (hamburger) {
                hamburger.classList.remove('open');
            }
        });
    });

    // Optional: Close mobile nav if clicked outside (add if desired)
    // document.addEventListener('click', function(event) {
    //     if (!mobileNav.contains(event.target) && !hamburger.contains(event.target) && mobileNav.classList.contains('open')) {
    //         mobileNav.classList.remove('open');
    //         if (hamburger) {
    //             hamburger.classList.remove('open');
    //         }
    //     }
    // });
});

// SIP Calculator Logic (from your original code example)
document.addEventListener('DOMContentLoaded', () => {
    const monthlyInvestmentRange = document.getElementById('monthly-investment');
    const monthlyInvestmentValue = document.getElementById('investment-value');
    const returnRateRange = document.getElementById('return-rate');
    const returnRateValue = document.getElementById('return-value');
    const timePeriodRange = document.getElementById('time-period');
    const timePeriodValue = document.getElementById('year-value');
    const calculateBtn = document.getElementById('calculate-sip');
    const investedAmountDisplay = document.getElementById('invested-amount');
    const futureValueDisplay = document.getElementById('future-value');

    // Sync range and number inputs
    monthlyInvestmentRange.addEventListener('input', () => monthlyInvestmentValue.value = monthlyInvestmentRange.value);
    monthlyInvestmentValue.addEventListener('input', () => monthlyInvestmentRange.value = monthlyInvestmentValue.value);

    returnRateRange.addEventListener('input', () => returnRateValue.value = returnRateRange.value);
    returnRateValue.addEventListener('input', () => returnRateRange.value = returnRateValue.value);

    timePeriodRange.addEventListener('input', () => timePeriodValue.value = timePeriodRange.value);
    timePeriodValue.addEventListener('input', () => timePeriodRange.value = timePeriodValue.value);

    function calculateSIP() {
        const p = parseFloat(monthlyInvestmentValue.value); // Monthly investment
        const r = parseFloat(returnRateValue.value) / 100 / 12; // Monthly interest rate
        const n = parseFloat(timePeriodValue.value) * 12; // Total number of months

        if (isNaN(p) || isNaN(r) || isNaN(n) || p <= 0 || r <= 0 || n <= 0) {
            investedAmountDisplay.textContent = 'Invalid Input';
            futureValueDisplay.textContent = 'Invalid Input';
            return;
        }

        const futureValue = p * ((Math.pow(1 + r, n) - 1) / r) * (1 + r);
        const investedAmount = p * n;

        investedAmountDisplay.textContent = `₹${Math.round(investedAmount).toLocaleString('en-IN')}`;
        futureValueDisplay.textContent = `₹${Math.round(futureValue).toLocaleString('en-IN')}`;
    }

    // Initial calculation and update on input change
    [monthlyInvestmentRange, monthlyInvestmentValue, returnRateRange, returnRateValue, timePeriodRange, timePeriodValue].forEach(element => {
        element.addEventListener('input', calculateSIP);
    });

    calculateBtn.addEventListener('click', calculateSIP);

    // Perform initial calculation on load
    calculateSIP();
});