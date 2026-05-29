import re, os

DOCS = '/Users/reneh/Development/python/essence-way-of-working/docs'

NEW_NAV_CSS = r"""
  /* ===== SITE NAV ===== */
  .skip-link{position:absolute;top:-100%;left:0;z-index:999;padding:10px 18px;background:#1c1a16;color:#f3efe6;font-family:"IBM Plex Mono",monospace;font-size:13px;font-weight:600;text-decoration:none;border-radius:0 0 8px 0;outline:none}
  .skip-link:focus-visible{top:0;outline:3px solid #f3efe6;outline-offset:2px}
  .site-nav{position:sticky;top:0;z-index:100;background:var(--paper,#f3efe6);border-bottom:1px solid var(--line,#d8d0bf);-webkit-backdrop-filter:blur(6px);backdrop-filter:blur(6px)}
  .site-nav-inner{max-width:1300px;margin:0 auto;padding:0 26px;display:flex;align-items:center;height:52px;gap:0}
  .site-nav-logo{font-family:"Fraunces",serif;font-weight:700;font-size:1rem;color:var(--ink,#1c1a16);text-decoration:none;white-space:nowrap;margin-right:auto;letter-spacing:-.01em;flex-shrink:0}
  .site-nav-logo em{font-style:italic;font-weight:500;color:#243b66}
  .site-nav-list{display:flex;list-style:none;margin:0;padding:0;gap:2px;align-items:center}
  .site-nav-list > li > a,.site-nav-list > li > button{font-family:"IBM Plex Mono",monospace;font-size:11px;letter-spacing:.08em;text-transform:uppercase;font-weight:600;color:var(--ink-soft,#524d42);text-decoration:none;padding:7px 10px;border-radius:6px;border:none;background:transparent;cursor:pointer;transition:.12s;line-height:1;display:flex;align-items:center;gap:4px;min-height:25px;white-space:nowrap}
  .site-nav-list > li > a:hover,.site-nav-list > li > button:hover{color:var(--ink,#1c1a16);background:var(--paper-2,#ece6d8)}
  .site-nav-list > li.active > a,.site-nav-list > li.active > button{color:var(--ink,#1c1a16);background:var(--paper-2,#ece6d8)}
  .has-drop{position:relative}
  .has-drop .drop{display:none;position:absolute;top:calc(100% + 4px);right:0;min-width:240px;background:var(--card,#fbf9f3);border:1px solid var(--line,#d8d0bf);border-radius:10px;box-shadow:0 1px 0 rgba(0,0,0,.04),0 14px 30px -22px rgba(28,26,22,.55);padding:5px;list-style:none;margin:0;z-index:200}
  .has-drop.open .drop{display:block}
  .drop li a{display:flex;align-items:center;font-family:"IBM Plex Mono",monospace;font-size:11px;letter-spacing:.04em;color:var(--ink-soft,#524d42);text-decoration:none;padding:8px 10px;border-radius:6px;transition:.1s;min-height:25px}
  .drop li a:hover,.drop li a:focus{background:var(--paper-2,#ece6d8);color:var(--ink,#1c1a16)}
  .drop li.active a{color:var(--ink,#1c1a16);font-weight:600}
  .drop-label{font-family:"IBM Plex Mono",monospace;font-size:9px;letter-spacing:.2em;text-transform:uppercase;color:#5a5040;padding:6px 10px 2px;display:block}
  /* search */
  .site-search{position:relative;margin-left:8px}
  .search-form{display:flex;align-items:center;position:relative}
  .search-input{font-family:"IBM Plex Mono",monospace;font-size:11px;letter-spacing:.02em;border:1px solid var(--line,#d8d0bf);background:var(--card,#fbf9f3);border-radius:20px;padding:6px 14px 6px 32px;width:160px;color:var(--ink,#1c1a16);transition:width .2s,border-color .2s;outline:none;min-height:25px}
  .search-input::placeholder{color:var(--ink-soft,#524d42);opacity:.8}
  .search-input:focus{width:220px;border-color:var(--ink,#1c1a16)}
  .search-icon{position:absolute;left:10px;top:50%;transform:translateY(-50%);pointer-events:none;color:var(--ink-soft,#524d42);line-height:1}
  .search-results{display:none;position:absolute;top:calc(100% + 6px);right:0;width:340px;background:var(--card,#fbf9f3);border:1px solid var(--line,#d8d0bf);border-radius:12px;box-shadow:0 1px 0 rgba(0,0,0,.04),0 18px 38px -24px rgba(28,26,22,.6);list-style:none;margin:0;padding:6px;max-height:420px;overflow-y:auto;z-index:201}
  .search-results.visible{display:block}
  .search-result{border-radius:8px}
  .search-result a{display:flex;align-items:flex-start;gap:10px;padding:9px 10px;text-decoration:none;color:inherit;border-radius:8px;transition:.1s;border-left:3px solid transparent}
  .search-result a:hover,.search-result a:focus,.search-result.sel a{background:var(--paper-2,#ece6d8)}
  .search-result.sel a{border-left-color:var(--rc,#243b66)}
  .search-result .r-tag{font-family:"IBM Plex Mono",monospace;font-size:9px;letter-spacing:.12em;text-transform:uppercase;font-weight:600;color:var(--rc,#243b66);margin-bottom:2px;white-space:nowrap}
  .search-result .r-title{font-family:"Fraunces",serif;font-weight:600;font-size:1rem;line-height:1.1;color:var(--ink,#1c1a16)}
  .search-result .r-snippet{font-size:.8rem;color:var(--ink-soft,#524d42);margin-top:2px;line-height:1.35}
  .search-result .r-snippet em{font-style:normal;font-weight:600;color:var(--ink,#1c1a16)}
  .search-no-results{padding:10px 12px;font-family:"IBM Plex Mono",monospace;font-size:11px;color:var(--ink-soft,#524d42);text-align:center}
  .search-see-all{border-top:1px dashed var(--line,#d8d0bf);margin-top:4px;padding-top:4px}
  .search-see-all a{display:flex;justify-content:center;font-family:"IBM Plex Mono",monospace;font-size:10px;letter-spacing:.1em;text-transform:uppercase;font-weight:600;color:var(--prac,#243b66);text-decoration:none;padding:8px 10px;border-radius:6px;transition:.1s;min-height:25px;align-items:center}
  .search-see-all a:hover,.search-see-all a:focus{background:var(--paper-2,#ece6d8)}
  .toolbar{top:52px !important}
  section{scroll-margin-top:132px !important}
  /* WCAG 2.4.11 focus appearance */
  :focus-visible{outline:3px solid #243b66;outline-offset:2px}
  a:focus-visible,button:focus-visible{outline:3px solid #243b66;outline-offset:3px;border-radius:4px}
  a.deck:focus-visible,a.page-link:focus-visible{outline:3px solid #243b66;outline-offset:4px;border-radius:14px}
  a.dl:focus-visible{outline:3px solid #243b66;outline-offset:4px;border-radius:30px}
  a.f:focus-visible,button.f:focus-visible{outline:3px solid #243b66;outline-offset:3px}
  .site-nav-list a:focus-visible,.site-nav-list button:focus-visible,.site-nav-logo:focus-visible{outline:3px solid #243b66;outline-offset:2px;border-radius:4px}
  .drop a:focus-visible{outline:3px solid #243b66;outline-offset:2px}
  .search-input:focus-visible{outline:3px solid #243b66;outline-offset:2px;border-radius:20px}
  /* WCAG 1.4.3 contrast corrections */
  :root{--cust:#1a7040;--product:#7a4900;--sol:#6b4c00;--bs:#0a5a72}
  @media(max-width:700px){
    .site-nav-logo em{display:none}
    .site-nav-list > li > a,.site-nav-list > li > button{font-size:10px;padding:6px 7px;letter-spacing:.04em}
    .search-input{width:110px}.search-input:focus{width:160px}
    .search-results{right:-60px;width:280px}
  }
  @media print{.site-nav,.skip-link{display:none}}
"""

