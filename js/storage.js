(function (global) {
  const STORAGE_KEY = 'jlpt_offline_v1';
  const INTERVALS_DAYS = [1, 3, 7, 14];

  function todayStr() {
    const d = new Date();
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${y}-${m}-${day}`;
  }

  function addDays(isoDateStr, days) {
    const [y, m, d] = isoDateStr.split('-').map(Number);
    const dt = new Date(y, m - 1, d);
    dt.setDate(dt.getDate() + days);
    const yy = dt.getFullYear();
    const mm = String(dt.getMonth() + 1).padStart(2, '0');
    const dd = String(dt.getDate()).padStart(2, '0');
    return `${yy}-${mm}-${dd}`;
  }

  const LEVEL_FILTER_KEYS = [
    'grammar',
    'vocab',
    'quiz',
    'reading',
    'listening',
    'review',
    'bookmarks'
  ];

  function allLevels() {
    return ['N5', 'N4', 'N3', 'N2', 'N1'];
  }

  function defaultLevelFilters() {
    const lv = allLevels();
    const o = {};
    LEVEL_FILTER_KEYS.forEach((k) => {
      o[k] = lv.slice();
    });
    return o;
  }

  function defaultState() {
    return {
      prefs: {
        dark: true,
        fontScale: 1,
        furigana: true,
        vocabDisplay: 'both',
        enabledLevels: ['N5', 'N4', 'N3', 'N2', 'N1'],
        levelFilters: defaultLevelFilters(),
        readingShowZh: true,
        enabledPacks: null,
        listeningDelayMs: 800,
        quizBranch: 'vocab'
      },
      favorites: { grammar: [], vocab: [], quiz: [], reading: [], listening: [] },
      mistakes: { quiz: {} },
      srs: {}
    };
  }

  function load() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return defaultState();
      const parsed = JSON.parse(raw);
      const base = defaultState();
      const mergedPrefs = { ...base.prefs, ...(parsed.prefs || {}) };
      const el = mergedPrefs.enabledLevels || base.prefs.enabledLevels;
      if (!mergedPrefs.levelFilters || typeof mergedPrefs.levelFilters !== 'object') {
        mergedPrefs.levelFilters = defaultLevelFilters();
        LEVEL_FILTER_KEYS.forEach((k) => {
          if (!mergedPrefs.levelFilters[k] || !mergedPrefs.levelFilters[k].length) {
            mergedPrefs.levelFilters[k] = el.slice();
          }
        });
      } else {
        LEVEL_FILTER_KEYS.forEach((k) => {
          if (!mergedPrefs.levelFilters[k] || !mergedPrefs.levelFilters[k].length) {
            mergedPrefs.levelFilters[k] = el.slice();
          }
        });
      }
      if (mergedPrefs.readingShowZh === undefined) mergedPrefs.readingShowZh = true;
      return {
        prefs: mergedPrefs,
        favorites: {
          grammar: parsed.favorites?.grammar || [],
          vocab: parsed.favorites?.vocab || [],
          quiz: parsed.favorites?.quiz || [],
          reading: parsed.favorites?.reading || [],
          listening: parsed.favorites?.listening || []
        },
        mistakes: { quiz: parsed.mistakes?.quiz || {} },
        srs: parsed.srs || {}
      };
    } catch {
      return defaultState();
    }
  }

  let state = load();

  function save() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  }

  function getPrefs() {
    return { ...state.prefs };
  }

  function setPrefs(partial) {
    state.prefs = { ...state.prefs, ...partial };
    save();
  }

  function isFavorite(type, id) {
    return (state.favorites[type] || []).includes(id);
  }

  function toggleFavorite(type, id) {
    if (!state.favorites[type]) state.favorites[type] = [];
    const arr = state.favorites[type];
    const i = arr.indexOf(id);
    if (i >= 0) arr.splice(i, 1);
    else arr.push(id);
    save();
  }

  function recordQuizMistake(quizId) {
    const n = state.mistakes.quiz[quizId] || 0;
    state.mistakes.quiz[quizId] = n + 1;
    save();
  }

  function clearMistakes() {
    state.mistakes.quiz = {};
    save();
  }

  function getMistakeQuizIds() {
    return Object.keys(state.mistakes.quiz).filter((id) => state.mistakes.quiz[id] > 0);
  }

  function scheduleVocabSrs(vocabId) {
    if (!state.srs[vocabId]) {
      state.srs[vocabId] = { stage: 0, next: todayStr() };
      save();
    }
  }

  function bumpSrsVocab(vocabId, remembered) {
    const cur = state.srs[vocabId];
    if (!cur) return;
    if (remembered) {
      const stage = Math.min(INTERVALS_DAYS.length - 1, (cur.stage || 0) + 1);
      const days = INTERVALS_DAYS[stage];
      state.srs[vocabId] = { stage, next: addDays(todayStr(), days) };
    } else {
      state.srs[vocabId] = { stage: 0, next: addDays(todayStr(), 1) };
    }
    save();
  }

  function removeSrsVocab(vocabId) {
    delete state.srs[vocabId];
    save();
  }

  function getDueVocabIds() {
    const t = todayStr();
    return Object.keys(state.srs).filter((id) => (state.srs[id].next || '') <= t);
  }

  function hasSrsVocab(id) {
    return Object.prototype.hasOwnProperty.call(state.srs, id);
  }

  function exportBundle() {
    return {
      version: 1,
      exportedAt: new Date().toISOString(),
      favorites: state.favorites,
      mistakes: state.mistakes,
      srs: state.srs,
      prefs: state.prefs
    };
  }

  function importBundle(data) {
    if (!data || typeof data !== 'object') throw new Error('invalid');
    state.favorites = {
      grammar: data.favorites?.grammar || [],
      vocab: data.favorites?.vocab || [],
      quiz: data.favorites?.quiz || [],
      reading: data.favorites?.reading || [],
      listening: data.favorites?.listening || []
    };
    state.mistakes = { quiz: data.mistakes?.quiz || {} };
    state.srs = data.srs || {};
    if (data.prefs) {
      state.prefs = { ...defaultState().prefs, ...data.prefs };
      const el = state.prefs.enabledLevels || defaultState().prefs.enabledLevels;
      if (!state.prefs.levelFilters || typeof state.prefs.levelFilters !== 'object') {
        state.prefs.levelFilters = defaultLevelFilters();
      }
      LEVEL_FILTER_KEYS.forEach((k) => {
        if (!state.prefs.levelFilters[k] || !state.prefs.levelFilters[k].length) {
          state.prefs.levelFilters[k] = el.slice();
        }
      });
      if (state.prefs.readingShowZh === undefined) state.prefs.readingShowZh = true;
    }
    save();
  }

  global.JLPTStorage = {
    load,
    getPrefs,
    setPrefs,
    isFavorite,
    toggleFavorite,
    recordQuizMistake,
    clearMistakes,
    getMistakeQuizIds,
    scheduleVocabSrs,
    bumpSrsVocab,
    removeSrsVocab,
    getDueVocabIds,
    hasSrsVocab,
    exportBundle,
    importBundle,
    todayStr,
    INTERVALS_DAYS,
    allLevels,
    defaultLevelFilters,
    LEVEL_FILTER_KEYS
  };
})(typeof window !== 'undefined' ? window : self);
