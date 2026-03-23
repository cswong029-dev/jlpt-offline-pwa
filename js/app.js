/* global JLPTStorage, JLPTData, JLPTTTS */
(function () {
  function esc(s) {
    const d = document.createElement('div');
    d.textContent = s == null ? '' : String(s);
    return d.innerHTML;
  }

  function $(id) {
    return document.getElementById(id);
  }

  const state = {
    registry: null,
    merged: null,
    tab: 'grammar',
    grammarDetailId: null,
    vocabIndex: 0,
    quizOrder: [],
    quizPos: 0,
    quizMistakesOnly: false,
    quizLocked: false,
    readingIdx: 0,
    readingQ: 0,
    listeningIdx: 0,
    listeningLocked: false,
    listeningLastChoice: null,
    overlayHtml: null
  };

  const ALL_LEVELS = ['N5', 'N4', 'N3', 'N2', 'N1'];

  function getLevelsSetFor(section) {
    const lf = JLPTStorage.getPrefs().levelFilters || {};
    const arr = lf[section];
    const use = arr && arr.length ? arr : ALL_LEVELS;
    return new Set(use);
  }

  function searchLevelsUnion() {
    const lf = JLPTStorage.getPrefs().levelFilters || {};
    const u = new Set();
    (JLPTStorage.LEVEL_FILTER_KEYS || []).forEach((k) => {
      const arr = lf[k];
      (arr && arr.length ? arr : ALL_LEVELS).forEach((lv) => u.add(lv));
    });
    return u;
  }

  function levelStripHtml(sectionKey) {
    const lf = JLPTStorage.getPrefs().levelFilters || {};
    const cur = lf[sectionKey];
    const active = cur && cur.length ? cur : ALL_LEVELS;
    const chips = ALL_LEVELS.map(
      (lv) =>
        `<label class="level-chip"><input type="checkbox" data-act="level-filter" data-section="${sectionKey}" value="${lv}" ${
          active.includes(lv) ? 'checked' : ''
        }/>${lv}</label>`
    ).join('');
    return `<div class="level-strip" data-level-strip="${sectionKey}">${chips}</div>`;
  }

  function packsAllowed() {
    const p = JLPTStorage.getPrefs().enabledPacks;
    if (!p || !p.length) return null;
    return p;
  }

  function filteredVocab() {
    return JLPTData.filterByLevels(state.merged.vocab, getLevelsSetFor('vocab'));
  }

  function filteredGrammar() {
    return JLPTData.filterByLevels(state.merged.grammar, getLevelsSetFor('grammar'));
  }

  function filteredQuizzes() {
    let list = JLPTData.filterByLevels(state.merged.quizzes, getLevelsSetFor('quiz'));
    const branch = JLPTStorage.getPrefs().quizBranch || 'vocab';
    list = list.filter((q) => (q.section || 'vocab') === branch);
    if (state.quizMistakesOnly) {
      const ids = new Set(JLPTStorage.getMistakeQuizIds());
      list = list.filter((q) => ids.has(q.id));
    }
    return list;
  }

  function filteredReading() {
    return JLPTData.filterByLevels(state.merged.reading, getLevelsSetFor('reading'));
  }

  function filteredListening() {
    const raw = (state.merged && state.merged.listening) || [];
    return JLPTData.filterByLevels(raw, getLevelsSetFor('listening'));
  }

  function applyPrefsToDom() {
    const prefs = JLPTStorage.getPrefs();
    document.documentElement.classList.toggle('dark', !!prefs.dark);
    document.documentElement.style.fontSize = `${16 * (prefs.fontScale || 1)}px`;
  }

  function setTab(tab) {
    state.tab = tab;
    state.grammarDetailId = null;
    state.overlayHtml = null;
    if (tab === 'quiz') rebuildQuizOrder();
    if (tab === 'listening') {
      state.listeningLocked = false;
      state.listeningLastChoice = null;
    }
    document.querySelectorAll('.nav-tabs button').forEach((b) => {
      b.classList.toggle('active', b.dataset.tab === tab);
    });
    window.location.hash = tab;
    renderMain();
  }

  function rebuildQuizOrder() {
    const list = filteredQuizzes();
    const idx = list.map((_, i) => i);
    for (let i = idx.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [idx[i], idx[j]] = [idx[j], idx[i]];
    }
    state.quizOrder = idx;
    state.quizPos = 0;
    state.quizLocked = false;
  }

  function playAudio(src) {
    if (!src || !String(src).trim()) return;
    const a = new Audio(src);
    a.play().catch(() => {});
  }

  function playOrTts(src, ttsText) {
    const s = src && String(src).trim();
    if (s) {
      if (window.JLPTTTS) JLPTTTS.stop();
      playAudio(s);
      return;
    }
    const t = ttsText && String(ttsText).trim();
    if (t && window.JLPTTTS) JLPTTTS.speakJa(t);
  }

  function openOverlay(html) {
    state.overlayHtml = html;
    renderOverlay();
  }

  function closeOverlay() {
    state.overlayHtml = null;
    const ov = $('overlay');
    if (ov) ov.classList.add('hidden');
  }

  function renderOverlay() {
    let ov = $('overlay');
    if (!ov) {
      ov = document.createElement('div');
      ov.id = 'overlay';
      ov.className = 'overlay hidden';
      ov.innerHTML =
        '<div class="overlay-inner" id="overlay-inner"></div>';
      ov.addEventListener('click', (e) => {
        if (e.target === ov) closeOverlay();
      });
      document.body.appendChild(ov);
    }
    if (!state.overlayHtml) {
      ov.classList.add('hidden');
      return;
    }
    ov.classList.remove('hidden');
    const inner = $('overlay-inner');
    inner.innerHTML = state.overlayHtml;
    inner.onclick = (e) => {
      const t = e.target.closest('[data-act]');
      if (!t) return;
      const act = t.dataset.act;
      if (act === 'close-overlay') {
        closeOverlay();
        return;
      }
      if (act === 'play') {
        playOrTts(t.dataset.src, t.dataset.tts);
        return;
      }
      if (act === 'fav-grammar') {
        JLPTStorage.toggleFavorite('grammar', t.dataset.id);
        const it = state.merged.grammar.find((x) => x.id === t.dataset.id);
        if (it) {
          state.overlayHtml = grammarDetailHtml(it);
          inner.innerHTML = state.overlayHtml;
        }
      }
    };
  }

  function renderMain() {
    const main = $('main');
    const prefs = JLPTStorage.getPrefs();

    if (state.tab === 'grammar') main.innerHTML = renderGrammarView();
    else if (state.tab === 'vocab') main.innerHTML = renderVocabView(prefs);
    else if (state.tab === 'quiz') main.innerHTML = renderQuizView();
    else if (state.tab === 'reading') main.innerHTML = renderReadingView(prefs);
    else if (state.tab === 'review') main.innerHTML = renderSrsView();
    else if (state.tab === 'bookmarks') main.innerHTML = renderBookmarksView();
    else if (state.tab === 'listening') main.innerHTML = renderListeningView();
    else if (state.tab === 'settings') main.innerHTML = renderSettingsView();

    bindMainHandlers();
  }

  function renderGrammarView() {
    const items = filteredGrammar();
    const rows = items
      .map(
        (it) => `
      <li>
        <button type="button" class="item-btn" data-act="grammar-open" data-id="${esc(it.id)}">
          <span class="tag">${esc(it.level)}</span>${esc(it.title)}
          <div class="muted" style="margin-top:0.25rem;font-size:0.85rem;">${esc(it.summary || '')}</div>
        </button>
      </li>`
      )
      .join('');
    return `
      <section class="panel">
        <h2>文法</h2>
        ${levelStripHtml('grammar')}
        <p class="muted">在此勾選要顯示的 JLPT 級別（僅本頁）。點條目可看說明與例句；無 MP3 時可用 TTS。</p>
        <ul class="list">${rows || '<li><p class="muted">此篩選下沒有資料。</p></li>'}</ul>
      </section>`;
  }

  function grammarDetailHtml(it) {
    const fav = JLPTStorage.isFavorite('grammar', it.id);
    const ex = (it.examples || [])
      .map((e) => {
        const ap = e.audioPhrase && String(e.audioPhrase).trim();
        const ttsLine = (e.reading || e.ja || '').trim();
        return `
        <div class="panel" style="box-shadow:none;margin-bottom:0.5rem;">
          <p class="reading-passage">${esc(e.ja)}</p>
          ${
            prefsShowReading()
              ? `<p class="reading-ruby">${esc(e.reading || '')}</p>`
              : ''
          }
          <p class="muted">${esc(e.zh || '')}</p>
          <div class="btn-row" style="margin-top:0.35rem;">
            <button type="button" class="btn" data-act="play" data-src="${esc(ap)}" data-tts="${esc(ttsLine)}">聽例句（MP3 或語音）</button>
          </div>
        </div>`;
      })
      .join('');
    const bodyParas = (it.body || '')
      .split('\n')
      .filter(Boolean)
      .map((p) => `<p>${esc(p)}</p>`)
      .join('');
    return `
      <h2><span class="tag">${esc(it.level)}</span>${esc(it.title)}</h2>
      <p class="muted">${esc(it.summary || '')}</p>
      <div class="btn-row">
        <button type="button" class="btn ${fav ? 'primary' : ''}" data-act="fav-grammar" data-id="${esc(
      it.id
    )}">${fav ? '已收藏' : '收藏'}</button>
        <button type="button" class="btn" data-act="close-overlay">關閉</button>
      </div>
      <div style="margin-top:1rem;">${bodyParas}</div>
      <h3 style="margin-top:1rem;font-size:1rem;">例句</h3>
      ${ex || '<p class="muted">無例句</p>'}`;
  }

  function prefsShowReading() {
    return !!JLPTStorage.getPrefs().furigana;
  }

  function renderVocabView(prefs) {
    const list = filteredVocab();
    if (!list.length) {
      return `<section class="panel"><h2>單字卡</h2>${levelStripHtml('vocab')}<p class="muted">沒有符合等級的單字。</p></section>`;
    }
    if (state.vocabIndex >= list.length) state.vocabIndex = 0;
    const it = list[state.vocabIndex];
    const mode = prefs.vocabDisplay || 'both';
    let main = '';
    let sub = '';
    if (mode === 'both') {
      main = it.word || '';
      sub = it.reading || '';
    } else if (mode === 'kanji_only') {
      main = it.word || '';
      sub = '';
    } else {
      main = it.reading || '';
      sub = it.word && it.word !== it.reading ? it.word : '';
    }
    const aw = it.audioWord && String(it.audioWord).trim();
    const ae = it.audioExample && String(it.audioExample).trim();
    const fav = JLPTStorage.isFavorite('vocab', it.id);
    const inSrs = JLPTStorage.hasSrsVocab(it.id);
    const dueIds = new Set(JLPTStorage.getDueVocabIds());
    return `
      <section class="panel">
        <h2>單字卡 <span class="muted" style="font-weight:400;">(${state.vocabIndex + 1}/${list.length})</span></h2>
        ${levelStripHtml('vocab')}
        <div class="vocab-main">${esc(main)}</div>
        ${sub ? `<div class="vocab-sub">${esc(sub)}</div>` : ''}
        <p><strong>${esc(it.meaning || '')}</strong> <span class="muted">${esc(it.pos || '')}</span></p>
        ${
          it.meaningEn && it.meaning && it.meaningEn !== it.meaning
            ? `<p class="muted" style="font-size:0.85rem;">原文釋義（英）：${esc(it.meaningEn)}</p>`
            : ''
        }
        <p class="reading-passage">${esc(it.exampleJa || '')}</p>
        ${
          prefs.furigana
            ? `<p class="reading-ruby">${esc(it.exampleReading || '')}</p>`
            : ''
        }
        <p class="muted">${esc(it.exampleZh || '')}</p>
        <div class="btn-row">
          <button type="button" class="btn" data-act="play" data-src="${esc(aw)}" data-tts="${esc(
      (it.reading || it.word || '').trim()
    )}">單字讀音（MP3 或語音）</button>
          <button type="button" class="btn" data-act="play" data-src="${esc(ae)}" data-tts="${esc(
      (it.exampleReading || it.exampleJa || '').trim()
    )}" ${!it.exampleJa && !it.exampleReading ? 'disabled' : ''}>例句（MP3 或語音）</button>
        </div>
        <div class="btn-row">
          <button type="button" class="btn" data-act="vocab-prev">上一個</button>
          <button type="button" class="btn" data-act="vocab-next">下一個</button>
          <button type="button" class="btn ${fav ? 'primary' : ''}" data-act="fav-vocab">${fav ? '已收藏' : '收藏'}</button>
        </div>
        <div class="btn-row">
          <button type="button" class="btn primary" data-act="srs-add" data-id="${esc(it.id)}">排入間隔複習</button>
          ${
            inSrs
              ? `<span class="muted">${dueIds.has(it.id) ? '今日待複習' : '已排程'}</span>`
              : ''
          }
        </div>
      </section>`;
  }

  function currentQuiz() {
    const list = filteredQuizzes();
    if (!list.length) return null;
    if (!state.quizOrder.length) rebuildQuizOrder();
    const i = state.quizOrder[state.quizPos % state.quizOrder.length];
    return list[i];
  }

  function renderQuizView() {
    const list = filteredQuizzes();
    const q = currentQuiz();
    const modeLabel = state.quizMistakesOnly ? '錯題模式' : '全部';
    const branch = JLPTStorage.getPrefs().quizBranch || 'vocab';
    const branchLabel =
      branch === 'grammar' ? '言語知識（文法）' : '言語知識（文字・語彙）';
    if (!list.length || !q) {
      return `<section class="panel">
        <h2>模擬測驗（JLPT 形式）</h2>
        ${levelStripHtml('quiz')}
        <p class="muted">目前區塊沒有題目。${state.quizMistakesOnly ? '錯題本在此區為空。' : '請確認擴充包與等級篩選，或切換「語彙／文法」。'}</p>
        <div class="btn-row">
          <button type="button" class="btn ${branch === 'vocab' ? 'primary' : ''}" data-act="quiz-branch-vocab">語彙（読み・語彙）</button>
          <button type="button" class="btn ${branch === 'grammar' ? 'primary' : ''}" data-act="quiz-branch-grammar">文法（文の形式）</button>
          <button type="button" class="btn" data-act="quiz-toggle-mistakes">${state.quizMistakesOnly ? '改為全部' : '只練錯題'}</button>
        </div>
      </section>`;
    }
    const choices = (q.choices || []).map((c, idx) => {
      let cls = 'choice';
      if (state.quizLocked) {
        const ok = Number(q.correctIndex);
        if (idx === ok) cls += ' correct';
        else if (idx === state.quizLastChoice && idx !== ok) cls += ' wrong';
      }
      return `<button type="button" class="${cls}" data-act="quiz-pick" data-idx="${idx}" ${
        state.quizLocked ? 'disabled' : ''
      }>${esc(c)}</button>`;
    });
    const fav = JLPTStorage.isFavorite('quiz', q.id);
    const ttsQ = (q.ttsQuestion || '').trim();
    const jlptLine = q.jlptPart ? `<span class="muted">【${esc(q.jlptPart)}】</span> ` : '';
    return `
      <section class="panel">
        <h2>模擬測驗 · ${esc(branchLabel)}</h2>
        ${levelStripHtml('quiz')}
        <p class="muted" style="margin:0 0 0.5rem;">${jlptLine}${esc(modeLabel)} · 第 ${state.quizPos + 1} / ${
      state.quizOrder.length
    } 題</p>
        <div class="btn-row" style="margin-top:0;">
          <button type="button" class="btn ${branch === 'vocab' ? 'primary' : ''}" data-act="quiz-branch-vocab">語彙（読み・語彙）</button>
          <button type="button" class="btn ${branch === 'grammar' ? 'primary' : ''}" data-act="quiz-branch-grammar">文法（文の形式）</button>
          <button type="button" class="btn" data-act="quiz-toggle-mistakes">${state.quizMistakesOnly ? '改為全部' : '只練錯題'}</button>
          <button type="button" class="btn" data-act="quiz-shuffle">重新洗牌</button>
        </div>
        <div class="btn-row">
          <button type="button" class="btn" data-act="quiz-tts-q" data-tts="${esc(ttsQ)}" ${
      ttsQ ? '' : 'disabled'
    }>聽題幹（日文語音）</button>
        </div>
        <p class="reading-passage" style="margin-top:0.75rem;">${esc(q.question)}</p>
        <div>${choices.join('')}</div>
        ${
          state.quizLocked
            ? `<div class="explanation-box"><strong>解釋</strong><br>${esc(q.explanation || '')}</div>`
            : ''
        }
        <div class="btn-row">
          <button type="button" class="btn ${fav ? 'primary' : ''}" data-act="fav-quiz" data-id="${esc(q.id)}">${fav ? '已收藏題目' : '收藏題目'}</button>
          <button type="button" class="btn" data-act="quiz-next" ${!state.quizLocked ? 'disabled' : ''}>下一題</button>
        </div>
      </section>`;
  }

  function renderReadingView(prefs) {
    const list = filteredReading();
    if (!list.length) {
      return `<section class="panel"><h2>閱讀</h2>${levelStripHtml('reading')}<p class="muted">沒有閱讀材料。</p></section>`;
    }
    if (state.readingIdx >= list.length) state.readingIdx = 0;
    const it = list[state.readingIdx];
    const qs = it.questions || [];
    if (state.readingQ >= qs.length) state.readingQ = 0;
    const rq = qs[state.readingQ];
    const showZh = JLPTStorage.getPrefs().readingShowZh !== false;
    return `
      <section class="panel">
        <h2>閱讀 <span class="muted" style="font-weight:400;">${state.readingIdx + 1}/${list.length}</span></h2>
        ${levelStripHtml('reading')}
        <p class="muted">${esc(it.title || '')} <span class="tag">${esc(it.level)}</span> · 篇幅隨級數遞增（N5 最短→N1 最長）</p>
        <label class="muted" style="display:flex;align-items:center;gap:0.35rem;margin:0.25rem 0 0.5rem;">
          <input type="checkbox" data-act="toggle-read-zh" ${showZh ? 'checked' : ''}/> 顯示中文翻譯
        </label>
        <p class="reading-passage">${esc(it.passageJa || '')}</p>
        ${
          prefs.furigana
            ? `<p class="reading-ruby">${esc(it.passageReading || '')}</p>`
            : ''
        }
        ${showZh ? `<p class="muted reading-zh-block">${esc(it.passageZh || '')}</p>` : ''}
        <div class="btn-row">
          <button type="button" class="btn" data-act="read-tts" data-tts="${esc(
            (it.passageReading || it.passageJa || '').trim()
          )}">聽正文（語音）</button>
          <button type="button" class="btn" data-act="read-prev">上一篇</button>
          <button type="button" class="btn" data-act="read-next">下一篇</button>
          <button type="button" class="btn ${JLPTStorage.isFavorite('reading', it.id) ? 'primary' : ''}" data-act="fav-reading">${JLPTStorage.isFavorite('reading', it.id) ? '已收藏' : '收藏本篇'}</button>
        </div>
        ${
          rq
            ? `<div class="panel" style="margin-top:0.75rem;">
          <h3 style="font-size:1rem;margin:0 0 0.5rem;">理解題</h3>
          ${qs.length > 1 ? `<p class="muted" style="margin:0 0 0.5rem;">第 ${state.readingQ + 1} / ${qs.length} 題</p>` : ''}
          <p>${esc(rq.question)}</p>
          ${(rq.choices || [])
            .map(
              (c, idx) =>
                `<button type="button" class="btn" style="display:block;width:100%;margin-bottom:0.35rem;text-align:left;" data-act="read-pick" data-idx="${idx}">${esc(
                  c
                )}</button>`
            )
            .join('')}
          <div id="read-explain" class="hidden"></div>
          ${
            qs.length > 1
              ? `<div class="btn-row" style="margin-top:0.5rem;">
            <button type="button" class="btn" data-act="read-q-prev" ${state.readingQ <= 0 ? 'disabled' : ''}>上一題</button>
            <button type="button" class="btn" data-act="read-q-next" ${
              state.readingQ >= qs.length - 1 ? 'disabled' : ''
            }>下一題</button>
          </div>`
              : ''
          }
        </div>`
            : ''
        }
      </section>`;
  }

  function renderSrsView() {
    const due = JLPTStorage.getDueVocabIds();
    const rev = getLevelsSetFor('review');
    const list = state.merged.vocab.filter((v) => due.includes(v.id) && rev.has(v.level));
    const rows = list
      .map((v) => {
        return `<li style="padding:0.6rem 0;border-bottom:1px solid var(--border);">
        <strong>${esc(v.word)}</strong> <span class="muted">${esc(v.reading || '')}</span>
        <div class="btn-row" style="margin:0.35rem 0 0;">
          <button type="button" class="btn primary" data-act="srs-ok" data-id="${esc(v.id)}">記得 · 往後排</button>
          <button type="button" class="btn" data-act="srs-bad" data-id="${esc(v.id)}">不熟 · 明天再見</button>
          <button type="button" class="btn danger" data-act="srs-drop" data-id="${esc(v.id)}">移出複習</button>
        </div>
      </li>`;
      })
      .join('');
    return `
      <section class="panel">
        <h2>間隔複習</h2>
        ${levelStripHtml('review')}
        <p class="muted">排程：1 → 3 → 7 → 14 天。此處級別篩選僅影響「待複習清單」（與單字卡分頁可不同）。</p>
        <ul class="list" style="padding:0;">${rows || '<p class="muted">目前沒有待複習項目。</p>'}</ul>
      </section>`;
  }

  function resolveBookmark(type, id) {
    const m = state.merged;
    if (type === 'grammar') return m.grammar.find((x) => x.id === id);
    if (type === 'vocab') return m.vocab.find((x) => x.id === id);
    if (type === 'quiz') return m.quizzes.find((x) => x.id === id);
    if (type === 'reading') return m.reading.find((x) => x.id === id);
    if (type === 'listening') return (m.listening || []).find((x) => x.id === id);
    return null;
  }

  function renderBookmarksView() {
    const fav = JLPTStorage.load().favorites;
    const bmLv = getLevelsSetFor('bookmarks');
    const blocks = ['grammar', 'vocab', 'quiz', 'reading', 'listening'].map((t) => {
      const label = {
        grammar: '文法',
        vocab: '單字',
        quiz: '測驗',
        reading: '閱讀',
        listening: '聽力'
      }[t];
      const ids = fav[t] || [];
      const rows = ids
        .map((id) => {
          const it = resolveBookmark(t, id);
          if (!it)
            return `<li><span class="muted">（找不到 ${esc(id)}）</span> <button type="button" class="btn" data-act="fav-remove" data-type="${t}" data-id="${esc(id)}">移除</button></li>`;
          if (!bmLv.has(it.level)) return '';
          let title = it.title || it.word || it.question || it.id;
          return `<li style="display:flex;align-items:center;justify-content:space-between;gap:0.5rem;padding:0.5rem 0;border-bottom:1px solid var(--border);">
            <span><span class="tag">${esc(it.level)}</span>${esc(title)}</span>
            <span>
              <button type="button" class="btn" data-act="bm-open" data-type="${t}" data-id="${esc(id)}">開啟</button>
              <button type="button" class="btn" data-act="fav-remove" data-type="${t}" data-id="${esc(id)}">移除</button>
            </span>
          </li>`;
        })
        .join('');
      return `<div class="panel"><h3 style="margin-top:0;">${label}</h3><ul class="list" style="padding:0;">${
        rows || '<p class="muted">無</p>'
      }</ul></div>`;
    });
    return `<section class="panel"><h2>收藏</h2>${levelStripHtml('bookmarks')}<p class="muted">依級別篩選下列清單（不影響其他分頁）。</p></section>${blocks.join('')}`;
  }

  function renderListeningView() {
    const packs = (state.registry && state.registry.packs) || [];
    const withListen = packs.filter((p) => p.features && p.features.listening);
    const list = filteredListening();
    if (!list.length) {
      return `
      <section class="panel">
        <h2>聽力（擴充）</h2>
        ${levelStripHtml('listening')}
        <p class="muted">在擴充包的 <code>registry.json</code> 加入 <code>files.listening</code> 並提供對應 JSON（見 data/schema-notes.txt）。</p>
        <p class="muted">註冊表標記 <code>features.listening: true</code> 的套件：${
          withListen.length ? withListen.map((p) => esc(p.id)).join('、') : '（目前無）'
        }</p>
        <p class="muted">尚無聽力題目時，請先用「測驗」「閱讀」；有音檔後可按「播放題目音檔」。</p>
      </section>`;
    }
    if (state.listeningIdx >= list.length) state.listeningIdx = 0;
    const it = list[state.listeningIdx];
    const audio = it.audioPrompt && String(it.audioPrompt).trim();
    const correct = Number(it.correctIndex);
    const choices = (it.choices || []).map((c, idx) => {
      let cls = 'choice';
      if (state.listeningLocked) {
        if (idx === correct) cls += ' correct';
        else if (idx === state.listeningLastChoice && idx !== correct) cls += ' wrong';
      }
      return `<button type="button" class="${cls}" data-act="listen-pick" data-idx="${idx}" ${
        state.listeningLocked ? 'disabled' : ''
      }>${esc(c)}</button>`;
    });
    const fav = JLPTStorage.isFavorite('listening', it.id);
    const listenTts = (it.ttsQuestion || '').trim() || (it.question || '').replace(/（.*?）/g, '').trim();
    return `
      <section class="panel">
        <h2>聽力 <span class="muted" style="font-weight:400;">(${state.listeningIdx + 1}/${list.length})</span></h2>
        ${levelStripHtml('listening')}
        <p class="muted">${esc(it.title || '')} <span class="tag">${esc(it.level)}</span></p>
        <div class="btn-row">
          <button type="button" class="btn primary" data-act="listen-play" data-src="${esc(audio)}" data-tts="${esc(listenTts)}">聽題目（MP3 或語音）</button>
          <button type="button" class="btn" data-act="listen-prev">上一筆</button>
          <button type="button" class="btn" data-act="listen-next">下一筆</button>
        </div>
        <p class="reading-passage" style="margin-top:0.75rem;">${esc(it.question || '')}</p>
        <div>${choices.join('')}</div>
        ${
          state.listeningLocked
            ? `<div class="explanation-box"><strong>解釋</strong><br>${esc(it.explanation || '')}</div>`
            : ''
        }
        <div class="btn-row">
          <button type="button" class="btn ${fav ? 'primary' : ''}" data-act="listen-fav" data-id="${esc(it.id)}">${fav ? '已收藏' : '收藏題目'}</button>
          <button type="button" class="btn" data-act="listen-nextq" ${!state.listeningLocked ? 'disabled' : ''}>下一筆（已看解釋）</button>
        </div>
      </section>`;
  }

  function renderSettingsView() {
    const prefs = JLPTStorage.getPrefs();
    const levels = ['N5', 'N4', 'N3', 'N2', 'N1'];
    const master = prefs.enabledLevels || levels;
    const levelChecks = levels
      .map(
        (lv) => `
      <label style="display:inline-flex;align-items:center;margin-right:0.75rem;margin-bottom:0.35rem;">
        <input type="checkbox" data-act="sync-level-master" value="${lv}" ${
          master.includes(lv) ? 'checked' : ''
        }/> ${lv}
      </label>`
      )
      .join('');
    const packs = (state.registry && state.registry.packs) || [];
    const packChecks = packs
      .map((p) => {
        const all = !prefs.enabledPacks || !prefs.enabledPacks.length;
        const on = all || (prefs.enabledPacks || []).includes(p.id);
        return `<label style="display:flex;align-items:center;gap:0.35rem;margin-bottom:0.35rem;">
          <input type="checkbox" data-act="pack-toggle" value="${esc(p.id)}" ${on ? 'checked' : ''}/>
          ${esc(p.title)} (${esc(p.id)})
        </label>`;
      })
      .join('');
    return `
      <section class="panel">
        <h2>設定</h2>
        <div class="settings-block" id="settings-level-master">
          <label>一鍵同步全部區塊的級別</label>
          <p class="muted" style="margin:0 0 0.35rem;font-size:0.85rem;">文法、單字、測驗、閱讀、聽力、複習、收藏各分頁頂端可再單獨調整；此處為批次套用。</p>
          <div>${levelChecks}</div>
        </div>
        <div class="settings-block">
          <label>啟用擴充包（全不勾＝全部啟用）</label>
          ${packChecks || '<p class="muted">無套件</p>'}
        </div>
        <div class="settings-block">
          <label><input type="checkbox" data-act="toggle-dark" ${prefs.dark ? 'checked' : ''}/> 深色模式</label>
        </div>
        <div class="settings-block">
          <label>字體大小 ${prefs.fontScale || 1}x</label>
          <input type="range" min="0.85" max="1.35" step="0.05" value="${prefs.fontScale || 1}" data-act="font-range"/>
        </div>
        <div class="settings-block">
          <label><input type="checkbox" data-act="toggle-furigana" ${
            prefs.furigana ? 'checked' : ''
          }/> 顯示假名／讀音列（例句與閱讀）</label>
        </div>
        <div class="settings-block">
          <label>單字卡顯示</label>
          <select data-act="vocab-display">
            <option value="both" ${prefs.vocabDisplay === 'both' ? 'selected' : ''}>漢字＋讀音</option>
            <option value="kanji_only" ${prefs.vocabDisplay === 'kanji_only' ? 'selected' : ''}>僅漢字</option>
            <option value="reading_only" ${prefs.vocabDisplay === 'reading_only' ? 'selected' : ''}>僅讀音</option>
          </select>
        </div>
        <div class="btn-row">
          <button type="button" class="btn danger" data-act="clear-mistakes">清空錯題紀錄</button>
        </div>
        <div class="settings-block" style="margin-top:1rem;">
          <label>備份／還原</label>
          <div class="btn-row">
            <button type="button" class="btn primary" data-act="export-data">匯出 JSON</button>
            <label class="btn">匯入 JSON<input type="file" accept="application/json" class="hidden" data-act="import-file"/></label>
          </div>
        </div>
      </section>`;
  }

  function bindMainHandlers() {
    const main = $('main');
    if (!main) return;

    main.onclick = (e) => {
      const t = e.target.closest('[data-act]');
      if (!t) return;
      const act = t.dataset.act;

      if (act === 'grammar-open') {
        const id = t.dataset.id;
        const it = state.merged.grammar.find((x) => x.id === id);
        if (it) openOverlay(grammarDetailHtml(it));
        return;
      }
      if (act === 'close-overlay') {
        closeOverlay();
        return;
      }
      if (act === 'play') {
        playOrTts(t.dataset.src, t.dataset.tts);
        return;
      }
      if (act === 'quiz-branch-vocab') {
        JLPTStorage.setPrefs({ quizBranch: 'vocab' });
        rebuildQuizOrder();
        renderMain();
        return;
      }
      if (act === 'quiz-branch-grammar') {
        JLPTStorage.setPrefs({ quizBranch: 'grammar' });
        rebuildQuizOrder();
        renderMain();
        return;
      }
      if (act === 'quiz-tts-q') {
        playOrTts('', t.dataset.tts);
        return;
      }
      if (act === 'read-tts') {
        playOrTts('', t.dataset.tts);
        return;
      }
      if (act === 'fav-vocab') {
        JLPTStorage.toggleFavorite('vocab', filteredVocab()[state.vocabIndex].id);
        renderMain();
        return;
      }
      if (act === 'vocab-prev') {
        const list = filteredVocab();
        state.vocabIndex = (state.vocabIndex - 1 + list.length) % list.length;
        renderMain();
        return;
      }
      if (act === 'vocab-next') {
        const list = filteredVocab();
        state.vocabIndex = (state.vocabIndex + 1) % list.length;
        renderMain();
        return;
      }
      if (act === 'srs-add') {
        JLPTStorage.scheduleVocabSrs(t.dataset.id);
        renderMain();
        return;
      }
      if (act === 'quiz-toggle-mistakes') {
        state.quizMistakesOnly = !state.quizMistakesOnly;
        rebuildQuizOrder();
        renderMain();
        return;
      }
      if (act === 'quiz-shuffle') {
        rebuildQuizOrder();
        renderMain();
        return;
      }
      if (act === 'quiz-pick') {
        const q = currentQuiz();
        if (!q || state.quizLocked) return;
        const idx = Number(t.dataset.idx);
        state.quizLocked = true;
        state.quizLastChoice = idx;
        if (idx !== Number(q.correctIndex)) JLPTStorage.recordQuizMistake(q.id);
        renderMain();
        return;
      }
      if (act === 'fav-quiz') {
        JLPTStorage.toggleFavorite('quiz', t.dataset.id);
        renderMain();
        return;
      }
      if (act === 'quiz-next') {
        state.quizPos++;
        state.quizLocked = false;
        if (state.quizPos >= state.quizOrder.length) rebuildQuizOrder();
        renderMain();
        return;
      }
      if (act === 'read-prev') {
        const list = filteredReading();
        state.readingIdx = (state.readingIdx - 1 + list.length) % list.length;
        state.readingQ = 0;
        renderMain();
        return;
      }
      if (act === 'read-next') {
        const list = filteredReading();
        state.readingIdx = (state.readingIdx + 1) % list.length;
        state.readingQ = 0;
        renderMain();
        return;
      }
      if (act === 'fav-reading') {
        const list = filteredReading();
        const it = list[state.readingIdx];
        if (it) JLPTStorage.toggleFavorite('reading', it.id);
        renderMain();
        return;
      }
      if (act === 'read-pick') {
        const list = filteredReading();
        const it = list[state.readingIdx];
        const rq = (it.questions || [])[state.readingQ];
        if (!rq) return;
        const idx = Number(t.dataset.idx);
        const box = $('read-explain');
        if (box) {
          box.classList.remove('hidden');
          const ok = idx === Number(rq.correctIndex);
          box.innerHTML = `<div class="explanation-box"><strong>解釋</strong><br>${esc(
            rq.explanation || ''
          )}<br><span class="muted">${ok ? '答對了' : '可再對照上文'}</span></div>`;
        }
        return;
      }
      if (act === 'read-q-prev') {
        if (state.readingQ > 0) state.readingQ--;
        renderMain();
        return;
      }
      if (act === 'read-q-next') {
        const list = filteredReading();
        const n = (list[state.readingIdx].questions || []).length;
        if (state.readingQ < n - 1) state.readingQ++;
        renderMain();
        return;
      }
      if (act === 'listen-play') {
        playOrTts(t.dataset.src, t.dataset.tts);
        return;
      }
      if (act === 'listen-pick') {
        const list = filteredListening();
        const it = list[state.listeningIdx];
        if (!it || state.listeningLocked) return;
        const idx = Number(t.dataset.idx);
        state.listeningLocked = true;
        state.listeningLastChoice = idx;
        if (idx !== Number(it.correctIndex)) JLPTStorage.recordQuizMistake(it.id);
        renderMain();
        return;
      }
      if (act === 'listen-fav') {
        JLPTStorage.toggleFavorite('listening', t.dataset.id);
        renderMain();
        return;
      }
      if (act === 'listen-prev') {
        const list = filteredListening();
        state.listeningIdx = (state.listeningIdx - 1 + list.length) % list.length;
        state.listeningLocked = false;
        state.listeningLastChoice = null;
        renderMain();
        return;
      }
      if (act === 'listen-next' || act === 'listen-nextq') {
        const list = filteredListening();
        state.listeningIdx = (state.listeningIdx + 1) % list.length;
        state.listeningLocked = false;
        state.listeningLastChoice = null;
        renderMain();
        return;
      }
      if (act === 'srs-ok') {
        JLPTStorage.bumpSrsVocab(t.dataset.id, true);
        renderMain();
        return;
      }
      if (act === 'srs-bad') {
        JLPTStorage.bumpSrsVocab(t.dataset.id, false);
        renderMain();
        return;
      }
      if (act === 'srs-drop') {
        JLPTStorage.removeSrsVocab(t.dataset.id);
        renderMain();
        return;
      }
      if (act === 'fav-remove') {
        JLPTStorage.toggleFavorite(t.dataset.type, t.dataset.id);
        renderMain();
        return;
      }
      if (act === 'bm-open') {
        const type = t.dataset.type;
        const id = t.dataset.id;
        const it = resolveBookmark(type, id);
        if (!it) return;
        if (type === 'grammar') openOverlay(grammarDetailHtml(it));
        if (type === 'vocab') {
          const list = filteredVocab();
          const ix = list.findIndex((x) => x.id === id);
          if (ix >= 0) {
            state.vocabIndex = ix;
            setTab('vocab');
          }
        }
        if (type === 'quiz') {
          const full = state.merged.quizzes.find((x) => x.id === id);
          if (full && full.section === 'grammar') JLPTStorage.setPrefs({ quizBranch: 'grammar' });
          else JLPTStorage.setPrefs({ quizBranch: 'vocab' });
          rebuildQuizOrder();
          const list = filteredQuizzes();
          const ix = list.findIndex((x) => x.id === id);
          if (ix >= 0) {
            state.quizOrder = [ix];
            state.quizPos = 0;
            state.quizLocked = false;
            setTab('quiz');
          }
        }
        if (type === 'reading') {
          const list = filteredReading();
          const ix = list.findIndex((x) => x.id === id);
          if (ix >= 0) {
            state.readingIdx = ix;
            state.readingQ = 0;
            setTab('reading');
          }
        }
        if (type === 'listening') {
          const list = filteredListening();
          const ix = list.findIndex((x) => x.id === id);
          if (ix >= 0) {
            state.listeningIdx = ix;
            state.listeningLocked = false;
            state.listeningLastChoice = null;
            setTab('listening');
          }
        }
        return;
      }
      if (act === 'clear-mistakes') {
        if (confirm('確定清空錯題次數？')) JLPTStorage.clearMistakes();
        renderMain();
        return;
      }
      if (act === 'export-data') {
        const blob = new Blob([JSON.stringify(JLPTStorage.exportBundle(), null, 2)], {
          type: 'application/json'
        });
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = `jlpt-backup-${JLPTStorage.todayStr()}.json`;
        a.click();
        URL.revokeObjectURL(a.href);
        return;
      }
    };

    main.onchange = (e) => {
      const t = e.target;
      if (t.matches('[data-act="level-filter"]')) {
        const section = t.dataset.section;
        const strip = main.querySelector(`[data-level-strip="${section}"]`);
        if (strip) {
          const checked = [...strip.querySelectorAll('input[type="checkbox"]:checked')].map((i) => i.value);
          const nextLv = checked.length ? checked : ALL_LEVELS.slice();
          const lf = { ...(JLPTStorage.getPrefs().levelFilters || {}) };
          lf[section] = nextLv;
          JLPTStorage.setPrefs({ levelFilters: lf });
          if (state.tab === 'quiz') rebuildQuizOrder();
          renderMain();
        }
        return;
      }
      if (t.matches('[data-act="toggle-read-zh"]')) {
        JLPTStorage.setPrefs({ readingShowZh: t.checked });
        renderMain();
        return;
      }
      if (t.matches('[data-act="import-file"]') && t.files && t.files[0]) {
        const fr = new FileReader();
        fr.onload = () => {
          try {
            JLPTStorage.importBundle(JSON.parse(fr.result));
            applyPrefsToDom();
            alert('匯入完成');
            reloadDataAndRender();
          } catch {
            alert('匯入失敗：檔案格式不正確');
          }
        };
        fr.readAsText(t.files[0], 'UTF-8');
        t.value = '';
      }
      if (t.matches('[data-act="font-range"]')) {
        JLPTStorage.setPrefs({ fontScale: Number(t.value) });
        applyPrefsToDom();
      }
      if (t.matches('[data-act="vocab-display"]')) {
        JLPTStorage.setPrefs({ vocabDisplay: t.value });
        renderMain();
      }
    };

    main.querySelectorAll('[data-act="toggle-dark"]').forEach((el) => {
      el.onchange = () => {
        JLPTStorage.setPrefs({ dark: el.checked });
        applyPrefsToDom();
      };
    });
    main.querySelectorAll('[data-act="toggle-furigana"]').forEach((el) => {
      el.onchange = () => {
        JLPTStorage.setPrefs({ furigana: el.checked });
        renderMain();
      };
    });
    function applySyncLevelsFromSettings() {
      const box = $('main').querySelector('#settings-level-master');
      if (!box) return;
      const checked = [...box.querySelectorAll('[data-act="sync-level-master"]:checked')].map((i) => i.value);
      const lv = checked.length ? checked : ALL_LEVELS.slice();
      const lf = {};
      (JLPTStorage.LEVEL_FILTER_KEYS || []).forEach((k) => {
        lf[k] = lv.slice();
      });
      JLPTStorage.setPrefs({ enabledLevels: lv, levelFilters: lf });
      if (state.tab === 'quiz') rebuildQuizOrder();
      renderMain();
    }
    main.querySelectorAll('[data-act="sync-level-master"]').forEach((el) => {
      el.onchange = () => applySyncLevelsFromSettings();
    });
    main.querySelectorAll('[data-act="pack-toggle"]').forEach((el) => {
      el.onchange = () => {
        const packs = (state.registry && state.registry.packs) || [];
        const selected = [];
        main.querySelectorAll('[data-act="pack-toggle"]').forEach((box) => {
          if (box.checked) selected.push(box.value);
        });
        let next = selected;
        if (selected.length === 0 || selected.length === packs.length) next = null;
        JLPTStorage.setPrefs({ enabledPacks: next });
        reloadDataAndRender();
      };
    });
  }

  async function reloadDataAndRender() {
    const { registry, merged } = await JLPTData.loadMergedData(packsAllowed());
    state.registry = registry;
    state.merged = merged;
    rebuildQuizOrder();
    renderMain();
  }

  function renderSearchResults(q) {
    const res = JLPTData.searchAll(state.merged, q, searchLevelsUnion());
    if (!res) {
      $('search-hint').textContent = '';
      if ($('search-pop')) $('search-pop').innerHTML = '';
      return;
    }
    const total =
      res.grammar.length +
      res.vocab.length +
      res.quizzes.length +
      res.reading.length +
      (res.listening || []).length;
    $('search-hint').textContent = total ? `找到 ${total} 筆（請至各分頁瀏覽或點下方連結）` : '沒有符合的結果';
    const lines = [];
    res.grammar.slice(0, 5).forEach((it) => {
      lines.push(
        `<button type="button" class="btn" style="width:100%;margin-bottom:0.35rem;text-align:left;" data-jump="grammar" data-id="${esc(
          it.id
        )}">[文法] ${esc(it.title)}</button>`
      );
    });
    res.vocab.slice(0, 5).forEach((it) => {
      lines.push(
        `<button type="button" class="btn" style="width:100%;margin-bottom:0.35rem;text-align:left;" data-jump="vocab" data-id="${esc(
          it.id
        )}">[單字] ${esc(it.word)}</button>`
      );
    });
    res.quizzes.slice(0, 5).forEach((it) => {
      lines.push(
        `<button type="button" class="btn" style="width:100%;margin-bottom:0.35rem;text-align:left;" data-jump="quiz" data-id="${esc(
          it.id
        )}">[測驗] ${esc(it.question)}</button>`
      );
    });
    res.reading.slice(0, 5).forEach((it) => {
      lines.push(
        `<button type="button" class="btn" style="width:100%;margin-bottom:0.35rem;text-align:left;" data-jump="reading" data-id="${esc(
          it.id
        )}">[閱讀] ${esc(it.title || it.passageJa)}</button>`
      );
    });
    (res.listening || []).slice(0, 5).forEach((it) => {
      lines.push(
        `<button type="button" class="btn" style="width:100%;margin-bottom:0.35rem;text-align:left;" data-jump="listening" data-id="${esc(
          it.id
        )}">[聽力] ${esc(it.title || it.question)}</button>`
      );
    });
    const box = $('search-pop');
    if (box) box.innerHTML = lines.join('') || '<p class="muted">沒有結果</p>';
  }

  function bindSearch() {
    const input = $('global-search');
    if (!input) return;
    let timer;
    input.addEventListener('input', () => {
      clearTimeout(timer);
      timer = setTimeout(() => renderSearchResults(input.value), 200);
    });
    const pop = $('search-pop');
    if (pop) {
      pop.onclick = (e) => {
        const b = e.target.closest('[data-jump]');
        if (!b) return;
        const jump = b.dataset.jump;
        const id = b.dataset.id;
        if (jump === 'grammar') {
          const it = state.merged.grammar.find((x) => x.id === id);
          if (it) openOverlay(grammarDetailHtml(it));
        }
        if (jump === 'vocab') {
          const list = filteredVocab();
          const ix = list.findIndex((x) => x.id === id);
          if (ix >= 0) {
            state.vocabIndex = ix;
            setTab('vocab');
          }
        }
        if (jump === 'quiz') {
          const full = state.merged.quizzes.find((x) => x.id === id);
          if (full && full.section === 'grammar') JLPTStorage.setPrefs({ quizBranch: 'grammar' });
          else JLPTStorage.setPrefs({ quizBranch: 'vocab' });
          rebuildQuizOrder();
          const list = filteredQuizzes();
          const ix = list.findIndex((x) => x.id === id);
          if (ix >= 0) {
            state.quizOrder = [ix];
            state.quizPos = 0;
            state.quizLocked = false;
            setTab('quiz');
          }
        }
        if (jump === 'reading') {
          const list = filteredReading();
          const ix = list.findIndex((x) => x.id === id);
          if (ix >= 0) {
            state.readingIdx = ix;
            state.readingQ = 0;
            setTab('reading');
          }
        }
        if (jump === 'listening') {
          const list = filteredListening();
          const ix = list.findIndex((x) => x.id === id);
          if (ix >= 0) {
            state.listeningIdx = ix;
            state.listeningLocked = false;
            state.listeningLastChoice = null;
            setTab('listening');
          }
        }
      };
    }
  }

  function bindNav() {
    document.querySelectorAll('.nav-tabs button').forEach((b) => {
      b.addEventListener('click', () => setTab(b.dataset.tab));
    });
  }

  async function registerSw() {
    const hint = $('sw-hint');
    if (!('serviceWorker' in navigator)) {
      if (hint) hint.textContent = '此瀏覽器不支援 Service Worker，離線快取可能無法使用。';
      return;
    }
    try {
      const reg = await navigator.serviceWorker.register('./sw.js', { scope: './' });
      if (hint) hint.textContent = `離線快取：已註冊（${reg.active ? '作用中' : '啟用中'}）。`;
    } catch (err) {
      if (hint)
        hint.textContent =
          '離線快取未啟用（請用 http://localhost 或 https 開啟，勿用 file://）。';
    }
  }

  async function init() {
    applyPrefsToDom();
    bindNav();
    await reloadDataAndRender();
    bindSearch();

    const hash = (window.location.hash || '').replace('#', '');
    if (
      ['grammar', 'vocab', 'quiz', 'reading', 'review', 'bookmarks', 'listening', 'settings'].includes(
        hash
      )
    ) {
      setTab(hash);
    } else {
      setTab('grammar');
    }

    window.addEventListener('hashchange', () => {
      const h = (window.location.hash || '').replace('#', '');
      if (
        ['grammar', 'vocab', 'quiz', 'reading', 'review', 'bookmarks', 'listening', 'settings'].includes(
          h
        ) &&
        h !== state.tab
      ) {
        state.tab = h;
        document.querySelectorAll('.nav-tabs button').forEach((b) => {
          b.classList.toggle('active', b.dataset.tab === h);
        });
        renderMain();
      }
    });

    registerSw();
  }

  document.addEventListener('DOMContentLoaded', init);

  document.addEventListener('click', (e) => {
    if (e.target.id === 'overlay') closeOverlay();
  });
})();