NEW_NAV_HTML = """<a class="skip-link" href="#main-content">Skip to main content</a>
<header class="site-nav" role="banner">
  <div class="site-nav-inner">
    <a class="site-nav-logo" href="index.html">Essence <em>Way of Working</em></a>
    <nav aria-label="Site navigation">
      <ul class="site-nav-list">
        <li><a href="index.html">Home</a></li>
        <li class="has-drop">
          <button aria-haspopup="true" aria-expanded="false" aria-controls="practices-menu">Practices <span aria-hidden="true">&#9662;</span></button>
          <ul class="drop" id="practices-menu">
            <span class="drop-label" aria-hidden="true">Four practices</span>
            <li><a href="business-scenarios-essence-practice.html">Business Scenarios</a></li>
            <li><a href="service-blueprint-essence-practice.html">Service Blueprint</a></li>
            <li><a href="mva-essence-practice.html">Min. Viable Architecture</a></li>
            <li><a href="mvg-essence-practice.html">Min. Viable Governance</a></li>
          </ul>
        </li>
        <li><a href="resources.html">Resources</a></li>
      </ul>
    </nav>
    <div class="site-search" role="search">
      <form class="search-form" action="search.html" method="get" aria-label="Site search">
        <span class="search-icon" aria-hidden="true">
          <svg width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="6.5" cy="6.5" r="4.5"/><line x1="10.5" y1="10.5" x2="14" y2="14"/></svg>
        </span>
        <input
          id="site-search-input"
          class="search-input"
          type="search"
          name="q"
          placeholder="Search..."
          aria-label="Search this site"
          aria-autocomplete="list"
          aria-expanded="false"
          aria-controls="search-results-list"
          aria-activedescendant=""
          autocomplete="off"
          spellcheck="false"
        >
      </form>
      <ul id="search-results-list" class="search-results" role="listbox" aria-label="Search results"></ul>
    </div>
  </div>
</header>
"""

