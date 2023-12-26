// document.getElementById("assigned-user-filter").addEventListener("change", applyFilters);
// document.getElementById("status-filter").addEventListener("change", applyFilters);

let currentPage = 1;
let assignedUserFilter = "";
let statusFilter = "";
let currentSearchQuery = "";

function renderConversation(conversation) {
  if (!conversation || conversation.length === 0) {
    return "N/A";
  }

  const lastMessage = conversation[conversation.length - 1];
  return lastMessage.text;
}

function updateQuestions(pageNumber = 1, searchQuery = currentSearchQuery) {
  const url = `/questions/json/?page=${pageNumber}&assigned_user=${assignedUserFilter}&status=${statusFilter}&search=${encodeURIComponent(
    searchQuery
  )}`;
  fetch(url)
    .then((response) => {
      if (!response.ok) {
        throw new Error("Ошибка сети при запросе данных");
      }
      return response.json();
    })
    .then((data) => {
      const questions = data.questions;
      let questionsHtml = questions
        .map((question) => {
          const lastMessageSnippet = question.last_message.length > 25
            ? question.last_message.slice(0, 25) + "..."
            : question.last_message;
          return `
            <tr class="table_tr">
              <th scope="row" class="question_table_string">${question.id}</th>
              <td class="question_table_string">
                ${question.student}
              </td>
              <td class="question_table_string">
                ${lastMessageSnippet}
              </td>
              <td class="question_table_string question_table_string_status" style="background-color: ${question.status_color};";>
                ${question.status_text}
              </td>
              <td class="question_table_string">${question.last_message_time}</td>
              <td class="question_table_string">${question.assigned_user}</td>
              <td class="question_table_string align-items-center">
                <a href="/view_question/${question.id}">
                  <i class="fas fa-eye"></i>
                </a>
              </td>
            </tr>
          `;
        })
        .join("");

      if (questions.length === 0) {
        questionsHtml =
          '<tr><td colspan="7" class="text-center">Нет вопросов</td></tr>';
      }

      document.getElementById("questions-table-body").innerHTML = questionsHtml;
      updatePagination(data.paginator, pageNumber || 1);
      sessionStorage.setItem("currentPage", pageNumber || 1);
      updateFilterOptions(data);
    })
    .catch((error) => {
      console.error("Ошибка:", error);
    });
}

function updatePagination(totalPages, currentPage) {
  const paginationContainer = document.getElementById("pagination-container");
  if (paginationContainer) {
    paginationContainer.innerHTML = "";

    if (totalPages > 1) {
      let paginationHtml = '<ul class="pagination">';

      for (let i = 1; i <= totalPages; i++) {
        paginationHtml += `<li class="page-item ${
          i === +currentPage ? "active" : ""
        }">
          <a class="page-link" href="#" data-page="${i}">${i}</a></li>`;
      }

      paginationHtml += "</ul>";
      paginationContainer.innerHTML = paginationHtml;

      // Добавим обработчик события для каждой страницы
      const pageLinks = paginationContainer.querySelectorAll(".page-link");
      pageLinks.forEach((link) => {
        link.addEventListener("click", () => {
          const page = link.dataset.page;
          updateQuestions(page);
        });
      });
    }
  }
}

function updateFilterOptions(data) {
  const assignedUserFilterSelect = document.getElementById(
    "assigned-user-filter"
  );
  const statusFilterSelect = document.getElementById("status-filter");

  if (
    !data ||
    !Array.isArray(data.assignedUser) ||
    !Array.isArray(data.status)
  ) {
    console.error("Ошибка: Некорректные данные для фильтров.", data);
    return;
  }

  // Сохраняем выбранные значения фильтров
  const selectedAssignedUser = assignedUserFilterSelect.value;
  const selectedStatus = statusFilterSelect.value;

  assignedUserFilterSelect.innerHTML = '<option value="">Все</option>';
  statusFilterSelect.innerHTML = '<option value="">Все</option>';

  data.assignedUser.forEach((user) => {
    const option = document.createElement("option");
    option.value = user;
    option.text = user;
    assignedUserFilterSelect.add(option);
  });

  data.status.forEach((status) => {
    const option = document.createElement("option");
    option.value = status.value;
    option.text = status.display;
    statusFilterSelect.add(option);
  });

  // Устанавливаем выбранные значения фильтров
  assignedUserFilterSelect.value = selectedAssignedUser;
  statusFilterSelect.value = selectedStatus;
}

const savedAssignedUserFilter =
  sessionStorage.getItem("assignedUserFilter") || "";
const savedStatusFilter = sessionStorage.getItem("statusFilter") || "";
updateQuestions(currentPage, savedAssignedUserFilter, savedStatusFilter);

setInterval(function () {
  updateQuestions(sessionStorage.getItem("currentPage"));
}, 5000);

function applyFilters() {
  assignedUserFilter = document.getElementById("assigned-user-filter").value;
  statusFilter = document.getElementById("status-filter").value;
  currentSearchQuery = document.querySelector('[name="search"]').value;
  updateQuestions(1, currentSearchQuery);
}

document
  .querySelector('[name="search"]')
  .addEventListener("input", function (e) {
    currentSearchQuery = e.target.value;
    updateQuestions(1, currentSearchQuery);
  });

function updateTotalQuestionsCount() {
  fetch("/get_total_questions_count/json")
    .then((response) => {
      if (!response.ok) {
        throw new Error("Ошибка сети при запросе данных");
      }
      return response.json();
    })
    .then((data) => {
      const totalQuestionsCount = data.total_questions_count;
      document.getElementById("total-questions-count").innerText =
        totalQuestionsCount;
    })
    .catch((error) => {
      console.error("Ошибка:", error);
    });
}

updateTotalQuestionsCount();

setInterval(function () {
  updateQuestions(sessionStorage.getItem("currentPage"), currentSearchQuery);
}, 5000);

updateFilterOptions();
