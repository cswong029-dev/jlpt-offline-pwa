(function (global) {
  let lastUtterance = null;

  function stripForSpeak(text) {
    if (!text) return '';
    return String(text)
      .replace(/\s*\/\s*/g, '、')
      .replace(/\s+/g, ' ')
      .trim();
  }

  function speakJa(text, options) {
    const t = stripForSpeak(text);
    if (!t) return Promise.resolve();
    if (!global.speechSynthesis) return Promise.resolve();

    return new Promise((resolve) => {
      try {
        global.speechSynthesis.cancel();
      } catch (_) {}
      const u = new SpeechSynthesisUtterance(t);
      u.lang = 'ja-JP';
      u.rate = (options && options.rate) || 0.92;
      u.pitch = (options && options.pitch) || 1;
      u.onend = () => resolve();
      u.onerror = () => resolve();
      lastUtterance = u;
      global.speechSynthesis.speak(u);
    });
  }

  function stop() {
    try {
      global.speechSynthesis.cancel();
    } catch (_) {}
  }

  global.JLPTTTS = { speakJa, stop, stripForSpeak };
})(typeof window !== 'undefined' ? window : self);