NEW_NAV_JS = r"""<script>
(function(){
  /* Active nav state */
  var p = location.pathname.split('/').pop() || 'index.html';
  document.querySelectorAll('.site-nav-list > li > a').forEach(function(a){
    if(a.getAttribute('href') === p) a.closest('li').classList.add('active');
  });
  var practicePages = ['business-scenarios-essence-practice.html','service-blueprint-essence-practice.html','mva-essence-practice.html','mvg-essence-practice.html'];
  if(practicePages.indexOf(p) !== -1) document.querySelectorAll('.has-drop').forEach(function(el){ el.classList.add('active'); });
  document.querySelectorAll('.drop li a').forEach(function(a){
    if(a.getAttribute('href') === p) a.closest('li').classList.add('active');
  });

  /* Disclosure nav keyboard (WCAG 2.1.1) */
  document.querySelectorAll('.has-drop').forEach(function(dropdown){
    var btn = dropdown.querySelector('button');
    var items = Array.from(dropdown.querySelectorAll('.drop li a'));
    function open(){ dropdown.classList.add('open'); btn.setAttribute('aria-expanded','true'); }
    function close(ret){ dropdown.classList.remove('open'); btn.setAttribute('aria-expanded','false'); if(ret) btn.focus(); }
    btn.addEventListener('click',function(e){ e.stopPropagation(); dropdown.classList.contains('open') ? close(false) : open(); });
    btn.addEventListener('keydown',function(e){
      if(e.key==='ArrowDown'){ e.preventDefault(); open(); if(items[0]) items[0].focus(); }
      else if(e.key==='ArrowUp'){ e.preventDefault(); open(); if(items.length) items[items.length-1].focus(); }
      else if(e.key==='Escape'){ close(true); }
    });
    items.forEach(function(item,i){
      item.addEventListener('keydown',function(e){
        if(e.key==='ArrowDown'){ e.preventDefault(); if(items[i+1]) items[i+1].focus(); }
        else if(e.key==='ArrowUp'){ e.preventDefault(); if(i>0) items[i-1].focus(); else close(true); }
        else if(e.key==='Escape'){ close(true); }
        else if(e.key==='Tab'){ close(false); }
      });
    });
  });
  document.addEventListener('click',function(){
    document.querySelectorAll('.has-drop.open').forEach(function(el){
      el.classList.remove('open'); el.querySelector('button').setAttribute('aria-expanded','false');
    });
  });

  /* Decorative aria-hidden */
  document.querySelectorAll('.track .ar').forEach(function(el){ el.setAttribute('aria-hidden','true'); });

  /* Site search */
  var searchInput   = document.getElementById('site-search-input');
  var searchResults = document.getElementById('search-results-list');
  var searchIndex   = null;
  var selIdx        = -1;
  var resultLinks   = [];

  function loadIndex(cb){
    if(searchIndex){ cb(); return; }
    fetch('search-index.json')
      .then(function(r){ return r.json(); })
      .then(function(d){ searchIndex = d; cb(); })
      .catch(function(){ searchIndex = []; });
  }

  function esc(s){ return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }

  function hilite(text, q){
    if(!q) return esc(text);
    var safe = q.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
    return esc(text).replace(new RegExp('('+safe+')','gi'),'<em>$1</em>');
  }

  function scoreEntry(entry, q){
    var ql = q.toLowerCase(), s = 0;
    if(entry.title.toLowerCase().indexOf(ql)  !== -1) s += 20;
    if(entry.kicker.toLowerCase().indexOf(ql) !== -1) s += 8;
    if(entry.lede.toLowerCase().indexOf(ql)   !== -1) s += 5;
    if(entry.text.toLowerCase().indexOf(ql)   !== -1) s += 2;
    entry.sections.forEach(function(sec){ if(sec.h.toLowerCase().indexOf(ql) !== -1) s += 6; });
    return s;
  }

  function bestSection(entry, q){
    var ql = q.toLowerCase(), best = null;
    entry.sections.forEach(function(sec){ if(!best && sec.h.toLowerCase().indexOf(ql) !== -1) best = sec.h; });
    return best;
  }

  function renderResults(q){
    if(!q || q.length < 2){ hideResults(); return; }
    var scored = searchIndex
      .map(function(e){ return {e:e, s:scoreEntry(e,q)}; })
      .filter(function(x){ return x.s > 0; })
      .sort(function(a,b){ return b.s - a.s; })
      .slice(0,7);

    if(scored.length === 0){
      searchResults.innerHTML = '<li class="search-no-results">No results for &ldquo;' + esc(q) + '&rdquo;</li>';
      showResults(); resultLinks = []; selIdx = -1; return;
    }

    var seeAllHtml = '<li class="search-see-all" role="none"><a href="search.html?q='+encodeURIComponent(q)+'">See all results for “'+esc(q)+'” &rarr;</a></li>';
    searchResults.innerHTML = scored.map(function(x, i){
      var e = x.e, sec = bestSection(e,q);
      var snip = sec ? hilite(sec,q) : hilite(e.lede.slice(0,90),q);
      return '<li class="search-result" role="option" id="sr-'+i+'" aria-selected="false">' +
        '<a href="'+esc(e.url)+'" tabindex="-1" style="--rc:'+esc(e.color)+'">' +
          '<div><div class="r-tag">'+esc(e.tag)+'</div>' +
          '<div class="r-title">'+hilite(e.title,q)+'</div>' +
          (snip ? '<div class="r-snippet">'+snip+'</div>' : '') +
        '</div></a></li>';
    }).join('') + seeAllHtml;

    resultLinks = Array.from(searchResults.querySelectorAll('.search-result a'));
    selIdx = -1;
    showResults();
  }

  function showResults(){ searchResults.classList.add('visible'); searchInput.setAttribute('aria-expanded','true'); }
  function hideResults(){
    searchResults.classList.remove('visible');
    searchInput.setAttribute('aria-expanded','false');
    searchInput.setAttribute('aria-activedescendant','');
    resultLinks.forEach(function(a){
      a.closest('.search-result').classList.remove('sel');
      a.closest('.search-result').setAttribute('aria-selected','false');
    });
    selIdx = -1;
  }

  function selectResult(i){
    resultLinks.forEach(function(a, j){
      var li = a.closest('.search-result');
      var sel = (j === i);
      li.classList.toggle('sel', sel);
      li.setAttribute('aria-selected', String(sel));
    });
    if(i >= 0 && resultLinks[i]){
      var li = resultLinks[i].closest('.search-result');
      searchInput.setAttribute('aria-activedescendant', li.id);
      li.scrollIntoView({block:'nearest'});
    } else {
      searchInput.setAttribute('aria-activedescendant','');
    }
    selIdx = i;
  }

  var debounceTimer;
  searchInput.addEventListener('input', function(){
    clearTimeout(debounceTimer);
    var q = searchInput.value.trim();
    debounceTimer = setTimeout(function(){ loadIndex(function(){ renderResults(q); }); }, 120);
  });

  searchInput.addEventListener('keydown', function(e){
    if(!searchResults.classList.contains('visible')) return;
    if(e.key==='ArrowDown'){
      e.preventDefault(); selectResult(Math.min(selIdx+1, resultLinks.length-1));
    } else if(e.key==='ArrowUp'){
      e.preventDefault(); selectResult(Math.max(selIdx-1, -1));
    } else if(e.key==='Enter'){
      e.preventDefault();
      if(selIdx >= 0 && resultLinks[selIdx]){
        window.location.href = resultLinks[selIdx].getAttribute('href');
      } else {
        var qv = searchInput.value.trim();
        if(qv) window.location.href = 'search.html?q=' + encodeURIComponent(qv);
      }
    } else if(e.key==='Escape'){
      hideResults(); searchInput.blur();
    }
  });

  searchInput.addEventListener('focus', function(){
    var q = searchInput.value.trim();
    if(q.length >= 2) loadIndex(function(){ renderResults(q); });
  });

  document.addEventListener('click', function(e){
    if(!e.target.closest('.site-search')) hideResults();
  });
})();
</script>"""

