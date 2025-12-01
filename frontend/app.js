const API_URL = window.API_URL || 'http://localhost:8000';

function showPage(pageId) {
    document.querySelectorAll('.page').forEach(page => {
        page.classList.remove('active');
    });
    document.getElementById(pageId + '-page').classList.add('active');
    
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`[data-page="${pageId}"]`).classList.add('active');
}

function showTab(tabId) {
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    document.getElementById(tabId + '-tab').classList.add('active');
    
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`[data-tab="${tabId}"]`).classList.add('active');
}

function showMessage(elementId, message, type) {
    const element = document.getElementById(elementId);
    element.textContent = message;
    element.className = `message ${type}`;
    setTimeout(() => {
        element.className = 'message';
    }, 5000);
}

document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        showPage(btn.dataset.page);
    });
});

document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        showTab(btn.dataset.tab);
    });
});

document.getElementById('qa-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const question = document.getElementById('question').value;
    const answer = document.getElementById('answer').value;
    const submittedBy = document.getElementById('submitted-by').value;
    
    try {
        const response = await fetch(`${API_URL}/api/add-qa`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                question,
                answer,
                submitted_by: submittedBy || null
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            showMessage('add-message', 'Вопрос-ответ отправлен на обработку и ожидает аппрува', 'success');
            document.getElementById('qa-form').reset();
        } else {
            const error = await response.json();
            showMessage('add-message', `Ошибка: ${error.detail || 'Неизвестная ошибка'}`, 'error');
        }
    } catch (error) {
        showMessage('add-message', `Ошибка: ${error.message}`, 'error');
    }
});

document.getElementById('file-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const fileInput = document.getElementById('file-input');
    const file = fileInput.files[0];
    
    if (!file) {
        showMessage('add-message', 'Выберите файл', 'error');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch(`${API_URL}/api/import-csv`, {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            const data = await response.json();
            showMessage('add-message', `Успешно импортировано ${data.imported} записей`, 'success');
            fileInput.value = '';
        } else {
            const error = await response.json();
            showMessage('add-message', `Ошибка: ${error.detail || 'Неизвестная ошибка'}`, 'error');
        }
    } catch (error) {
        showMessage('add-message', `Ошибка: ${error.message}`, 'error');
    }
});

document.getElementById('voice-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const fileInput = document.getElementById('voice-input');
    const file = fileInput.files[0];
    
    if (!file) {
        showMessage('add-message', 'Выберите аудио файл', 'error');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch(`${API_URL}/api/process-voice`, {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            const data = await response.json();
            showMessage('add-message', 'Голосовое сообщение обработано и отправлено на аппрув', 'success');
            fileInput.value = '';
        } else {
            const error = await response.json();
            showMessage('add-message', `Ошибка: ${error.detail || 'Неизвестная ошибка'}`, 'error');
        }
    } catch (error) {
        showMessage('add-message', `Ошибка: ${error.message}`, 'error');
    }
});

document.getElementById('search-btn').addEventListener('click', async () => {
    const query = document.getElementById('search-input').value.trim();
    
    if (!query) {
        return;
    }
    
    const resultsDiv = document.getElementById('search-results');
    resultsDiv.innerHTML = '<div class="loading">Поиск...</div>';
    
    try {
        const response = await fetch(`${API_URL}/api/search`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query })
        });
        
        if (response.ok) {
            const data = await response.json();
            displaySearchResults(data.qa_pairs);
        } else {
            resultsDiv.innerHTML = '<div class="message error">Ошибка поиска</div>';
        }
    } catch (error) {
        resultsDiv.innerHTML = `<div class="message error">Ошибка: ${error.message}</div>`;
    }
});

document.getElementById('search-input').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        document.getElementById('search-btn').click();
    }
});

