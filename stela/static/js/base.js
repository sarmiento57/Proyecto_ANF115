// Define Nord palette
const nord = {
  nord0: '#2e3440',
  nord1: '#3b4252',
  nord2: '#4c566a', // your requested background
  nord3: '#ebcb8b', // line color
  nord4: '#d8dee9',
  white: '#ffffff'
};

document.addEventListener('DOMContentLoaded', function() {
    // --- Existing Company List Pop-up Logic ---
    const companiesButton = document.getElementById('btn-companies');
    const companiesPopup = document.getElementById('empresas-popup');

    function closeCompaniesPopupOutside(event) {
        if (!companiesButton.contains(event.target) && !companiesPopup.contains(event.target)) {
            companiesPopup.classList.add('d-none');
            document.removeEventListener('click', closeCompaniesPopupOutside);
        }
    }

    if (companiesButton && companiesPopup) {
        companiesButton.addEventListener('click', function(event) {
            event.preventDefault();
            companiesPopup.classList.toggle('d-none');
            event.stopPropagation();

            if (!companiesPopup.classList.contains('d-none')) {
                document.addEventListener('click', closeCompaniesPopupOutside);
            } else {
                document.removeEventListener('click', closeCompaniesPopupOutside);
            }
        });

        companiesPopup.addEventListener('click', function(event) {
            event.stopPropagation();
        });
    }


    // --- NEW Profile Pop-up Logic ---
    const profileButton = document.getElementById('btn-profile');
    const profilePopup = document.getElementById('profile-popup');

    function closeProfilePopupOutside(event) {
        // Check if the click was NOT on the button AND NOT inside the popup
        if (!profileButton.contains(event.target) && !profilePopup.contains(event.target)) {
            profilePopup.classList.add('d-none');
            // Remove the listener once closed
            document.removeEventListener('click', closeProfilePopupOutside);
        }
    }

    if (profileButton && profilePopup) {
        // 1. Toggle the pop-up when the "Nombre" button is clicked
        profileButton.addEventListener('click', function(event) {
            profilePopup.classList.toggle('d-none');
            event.stopPropagation(); // Prevent the click from immediately propagating to the document

            // Add listener to close when clicking outside
            if (!profilePopup.classList.contains('d-none')) {
                document.addEventListener('click', closeProfilePopupOutside);
            } else {
                document.removeEventListener('click', closeProfilePopupOutside);
            }
        });

        // 2. Prevent clicks inside the popup from propagating and closing it
        profilePopup.addEventListener('click', function(event) {
            event.stopPropagation();
        });
    }

    // Initialize Lucide icons (kept for completeness, assuming it's still needed)
    lucide.createIcons();
});