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

