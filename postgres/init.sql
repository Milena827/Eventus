CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    course INTEGER CHECK (course BETWEEN 1 AND 6),
    faculty VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE competences (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT
);

CREATE TABLE test_results (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    competence_id INTEGER NOT NULL REFERENCES competences(id) ON DELETE CASCADE,
    score INTEGER CHECK (score BETWEEN 200 AND 800),
    assessment_date DATE,
    UNIQUE(user_id, competence_id)
);

CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE interests (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    UNIQUE(user_id, category_id)
);

CREATE TABLE desired_skills (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    competence_id INTEGER NOT NULL REFERENCES competences(id) ON DELETE CASCADE,
    priority INTEGER CHECK (priority BETWEEN 1 AND 5) DEFAULT 1,
    UNIQUE(user_id, competence_id)
);

CREATE TABLE sources (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    url VARCHAR(500) NOT NULL,
    parser_type VARCHAR(50) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE events (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    url VARCHAR(500) NOT NULL,
    source_id INTEGER REFERENCES sources(id) ON DELETE SET NULL,
    event_date TIMESTAMP,
    location VARCHAR(500),
    format VARCHAR(20) DEFAULT 'offline' CHECK (format IN ('online', 'offline', 'hybrid')),
    image_url VARCHAR(500),
    status VARCHAR(20) DEFAULT 'active',
    UNIQUE(source_id, url)
);

CREATE TABLE event_competences (
    id SERIAL PRIMARY KEY,
    event_id INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    competence_id INTEGER NOT NULL REFERENCES competences(id) ON DELETE CASCADE,
    relevance INTEGER CHECK (relevance BETWEEN 1 AND 5),
    UNIQUE(event_id, competence_id)
);

CREATE TABLE event_categories (
    id SERIAL PRIMARY KEY,
    event_id INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    UNIQUE(event_id, category_id)
);

CREATE TABLE action_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE user_actions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    event_id INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    action_type_id INTEGER NOT NULL REFERENCES action_types(id) ON DELETE CASCADE,
    rating INTEGER CHECK (rating BETWEEN 1 AND 5),
    review_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- ЗАПОЛНЕНИЕ СПРАВОЧНИКОВ
-- ============================================

INSERT INTO competences (name, description) VALUES
('Анализ информации', 'Способность анализировать информацию и принимать решения'),
('Планирование', 'Умение планировать задачи и ресурсы'),
('Партнерство/сотрудничество', 'Способность работать в команде'),
('Коммуникативная грамотность', 'Навыки эффективного общения'),
('Клиентоориентированность', 'Понимание потребностей клиентов'),
('Стрессоустойчивость', 'Сохранение продуктивности в стрессовых ситуациях'),
('Эмоциональный интеллект', 'Понимание своих и чужих эмоций'),
('Ориентация на результат', 'Нацеленность на достижение целей'),
('Саморазвитие', 'Стремление к постоянному развитию'),
('Следование правилам', 'Соблюдение норм и процедур'),
('Лидерство', 'Умение вести за собой');

INSERT INTO categories (name) VALUES
('IT'),
('Спорт'),
('Наука'),
('Настольные игры'),
('Музыка'),
('Бизнес'),
('Искусство');

INSERT INTO action_types (name) VALUES
('view'),
('like'),
('going'),
('attended'),
('rate');

INSERT INTO sources (name, url, parser_type, is_active) VALUES
('VK: Точка кипения', 'https://vk.com/tochkatyumen', 'vk_api', true),
('VK: Центр карьеры ТюмГУ', 'https://vk.com/utmn_career', 'vk_api', true),
('ГородЗовёт Тюмень', 'https://gorodzovet.ru/tyumen/', 'html_parser', true),
('VisitTyumen', 'https://visittyumen.ru', 'html_parser', true),
('Мой-портал.ру', 'https://xn----8sbzkbmchku.xn--p1ai/kuda-skhodit/', 'html_parser', true);