export function formatDate(dateStr) {
    if (!dateStr) return 'Дата уточняется';
    const date = new Date(dateStr);
    return date.toLocaleDateString('ru-RU', {
        day: 'numeric',
        month: 'long',
        year: 'numeric',
    });
}

export function formatDateTime(dateStr) {
    if (!dateStr) return 'Дата уточняется';
    const date = new Date(dateStr);
    return date.toLocaleString('ru-RU', {
        day: 'numeric',
        month: 'long',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
    });
}

export function truncateText(text, maxLength = 100) {
    if (!text) return '';
    return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
}

export function cleanLocation(loc) {
    if (!loc) return 'Тюмень';
    if (typeof loc === 'string' && (loc.startsWith('{') || loc.startsWith("'city'"))) {
        try {
            const fixed = loc.replace(/'/g, '"').replace(/xa0/g, ' ').replace(/\\xa0/g, ' ');
            const obj = JSON.parse(fixed);
            const text = obj.text || obj.street || '';
            return text.replace(/xa0/g, ' ').trim() || 'Тюмень';
        } catch {
            return String(loc)
                .replace(/'/g, '')
                .replace(/xa0/g, ' ')
                .replace(/city:/g, '')
                .replace(/street:/g, '')
                .replace(/cityAlias:/g, '')
                .replace(/cityId:/g, '')
                .replace(/lat:/g, '')
                .replace(/lon:/g, '')
                .replace(/[{}]/g, '')
                .trim() || 'Тюмень';
        }
    }
    return String(loc).replace(/xa0/g, ' ');
}