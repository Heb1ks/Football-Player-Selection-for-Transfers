const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const source = fs.readFileSync(path.join(__dirname, '../app/static/app.js'), 'utf8');

function candidate(id = 1, season = 2023) {
    return {
        player_id: id, player_name: `Player ${id}`, season, position: 'Attack',
        origin_club: 'Origin', scenario_club: 'Destination', age: 23.5,
        pre_minutes: 1500, prediction: 0.3, persistence: 0.2, context_prediction: 0.25,
        model: 'individual_rf', key: `${id}-${season}-Destination-individual_rf`,
    };
}

function workspace(stored = '[]') {
    const elements = new Map();
    const requests = [];
    class Element {
        constructor() {
            this.value = '';
            this.attributes = {};
            this.style = {};
            this.children = [];
            this.elements = {season: {value: '2023'}};
        }
        set textContent(value) { this.text = String(value); this.children = []; }
        get textContent() { return this.text || ''; }
        setAttribute(name, value) { this.attributes[name] = value; }
        append(element) { this.children.push(element); }
        querySelectorAll() { return []; }
    }
    const element = selector => {
        if (!elements.has(selector)) elements.set(selector, new Element());
        return elements.get(selector);
    };
    element('#filters').values = {season: '2023', model: 'individual_rf'};
    const context = vm.createContext({
        document: {querySelector: element, querySelectorAll: () => [], createElement: () => new Element()},
        localStorage: {getItem: () => stored, setItem: (_key, value) => { stored = value; }},
        URLSearchParams,
        FormData: class { constructor(form) { return Object.entries(form.values); } },
        setTimeout: () => 0, clearTimeout: () => {},
        fetch: url => {
            if (url === '/api/meta') return new Promise(() => {});
            return new Promise(resolve => requests.push({url, resolve}));
        },
    });
    vm.runInContext(source + '\n;globalThis.snapshot=()=>({saved,rows,query:query.toString(),loading});', context);
    const snapshot = () => JSON.parse(JSON.stringify(context.snapshot()));
    const respond = (index, rows, ok = true) => requests[index].resolve({
        ok, json: async () => ok ? {rows, context: 'Recorded destination'} : {error: 'Request failed'},
    });
    return {context, element, requests, respond, snapshot};
}

test('malformed shortlist records cannot break candidate rendering', () => {
    for (const raw of ['{', 'null', '{}', '[null,42,"bad"]']) {
        const app = workspace(raw);
        assert.deepEqual(app.snapshot().saved, []);
        assert.doesNotThrow(() => app.context.renderSaved());
    }
    const good = candidate();
    const app = workspace(JSON.stringify([null, good, {...good, prediction: null}]));
    assert.deepEqual(app.snapshot().saved, [good]);
});

test('duplicate saved candidates are shown once', () => {
    const item = candidate();
    assert.equal(workspace(JSON.stringify([item, item])).snapshot().saved.length, 1);
});

test('out-of-order responses retain the latest pool and matching export parameters', async () => {
    const app = workspace();
    const first = app.context.load();
    assert.equal(app.element('#export').disabled, true);
    app.element('#filters').values = {season: '2024', model: 'formation_rf'};
    const second = app.context.load();
    app.respond(1, [candidate(2, 2024)]);
    await second;
    app.respond(0, [candidate(1, 2023)]);
    await first;
    assert.equal(app.snapshot().rows[0].player_id, 2);
    assert.equal(app.snapshot().query, 'season=2024&model=formation_rf');
    assert.equal(app.element('#export').disabled, false);
    assert.equal(app.element('.table-wrap').attributes['aria-busy'], 'false');
});

test('failed requests clear the pool and keep export unavailable', async () => {
    const app = workspace();
    const success = app.context.load();
    app.respond(0, [candidate()]);
    await success;
    const failure = app.context.load();
    app.respond(1, [], false);
    await failure;
    assert.deepEqual(app.snapshot().rows, []);
    assert.equal(app.element('#export').disabled, true);
    assert.equal(app.element('#error').hidden, false);
    assert.equal(app.element('#filters .primary').disabled, false);
});

test('export is unavailable when a name search hides every candidate', async () => {
    const app = workspace();
    const pending = app.context.load();
    app.respond(0, [candidate()]);
    await pending;
    app.element('#search').value = 'No such player';
    app.context.renderRows();
    assert.equal(app.element('#result-count').textContent, '0');
    assert.equal(app.element('#export').disabled, true);
});