files = sorted(f for f in os.listdir(DOCS) if f.endswith('.html'))

for filename in files:
    path = os.path.join(DOCS, filename)
    content = open(path).read()

    content, n1 = re.subn(
        r'/\* ===== SITE NAV ===== \*/.*?</style>',
        NEW_NAV_CSS + '\n</style>', content, count=1, flags=re.S)

    content, n2 = re.subn(
        r'(?:<a class="skip-link"[^>]*>[^<]*</a>\n)?<header class="site-nav"[\s\S]*?</header>\n',
        NEW_NAV_HTML, content, count=1, flags=re.S)

    content, n3 = re.subn(
        r'<script>\s*\(function\(\)\{[\s\S]*?practicePages[\s\S]*?\}\)\(\);\s*</script>',
        NEW_NAV_JS, content, count=1, flags=re.S)

    # Fresh injection for files that have no existing nav markers
    if n1 == 0 and '</style>' in content:
        content = content.replace('</style>', NEW_NAV_CSS + '\n</style>', 1)
        n1 = 1
    if n2 == 0 and '<body>' in content:
        content = content.replace('<body>', '<body>\n' + NEW_NAV_HTML, 1)
        n2 = 1
    if n3 == 0 and '</body>' in content:
        content = content.replace('</body>', NEW_NAV_JS + '\n</body>', 1)
        n3 = 1

    open(path, 'w').write(content)
    ok = 'v' if n1+n2+n3 == 3 else '!'
    print(f'{ok} {filename:<52} css={n1} html={n2} js={n3}')

print(f'\nDone — {len(files)} files.')