function displaySearchResults(qaPairs) {
    const resultsDiv = document.getElementById('search-results');
    
    if (qaPairs.length === 0) {
        resultsDiv.innerHTML = '<div class="message">Ничего не найдено</div>';
        return;
    }
    
    resultsDiv.innerHTML = qaPairs.map(qa => `
        <div class="qa-item">
            <h3>${escapeHtml(qa.question_processed || qa.question)}</h3>
            <p>${escapeHtml(qa.answer_processed || qa.answer)}</p>
        </div>
    `).join('');
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

async function loadPending() {
    const pendingList = document.getElementById('pending-list');
    pendingList.innerHTML = '<div class="loading">Загрузка...</div>';
    
    try {
        const response = await fetch(`${API_URL}/api/pending`);
        
        if (response.ok) {
            const data = await response.json();
            displayPending(data);
        } else {
            pendingList.innerHTML = '<div class="message error">Ошибка загрузки</div>';
        }
    } catch (error) {
        pendingList.innerHTML = `<div class="message error">Ошибка: ${error.message}</div>`;
    }
}

function displayPending(pendingItems) {
    const pendingList = document.getElementById('pending-list');
    
    if (pendingItems.length === 0) {
        pendingList.innerHTML = '<div class="message">Нет записей на аппрув</div>';
        return;
    }
    
    pendingList.innerHTML = pendingItems.map(item => `
        <div class="pending-item">
            <h3>Запись #${item.id}</h3>
            ${item.submitted_by ? `<p><strong>От:</strong> ${escapeHtml(item.submitted_by)}</p>` : ''}
            <p><strong>Дата:</strong> ${new Date(item.created_at).toLocaleString('ru-RU')}</p>
            
            <div class="original">
                <h4>Оригинал:</h4>
                <p><strong>Вопрос:</strong> ${escapeHtml(item.question)}</p>
                <p><strong>Ответ:</strong> ${escapeHtml(item.answer)}</p>
            </div>
            
            ${item.question_processed || item.answer_processed ? `
            <div class="processed">
                <h4>Обработано:</h4>
                ${item.question_processed ? `<p><strong>Вопрос:</strong> ${escapeHtml(item.question_processed)}</p>` : ''}
                ${item.answer_processed ? `<p><strong>Ответ:</strong> ${escapeHtml(item.answer_processed)}</p>` : ''}
            </div>
            ` : ''}
            
            <div class="actions">
                <button class="btn-approve" onclick="approveQA(${item.id})">Одобрить</button>
                <button class="btn-reject" onclick="rejectQA(${item.id})">Отклонить</button>
            </div>
        </div>
    `).join('');
}

async function approveQA(id) {
    try {
        const response = await fetch(`${API_URL}/api/approve/${id}`, {
            method: 'POST'
        });
        
        if (response.ok) {
            loadPending();
        } else {
            alert('Ошибка при одобрении');
        }
    } catch (error) {
        alert(`Ошибка: ${error.message}`);
    }
}

async function rejectQA(id) {
    if (!confirm('Вы уверены, что хотите отклонить эту запись?')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/api/reject/${id}`, {
            method: 'POST'
        });
        
        if (response.ok) {
            loadPending();
        } else {
            alert('Ошибка при отклонении');
        }
    } catch (error) {
        alert(`Ошибка: ${error.message}`);
    }
}

document.getElementById('refresh-pending').addEventListener('click', loadPending);

if (document.getElementById('admin-page').classList.contains('active')) {
    loadPending();
}

document.querySelector('[data-page="admin"]').addEventListener('click', () => {
    setTimeout(loadPending, 100);
});

async function loadUnanswered() {
    const unansweredList = document.getElementById('unanswered-list');
    unansweredList.innerHTML = '<div class="loading">Загрузка...</div>';
    
    try {
        const response = await fetch(`${API_URL}/api/slack/unanswered`);
        
        if (response.ok) {
            const data = await response.json();
            displayUnanswered(data);
        } else {
            unansweredList.innerHTML = '<div class="message error">Ошибка загрузки</div>';
        }
    } catch (error) {
        unansweredList.innerHTML = `<div class="message error">Ошибка: ${error.message}</div>`;
    }
}

function displayUnanswered(items) {
    const unansweredList = document.getElementById('unanswered-list');
    
    if (items.length === 0) {
        unansweredList.innerHTML = '<div class="message">Нет неотвеченных вопросов</div>';
        return;
    }
    
    unansweredList.innerHTML = items.map(item => `
        <div class="pending-item">
            <h3>Вопрос #${item.id}</h3>
            ${item.slack_user ? `<p><strong>Из Slack:</strong> ${escapeHtml(item.slack_user)}</p>` : ''}
            <p><strong>Дата:</strong> ${new Date(item.created_at).toLocaleString('ru-RU')}</p>
            
            <div class="original">
                <h4>Вопрос:</h4>
                <p>${escapeHtml(item.question)}</p>
            </div>
            
            <div class="form-group" style="margin-top: 15px;">
                <label for="answer-${item.id}">Ответ:</label>
                <textarea id="answer-${item.id}" rows="4" style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px;"></textarea>
            </div>
            
            <div class="actions">
                <button class="btn-approve" onclick="addAnswer(${item.id})">Добавить ответ</button>
            </div>
        </div>
    `).join('');
}

async function addAnswer(id) {
    const answerText = document.getElementById(`answer-${id}`).value.trim();
    
    if (!answerText) {
        alert('Введите ответ');
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/api/slack/qa/${id}/answer`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ answer: answerText })
        });
        
        if (response.ok) {
            loadUnanswered();
        } else {
            const error = await response.json();
            alert(`Ошибка: ${error.detail || 'Неизвестная ошибка'}`);
        }
    } catch (error) {
        alert(`Ошибка: ${error.message}`);
    }
}

