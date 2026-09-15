// reader.js — 单篇阅读页逻辑（意中双语 · 段落点读）
(function () {
  'use strict';
  var DATA = window.__GRIMM_INDEX__;
  var PREFS_KEY = 'grimm_prefs_v1';

  function $(id) { return document.getElementById(id); }
  function esc(s) {
    return (s || '').replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }
  function fmt(t) {
    if (!isFinite(t) || t < 0) t = 0;
    var m = Math.floor(t / 60), s = Math.floor(t % 60);
    return m + ':' + (s < 10 ? '0' : '') + s;
  }

  // ---------- prefs ----------
  var prefs = { mode: 'pair', fs: 19, cont: true, follow: true, loop: false, rate: 1 };
  try { var p = JSON.parse(localStorage.getItem(PREFS_KEY)); if (p) prefs = Object.assign(prefs, p); } catch (e) {}
  function savePrefs() { try { localStorage.setItem(PREFS_KEY, JSON.stringify(prefs)); } catch (e) {} }

  // ---------- routing & per-story data ----------
  function loadScript(src, cb) {
    var s = document.createElement('script');
    s.src = src;
    s.onload = function () { cb && cb(); };
    s.onerror = function () { cb && cb(new Error('load fail: ' + src)); };
    document.head.appendChild(s);
  }
  function store() {
    return window.__GRIMM_STORIES__ || (window.__GRIMM_STORIES__ = {});
  }
  function getStoryIdx() {
    var id = new URLSearchParams(location.search).get('id');
    var idx = DATA.stories.findIndex(function (s) { return s.id === id; });
    if (idx < 0) idx = 0;
    return idx;
  }
  var storyIdx = getStoryIdx();
  var sid = DATA.stories[storyIdx].id;
  var story = null, paras = null;   // filled by boot() after story data loads

  // ---------- sidebar ----------
  function renderSidebar() {
    var q = ($('sideSearch').value || '').trim().toLowerCase();
    var html = DATA.stories.map(function (s, i) {
      var on = i === storyIdx ? ' on' : '';
      var show = !q ||
        (s.title_it || '').toLowerCase().indexOf(q) >= 0 ||
        (s.title_zh || '').toLowerCase().indexOf(q) >= 0 ||
        s.id.indexOf(q) >= 0;
      if (!show) return '';
      return '<a class="' + on.trim() + '" data-go="' + i + '">' +
        '<span class="cn-no">' + s.id + '</span>' +
        '<span class="cn-it">' + esc(s.title_it) + '</span>' +
        '<span class="cn-zh">' + esc(s.title_zh) + '</span></a>';
    }).join('');
    $('storyNav').innerHTML = html;
    $('sideStats').innerHTML = '共 <b>' + DATA.stories.length + '</b> 篇 · 当前第 ' + (storyIdx + 1) + ' 篇';
  }
  $('storyNav').addEventListener('click', function (e) {
    var a = e.target.closest('[data-go]'); if (!a) return;
    location.href = 'lettura.html?id=' + encodeURIComponent(DATA.stories[+a.dataset.go].id);
  });
  $('sideSearch').addEventListener('input', renderSidebar);

  // ---------- content ----------
  function renderContent() {
    var head =
      '<div class="chapter-head">' +
      '<div class="ch-no">N. ' + story.id + ' / ' + DATA.stories.length + '</div>' +
      '<div class="ch-it">' + esc(story.title_it) + '</div>' +
      '<div class="ch-zh">' + esc(story.title_zh) + '</div></div>';
    var body = paras.map(function (p, i) {
      var zh = p.zh ? '<div class="zh-line">' + esc(p.zh) + '</div>' : '';
      return '<div class="para" data-idx="' + i + '">' +
        '<div class="para-bar"><span class="para-idx">§' + (i + 1) + '</span>' +
        '<button class="para-play" data-play="' + i + '">▶ 朗读</button>' +
        '<span class="para-noaudio" data-noaudio="' + i + '" style="display:none">未生成音频</span></div>' +
        '<div class="para-body">' +
        '<div class="it-line">' + esc(p.it) + '</div>' + zh + '</div></div>';
    }).join('');
    $('content').innerHTML = head + body;
    $('chapterFootLabel').textContent = '第 ' + (storyIdx + 1) + ' / ' + DATA.stories.length + ' 篇';
  }

  // ---------- mode / font / switches ----------
  function applyMode() {
    document.body.className = 'mode-' + prefs.mode;
    Array.prototype.forEach.call(document.querySelectorAll('#modeSeg button'), function (b) {
      b.classList.toggle('on', b.dataset.mode === prefs.mode);
    });
  }
  function applyFont() {
    document.documentElement.style.setProperty('--fs', prefs.fs + 'px');
  }
  $('modeSeg').addEventListener('click', function (e) {
    var b = e.target.closest('button'); if (!b) return;
    prefs.mode = b.dataset.mode; applyMode(); savePrefs();
  });
  $('btnFontUp').addEventListener('click', function () { prefs.fs = Math.min(28, prefs.fs + 1); applyFont(); savePrefs(); });
  $('btnFontDn').addEventListener('click', function () { prefs.fs = Math.max(15, prefs.fs - 1); applyFont(); savePrefs(); });
  $('chkCont').checked = prefs.cont;
  $('chkFollow').checked = prefs.follow;
  $('chkLoop').checked = prefs.loop;
  $('rate').value = prefs.rate; $('rateVal').textContent = (+prefs.rate).toFixed(2) + '×';
  $('chkCont').addEventListener('change', function () { prefs.cont = this.checked; savePrefs(); });
  $('chkFollow').addEventListener('change', function () { prefs.follow = this.checked; savePrefs(); });
  $('chkLoop').addEventListener('change', function () { prefs.loop = this.checked; savePrefs(); audio.loop = false; });

  // ---------- player ----------
  var audio = $('audio');
  var cur = -1;          // 当前段落
  var playing = false;

  // 自动滚动：仅当目标段落不在可视区内时才滚（不抢用户手动滚动）
  function scrollToPara(i) {
    if (!prefs.follow) return;
    var el = document.querySelector('.para[data-idx="' + i + '"]');
    var rd = $('reader');
    if (!el || !rd) return;
    var rr = rd.getBoundingClientRect();
    var er = el.getBoundingClientRect();
    var visible = er.top >= rr.top + 8 && er.bottom <= rr.bottom - 8;
    if (!visible) el.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }

  function setCur(i, opts) {
    opts = opts || {};
    if (!paras || i < 0 || i >= paras.length) return;
    cur = i;
    var p = paras[i];
    Array.prototype.forEach.call(document.querySelectorAll('.para'), function (el) {
      el.classList.toggle('playing', +el.dataset.idx === i);
    });
    $('readProgress').textContent = '§' + (i + 1) + ' / ' + paras.length;
    $('nowTitle').textContent = '§' + (i + 1) + '  ' + story.title_it;
    scrollToPara(i);
    audio.loop = false;
    audio.src = p.audio;
    try { audio.load(); } catch (e) {}
    if (opts.play) play();
  }
  function play() {
    if (cur < 0) { setCur(0, { play: false }); }
    audio.play().then(function () { playing = true; $('btnPlay').textContent = '❚❚'; })
      .catch(function () { playing = false; $('btnPlay').textContent = '▶'; });
  }
  function pause() { audio.pause(); playing = false; $('btnPlay').textContent = '▶'; }
  function toggle() { if (playing) pause(); else play(); }

  function markNoAudio(i) {
    var el = document.querySelector('[data-noaudio="' + i + '"]');
    if (el) el.style.display = 'inline';
    var pb = document.querySelector('[data-play="' + i + '"]');
    if (pb) pb.disabled = true;
  }

  $('btnPlay').addEventListener('click', toggle);
  $('btnPrevPara').addEventListener('click', function () { if (cur > 0) setCur(cur - 1, { play: playing }); });
  $('btnNextPara').addEventListener('click', function () { if (cur < paras.length - 1) setCur(cur + 1, { play: playing }); });
  $('btnRepeat').addEventListener('click', function () { if (cur >= 0) { audio.currentTime = 0; play(); } });

  $('content').addEventListener('click', function (e) {
    var playBtn = e.target.closest('[data-play]');
    var para = e.target.closest('.para');
    if (!para) return;
    var i = +para.dataset.idx;
    if (playBtn) {
      setCur(i, { play: true }); return;
    }
    // 单击段落正文：朗读该段；Shift+单击：从此段开始连续播放
    prefs.cont = e.shiftKey ? true : prefs.cont;
    setCur(i, { play: true });
  });

  audio.addEventListener('play', function () { playing = true; $('btnPlay').textContent = '❚❚'; barsHideSoon(1600); });
  audio.addEventListener('pause', function () { playing = false; $('btnPlay').textContent = '▶'; barsShow(); });
  audio.addEventListener('error', function () { if (cur >= 0) markNoAudio(cur); });
  audio.addEventListener('ended', function () {
    if (prefs.loop && cur >= 0) { audio.currentTime = 0; play(); return; }
    if (prefs.cont && cur < paras.length - 1) { setCur(cur + 1, { play: true }); }
    else { playing = false; $('btnPlay').textContent = '▶'; barsShow(); }
  });
  audio.addEventListener('timeupdate', function () {
    if (!audio.duration) return;
    $('seek').value = Math.round((audio.currentTime / audio.duration) * 1000);
    $('tCur').textContent = fmt(audio.currentTime);
    $('tDur').textContent = fmt(audio.duration);
  });
  $('seek').addEventListener('input', function () {
    if (audio.duration) audio.currentTime = (this.value / 1000) * audio.duration;
  });
  $('rate').addEventListener('input', function () {
    prefs.rate = +this.value; audio.playbackRate = prefs.rate; $('rateVal').textContent = prefs.rate.toFixed(2) + '×'; savePrefs();
  });
  $('btnRateReset').addEventListener('click', function () {
    prefs.rate = 1; audio.playbackRate = 1; $('rate').value = 1; $('rateVal').textContent = '1.00×'; savePrefs();
  });

  // ---------- 沉浸模式：播放时隐藏上/下栏并折叠占位（阅读区变大），点击阅读区显示 ----------
  var immerseTimer = null;
  function setBars(visible) {
    var tb = document.getElementById('toolbar'), pl = document.getElementById('player');
    if (!tb || !pl) return;
    if (visible) {
      tb.style.marginTop = '';
      pl.style.marginBottom = '';
      document.body.classList.remove('immersive');
    } else {
      // 负 margin 折掉两栏占位，#reader 随之撑满
      tb.style.marginTop = -tb.offsetHeight + 'px';
      pl.style.marginBottom = -pl.offsetHeight + 'px';
      document.body.classList.add('immersive');
    }
  }
  function barsShow() {
    if (immerseTimer) { clearTimeout(immerseTimer); immerseTimer = null; }
    setBars(true);
  }
  function barsHideSoon(ms) {
    if (immerseTimer) clearTimeout(immerseTimer);
    immerseTimer = setTimeout(function () {
      immerseTimer = null;
      if (playing) setBars(false);
    }, ms || 1600);
  }
  $('reader').addEventListener('click', function () {
    if (document.body.classList.contains('immersive')) {
      barsShow();
      if (playing) barsHideSoon(7500);   // 仍在播放则 7.5s 后再次隐藏
    }
  });

  // ---------- prev / next story ----------
  function goStory(d) {
    var ni = storyIdx + d;
    if (ni < 0 || ni >= DATA.stories.length) return;
    location.href = 'lettura.html?id=' + encodeURIComponent(DATA.stories[ni].id);
  }
  $('btnPrev').addEventListener('click', function () { goStory(-1); });
  $('btnNext').addEventListener('click', function () { goStory(1); });

  // ---------- misc UI ----------
  $('btnMenu').addEventListener('click', function () {
    $('sidebar').classList.toggle('hidden'); $('overlay').classList.toggle('on');
  });
  $('overlay').addEventListener('click', function () {
    $('sidebar').classList.add('hidden'); $('overlay').classList.remove('on');
  });
  document.addEventListener('keydown', function (e) {
    if (e.target.tagName === 'INPUT') return;
    if (e.code === 'Space') { e.preventDefault(); toggle(); }
    else if (e.code === 'ArrowLeft') { if (cur > 0) setCur(cur - 1, { play: playing }); }
    else if (e.code === 'ArrowRight') { if (cur < paras.length - 1) setCur(cur + 1, { play: playing }); }
    else if (e.key === 'r' || e.key === 'R') { if (cur >= 0) { audio.currentTime = 0; play(); } }
  });

  // ---------- init ----------
  // 手机/窄屏：侧边栏默认收起，点 ☰ 展开
  if (window.matchMedia && window.matchMedia('(max-width:900px)').matches) {
    $('sidebar').classList.add('hidden');
  }
  renderSidebar();

  function boot() {
    story = store()[sid];
    paras = story.paras;
    renderContent();
    applyMode();
    applyFont();
    audio.playbackRate = prefs.rate;
    // 空闲时预取上/下一篇，切换几乎零等待
    setTimeout(function () {
      [storyIdx - 1, storyIdx + 1].forEach(function (j) {
        var n = DATA.stories[j];
        if (n && !store()[n.id]) loadScript('data/st/' + n.id + '.js');
      });
    }, 1200);
  }

  if (store()[sid]) {
    boot();
  } else {
    loadScript('data/st/' + sid + '.js', function (err) {
      if (err) {
        $('content').innerHTML = '<p style="color:#8a1f2b;padding:30px 0">加载失败，请刷新重试。</p>';
        return;
      }
      boot();
    });
  }
})();
