class Logger {
    constructor(moduleName) {
        this.moduleName = moduleName;
    }

    _log(level, message, data = null) {
        const timestamp = new Date().toLocaleString('ru-RU');
        const prefix = `[${timestamp}] [${level}] [${this.moduleName}]`;
        console.log(`${prefix} ${message}`);
        if (data) {
            if (data instanceof Error) {
                console.log(`  Ошибка: ${data.message}`);
                if (data.stack) console.log(`  Стек: ${data.stack}`);
            } else if (typeof data === 'object') {
                console.log(`  Данные:`, data);
            }
        }
    }

    debug(m, d) { this._log('DEBUG', m, d); }
    info(m, d) { this._log('INFO', m, d); }
    warn(m, d) { this._log('WARN', m, d); }
    error(m, d) { this._log('ERROR', m, d); }
}

export const log = {
    api: new Logger('API'),
    auth: new Logger('Auth'),
    events: new Logger('Events'),
    recs: new Logger('Recs'),
    user: new Logger('User'),
    router: new Logger('Router'),
};