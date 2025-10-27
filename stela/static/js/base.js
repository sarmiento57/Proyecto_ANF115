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
    const companiesButton = document.getElementById('btn-companies');
    const popup = document.getElementById('empresas-popup');

    // 1. Toggle the pop-up when the "Empresas" button is clicked
    companiesButton.addEventListener('click', function(event) {
        // Prevent the default link/button action (though not strictly necessary for this button)
        event.preventDefault();

        // Toggle the 'd-none' class to show/hide the pop-up
        popup.classList.toggle('d-none');

        // Stop the click event from propagating to the document body immediately
        event.stopPropagation();

        // Add a listener to close the pop-up when clicking outside
        if (!popup.classList.contains('d-none')) {
            document.addEventListener('click', closePopupOutside);
        } else {
            document.removeEventListener('click', closePopupOutside);
        }
    });

    // 2. Function to close the pop-up when clicking anywhere else on the document
    function closePopupOutside(event) {
        // Check if the click was NOT on the companies button AND NOT inside the pop-up itself
        if (!companiesButton.contains(event.target) && !popup.contains(event.target)) {
            popup.classList.add('d-none');
            // Remove the listener once it's closed to avoid unnecessary overhead
            document.removeEventListener('click', closePopupOutside);
        }
    }

    // 3. Optional: Prevent clicks inside the popup from closing it immediately
    popup.addEventListener('click', function(event) {
        event.stopPropagation();
    });
});