document.getElementById('refresh-unanswered').addEventListener('click', loadUnanswered);

document.querySelector('[data-page="unanswered"]').addEventListener('click', () => {
    setTimeout(loadUnanswered, 100);
});

async function loadHistory() {
    const historyList = document.getElementById('history-list');
    historyList.innerHTML = '<div class="loading">Загрузка...</div>';
    
    try {
        const response = await fetch(`${API_URL}/api/log/questions?limit=100`);
        
        if (response.ok) {
            const data = await response.json();
            displayHistory(data);
        } else {
            historyList.innerHTML = '<div class="message error">Ошибка загрузки</div>';
        }
    } catch (error) {
        historyList.innerHTML = `<div class="message error">Ошибка: ${error.message}</div>`;
    }
}

function displayHistory(items) {
    const historyList = document.getElementById('history-list');
    const filter = document.getElementById('history-filter').value;
    
    let filteredItems = items;
    if (filter === 'answered') {
        filteredItems = items.filter(item => item.answers && item.answers.length > 0);
    } else if (filter === 'unanswered') {
        filteredItems = items.filter(item => !item.answers || item.answers.length === 0);
    }
    
    if (filteredItems.length === 0) {
        historyList.innerHTML = '<div class="message">Нет записей</div>';
        return;
    }
    
    const tableHtml = `
        <table class="history-table">
            <thead>
                <tr>
                    <th>Дата</th>
                    <th>Вопрос</th>
                    <th>Ответ</th>
                    <th>Источник</th>
                </tr>
            </thead>
            <tbody>
                ${filteredItems.map(item => {
                    const hasAnswer = item.answers && item.answers.length > 0;
                    const answerText = hasAnswer ? item.answers[0].text : '—';
                    const answerSource = hasAnswer ? item.answers[0].source : '';
                    
                    return `
                        <tr>
                            <td>${new Date(item.created_at).toLocaleString('ru-RU')}</td>
                            <td class="question-text" title="${escapeHtml(item.text)}">${escapeHtml(item.text)}</td>
                            <td class="answer-text ${hasAnswer ? 'status-answered' : 'status-unanswered'}" title="${escapeHtml(answerText)}">${escapeHtml(answerText)}</td>
                            <td>
                                <span class="source-badge ${item.source || ''}">${item.source || 'web'}</span>
                                ${answerSource ? `<span class="source-badge ${answerSource}">${answerSource}</span>` : ''}
                            </td>
                        </tr>
                    `;
                }).join('')}
            </tbody>
        </table>
    `;
    
    historyList.innerHTML = tableHtml;
}

document.getElementById('refresh-history').addEventListener('click', loadHistory);

document.getElementById('history-filter').addEventListener('change', () => {
    loadHistory();
});

document.querySelector('[data-page="history"]').addEventListener('click', () => {
    setTimeout(loadHistory, 100);
});

