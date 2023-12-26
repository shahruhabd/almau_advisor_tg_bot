window.onload = function() {
    var selectAllButton = document.getElementById('select-all');
    var allChecked = false;
    .0

    selectAllButton.onclick = function() {
        var checkboxes = document.getElementsByName('students');

        allChecked = !allChecked;

        for(var i = 0; i < checkboxes.length; i++) {
            checkboxes[i].checked = allChecked;
        }

        if (allChecked) {
            selectAllButton.classList.remove('btn-secondary');
            selectAllButton.classList.add('btn-primary');
        } else {
            selectAllButton.classList.remove('btn-primary');
            selectAllButton.classList.add('btn-secondary');
        }
    }

    function updateResetButtonState() {
        var searchParams = new URLSearchParams(window.location.search);
        var resetFiltersLink = document.getElementById('resetFilters');

        if (searchParams.has('search_query') || searchParams.has('course_filter')) {
            resetFiltersLink.classList.remove('disabled');
        } else {
            resetFiltersLink.classList.add('disabled');
        }
    }

    updateResetButtonState();

    var searchQuery = document.querySelector('input[name="search_query"]');
    var courseFilter = document.querySelector('select[name="course_filter"]');
    var resetButton = document.getElementById('resetFilters');
    const genderFilter = document.querySelector('select[name="gender_filter"]');
    const departmentFilter = document.querySelector('select[name="department_filter"]');
    const searchButton = document.querySelector('button[type="submit"]');

    function updateSearchButtonState() {
        if (searchQuery.value || courseFilter.value || genderFilter.value || departmentFilter.value) {
            searchButton.disabled = false; 
        } else {
            searchButton.disabled = true;  
        }
    }

    searchQuery.addEventListener('input', updateSearchButtonState);
    courseFilter.addEventListener('change', updateSearchButtonState);
    genderFilter.addEventListener('change', updateSearchButtonState);
    departmentFilter.addEventListener('change', updateSearchButtonState);
    updateSearchButtonState();
    if (resetButton) {
        resetButton.onclick = function() {
            searchQuery.value = '';
            courseFilter.value = '';
            updateResetButtonState();
        }
    }
}

document.addEventListener('DOMContentLoaded', (event) => {
    document.querySelectorAll('.btn-close').forEach(button => {
        button.addEventListener('click', (e) => {
            e.target.parentElement.classList.add('d-none');
        });
    });
});