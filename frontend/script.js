const API_BASE = 'http://127.0.0.1:8000';
let currentToken = null;

// Утилиты для работы с API
async function apiRequest(endpoint, options = {}) {
    console.log(`Making request to: ${API_BASE}${endpoint}`);
    
    const url = `${API_BASE}${endpoint}`;
    const config = {
        headers: {
            'Content-Type': 'application/json',
            ...options.headers,
        },
        ...options,
    };

    if (currentToken) {
        config.headers['Authorization'] = `Bearer ${currentToken}`;
        console.log('Token added to request');
    }

    try {
        const response = await fetch(url, config);
        console.log(`Response status: ${response.status}`);
        
        if (response.status === 401) {
            logout();
            throw new Error('Требуется авторизация');
        }

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`HTTP ${response.status}: ${errorText}`);
        }

        const data = await response.json();
        console.log('Response data:', data);
        return data;
        
    } catch (error) {
        console.error('API Error:', error);
        showError(error.message);
        throw error;
    }
}

// Показать/скрыть секции
function showSection(sectionName) {
    console.log(`Showing section: ${sectionName}`);
    
    document.querySelectorAll('.content-section').forEach(section => {
        section.style.display = 'none';
    });
    
    const targetSection = document.getElementById(`${sectionName}Section`);
    if (targetSection) {
        targetSection.style.display = 'block';
    }
}

// Показать ошибку
function showError(message) {
    alert(`Ошибка: ${message}`);
}

// Логин
async function login() {
    console.log('Login function called');
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    console.log('Username:', username, 'Password:', password);

    if (!username || !password) {
        showError('Введите логин и пароль');
        return;
    }

    try {
        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);

        console.log('Sending login request...');
        
        const response = await fetch(`${API_BASE}/token`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: formData,
        });

        console.log('Login response status:', response.status);
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('Login error response:', errorText);
            throw new Error('Неверный логин или пароль');
        }

        const data = await response.json();
        console.log('Login success, token received');
        currentToken = data.access_token;

        localStorage.setItem('token', currentToken);
        
        document.getElementById('loginSection').style.display = 'none';
        document.getElementById('mainSection').style.display = 'block';
        document.getElementById('userName').textContent = username;

        await loadUserProfile();
        
    } catch (error) {
        console.error('Login error:', error);
        showError(error.message);
    }
}

// Загрузка профиля пользователя
async function loadUserProfile() {
    try {
        console.log('Loading user profile...');
        const userData = await apiRequest('/users/me');
        
        document.getElementById('profileInfo').innerHTML = `
            <div class="success">
                <p><strong>Имя пользователя:</strong> ${userData.name}</p>
                <p><strong>Роль:</strong> ${userData.role}</p>
            </div>
        `;

        if (userData.role === 'Преподаватель' || userData.role === 'Админ') {
            document.getElementById('teacherBtn').style.display = 'block';
        }

    } catch (error) {
        console.error('Error loading profile:', error);
        showError('Ошибка загрузки профиля');
    }
}

// Загрузка оценок студента
async function loadMyGrades() {
    try {
        console.log('Loading grades...');
        const grades = await apiRequest('/my_grades');
        const gradesList = document.getElementById('gradesList');
        
        if (grades.length === 0) {
            gradesList.innerHTML = '<p>У вас пока нет оценок</p>';
            return;
        }

        gradesList.innerHTML = grades.map(grade => `
            <div class="grade-item">
                <div class="grade-discipline">${grade.Дисциплина}</div>
                <div class="grade-value">Оценка: ${grade.Оценка}</div>
                <div class="grade-meta">
                    Преподаватель: ${grade.Учитель}<br>
                    Дата: ${new Date(grade['Дата оценки']).toLocaleDateString()}
                </div>
            </div>
        `).join('');

    } catch (error) {
        console.error('Error loading grades:', error);
        showError('Ошибка загрузки оценок');
    }
}

// Загрузка оценок группы (для преподавателей)
async function loadGroupGrades() {
    const groupName = document.getElementById('groupName').value;
    
    if (!groupName) {
        showError('Введите название группы');
        return;
    }

    try {
        console.log(`Loading grades for group: ${groupName}`);
        const grades = await apiRequest(`/teacher/grades/${groupName}`);
        const teacherContent = document.getElementById('teacherContent');
        
        if (grades.length === 0) {
            teacherContent.innerHTML = '<p>В этой группе пока нет оценок</p>';
            return;
        }

        teacherContent.innerHTML = `
            <h4>Оценки группы ${groupName}</h4>
            ${grades.map(grade => `
                <div class="grade-item">
                    <strong>${grade.Студент}</strong>: ${grade.Оценка}
                    <br><small>${new Date(grade.Дата).toLocaleDateString()}</small>
                </div>
            `).join('')}
        `;

    } catch (error) {
        console.error('Error loading group grades:', error);
        showError('Ошибка загрузки оценок группы');
    }
}

// Выход
function logout() {
    console.log('Logging out...');
    currentToken = null;
    localStorage.removeItem('token');
    document.getElementById('mainSection').style.display = 'none';
    document.getElementById('loginSection').style.display = 'block';
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing...');
    
    // Привязка событий к кнопкам
    document.getElementById('loginBtn').addEventListener('click', login);
    document.getElementById('logoutBtn').addEventListener('click', logout);
    document.getElementById('profileBtn').addEventListener('click', () => showSection('profile'));
    document.getElementById('gradesBtn').addEventListener('click', () => {
        showSection('grades');
        loadMyGrades();
    });
    document.getElementById('teacherBtn').addEventListener('click', () => showSection('teacher'));
    document.getElementById('loadGroupGradesBtn').addEventListener('click', loadGroupGrades);

    // Проверка авторизации при загрузке
    const savedToken = localStorage.getItem('token');
    
    if (savedToken) {
        console.log('Found saved token');
        currentToken = savedToken;
        document.getElementById('loginSection').style.display = 'none';
        document.getElementById('mainSection').style.display = 'block';
        loadUserProfile();
    } else {
        console.log('No saved token found');
    }
    
    console.log('Initialization complete');
});