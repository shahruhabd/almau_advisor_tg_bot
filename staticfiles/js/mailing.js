window.onload = function() {
    // Получаем кнопку "Выбрать все"
    var selectAllButton = document.getElementById('select-all');
    var allChecked = false; // Состояние всех чекбоксов

    // При клике на кнопку "Выбрать все"
    selectAllButton.onclick = function() {
        // Получаем все чекбоксы с именем 'students'
        var checkboxes = document.getElementsByName('students');

        allChecked = !allChecked; // Инвертируем состояние

        // Переключаем состояние каждого чекбокса и класс кнопки
        for(var i = 0; i < checkboxes.length; i++) {
            checkboxes[i].checked = allChecked;
        }

        // Меняем класс кнопки в зависимости от состояния
        if (allChecked) {
            selectAllButton.classList.remove('btn-secondary');
            selectAllButton.classList.add('btn-primary');
        } else {
            selectAllButton.classList.remove('btn-primary');
            selectAllButton.classList.add('btn-secondary');
        }
    }

    // Функция для обновления состояния кнопки "Убрать все фильтры"
    function updateResetButtonState() {
        var searchParams = new URLSearchParams(window.location.search);
        var resetFiltersLink = document.getElementById('resetFilters');

        if (searchParams.has('search_query') || searchParams.has('course_filter')) {
            // Если есть параметры поиска, делаем ссылку активной
            resetFiltersLink.classList.remove('disabled');
        } else {
            // Иначе делаем ссылку неактивной
            resetFiltersLink.classList.add('disabled');
        }
    }

    // Вызываем функцию при загрузке страницы, чтобы установить правильное состояние кнопки
    updateResetButtonState();

    // Получаем поля фильтрации
    var searchQuery = document.querySelector('input[name="search_query"]');
    var courseFilter = document.querySelector('select[name="course_filter"]');
    var resetButton = document.getElementById('resetFilters');
    const genderFilter = document.querySelector('select[name="gender_filter"]');
    const departmentFilter = document.querySelector('select[name="department_filter"]');
    const searchButton = document.querySelector('button[type="submit"]');

    function updateSearchButtonState() {
        // Проверяем, заполнено ли хотя бы одно из полей
        if (searchQuery.value || courseFilter.value || genderFilter.value || departmentFilter.value) {
            searchButton.disabled = false; // Сделать кнопку активной
        } else {
            searchButton.disabled = true;  // Сделать кнопку неактивной
        }
    }

    // Добавляем слушателей событий на изменение фильтров
    searchQuery.addEventListener('input', updateSearchButtonState);
    courseFilter.addEventListener('change', updateSearchButtonState);
    genderFilter.addEventListener('change', updateSearchButtonState);
    departmentFilter.addEventListener('change', updateSearchButtonState);
    updateSearchButtonState();
    // Если на странице есть кнопка "Убрать все фильтры", устанавливаем её состояние
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