function updateChat() {
    const chatBox = document.querySelector('.chat-box');
    const questionId = chatBox.getAttribute('data-question-id'); // Убедитесь, что вы добавили атрибут data-question-id к div'у .chat-box

    fetch(`/get_chat_data/${questionId}/`)
        .then((response) => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then((data) => {
            let chatHtml = data.conversation.map((entry) => {
                return `
                    <div class="chat-message ${entry.type}">
                        <div>
                            ${entry.text}
                            <span class="timestamp">${entry.timestamp}</span>
                        </div>
                    </div>
                `;
            }).join('');

            if (data.conversation.length === 0) {
                chatHtml = '<p>Нет разговора</p>';
            }

            chatBox.innerHTML = chatHtml;

            // Прокручиваем чат в самый низ после обновления его содержимого
            chatBox.scrollTop = chatBox.scrollHeight;
        })
        .catch((error) => {
            console.error('Ошибка:', error);
        });
}

updateChat();
setInterval(updateChat, 3000); 


function insertText(text) {
    var input = document.getElementById('messageInput');
    input.value = text;
}
window.onload = function () {
    var chatBox = document.querySelector('.chat-box');
    chatBox.scrollTop = chatBox.scrollHeight;
};

document.addEventListener('DOMContentLoaded', function() {
    // Получаем textarea по его ID
    const messageInput = document.getElementById('messageInput');

    // Добавляем событие keydown к textarea
    messageInput.addEventListener('keydown', function(event) {
        // Проверяем, была ли нажата клавиша Enter и не удерживается ли клавиша Shift
        if (event.key === 'Enter' && !event.shiftKey) {
            // Отменяем стандартное действие (новая строка в textarea)
            event.preventDefault();

            // Находим ближайшую форму и отправляем ее
            // Вы также можете здесь выполнить любой AJAX-запрос, если нужно
            messageInput.closest('form').submit();
        }
    });
});