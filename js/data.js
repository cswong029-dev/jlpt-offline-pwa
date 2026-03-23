(function (global) {
  async function fetchJson(path) {
    const res = await fetch(path, { cache: 'no-cache' });
    if (!res.ok) throw new Error(`無法載入 ${path}`);
    return res.json();
  }

  async function loadMergedData(enabledPackIds) {
    const registry = await fetchJson('data/registry.json');
    const merged = { vocab: [], grammar: [], quizzes: [], reading: [], listening: [] };
    const allow =
      enabledPackIds && enabledPackIds.length
        ? new Set(enabledPackIds)
        : new Set(registry.packs.map((p) => p.id));

    for (const pack of registry.packs) {
      if (!allow.has(pack.id)) continue;
      const base = pack.basePath.replace(/\/?$/, '/');
      const files = pack.files || {};

      if (files.vocab) {
        const data = await fetchJson(base + files.vocab);
        (data.items || []).forEach((it) => merged.vocab.push({ ...it, _packId: pack.id }));
      }
      if (files.grammar) {
        const data = await fetchJson(base + files.grammar);
        (data.items || []).forEach((it) => merged.grammar.push({ ...it, _packId: pack.id }));
      }
      if (files.quizzes) {
        const data = await fetchJson(base + files.quizzes);
        (data.items || []).forEach((it) => merged.quizzes.push({ ...it, _packId: pack.id }));
      }
      if (files.reading) {
        const data = await fetchJson(base + files.reading);
        (data.items || []).forEach((it) => merged.reading.push({ ...it, _packId: pack.id }));
      }
      if (files.listening) {
        const data = await fetchJson(base + files.listening);
        (data.items || []).forEach((it) => merged.listening.push({ ...it, _packId: pack.id }));
      }
    }

    return { registry, merged };
  }

  function filterByLevels(items, levelsSet) {
    if (!levelsSet || levelsSet.size === 0) return items.slice();
    return items.filter((it) => levelsSet.has(it.level));
  }

  function normalizeQuery(q) {
    return (q || '').trim().toLowerCase();
  }

  function levelMatch(it, levelsSet) {
    if (!levelsSet || levelsSet.size === 0) return true;
    return levelsSet.has(it.level);
  }

  function searchAll(merged, q, levelsSet) {
    const nq = normalizeQuery(q);
    if (!nq) return null;
    const hit = (text) => (text || '').toLowerCase().includes(nq);

    return {
      grammar: merged.grammar.filter(
        (it) =>
          levelMatch(it, levelsSet) &&
          (hit(it.title) || hit(it.summary) || hit(it.body) || hit(it.id))
      ),
      vocab: merged.vocab.filter(
        (it) =>
          levelMatch(it, levelsSet) &&
          (hit(it.word) ||
            hit(it.reading) ||
            hit(it.meaning) ||
            hit(it.meaningEn) ||
            hit(it.exampleJa) ||
            hit(it.id))
      ),
      quizzes: merged.quizzes.filter(
        (it) =>
          levelMatch(it, levelsSet) &&
          (hit(it.question) || hit(it.explanation) || hit(it.id))
      ),
      reading: merged.reading.filter(
        (it) =>
          levelMatch(it, levelsSet) &&
          (hit(it.title) ||
            hit(it.passageJa) ||
            hit(it.passageReading) ||
            hit(it.passageZh) ||
            hit(it.id))
      ),
      listening: (merged.listening || []).filter(
        (it) =>
          levelMatch(it, levelsSet) &&
          (hit(it.question) || hit(it.title) || hit(it.explanation) || hit(it.id))
      )
    };
  }

  global.JLPTData = {
    loadMergedData,
    filterByLevels,
    searchAll,
    normalizeQuery
  };
})(typeof window !== 'undefined' ? window : self);
