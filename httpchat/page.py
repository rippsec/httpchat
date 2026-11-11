PAGE = r"""<!doctype html>
<html lang="es"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>HTTP Chat</title>
<style>
:root{--bg:#f4f4f6;--card:#fff;--fg:#1b1b1f;--mut:#6b6b76;--me:#2f6fed;--line:#e2e2e8;--live:#e8a33d}
@media (prefers-color-scheme:dark){:root{--bg:#141418;--card:#1e1e24;--fg:#ececf1;--mut:#9a9aa6;--me:#4c86ff;--line:#2c2c35;--live:#f0b453}}
*{box-sizing:border-box}html,body{height:100%;margin:0}
body{background:var(--bg);color:var(--fg);font:15px/1.4 system-ui,sans-serif;display:flex;flex-direction:column}
header{padding:10px 16px;border-bottom:1px solid var(--line);display:flex;gap:8px;align-items:center;background:var(--card);flex-wrap:wrap}
header b{flex:1}
input,button{font:inherit;padding:8px 10px;border-radius:8px;border:1px solid var(--line);background:var(--bg);color:var(--fg);min-width:0}
button{background:var(--me);color:#fff;border:none;cursor:pointer}
#log{flex:1;overflow-y:auto;padding:16px;display:flex;flex-direction:column;gap:8px}
.m{max-width:75%;padding:8px 12px;border-radius:12px;background:var(--card);border:1px solid var(--line);white-space:pre-wrap;overflow-wrap:anywhere}
.m.me{align-self:flex-end;background:var(--me);color:#fff;border:none}
.m.draft{border:1.5px dashed var(--live);background:transparent}
.m.draft .meta{color:var(--live);opacity:1}
.m.draft .txt::after{content:'▍';color:var(--live);animation:blink 1s steps(1) infinite}
@keyframes blink{50%{opacity:0}}
.meta{font-size:12px;opacity:.7;margin-bottom:2px}
#live{display:contents}
.m.draft.mine{align-self:flex-end;border-color:var(--me)}
.m.draft.mine .meta{color:var(--me)}
.m.draft.mine .txt::after{color:var(--me)}
main{flex:1;display:flex;min-height:0}
aside{width:230px;border-left:1px solid var(--line);background:var(--card);overflow-y:auto;padding:12px}
aside h3{margin:0 0 8px;font-size:13px;font-weight:600;color:var(--mut);text-transform:uppercase;letter-spacing:.04em}
aside ul{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:6px}
aside li{display:flex;gap:8px;align-items:flex-start;padding:6px 8px;border-radius:8px}
aside li.me{background:var(--bg)}
aside .dot{width:8px;height:8px;border-radius:50%;background:#2fb36b;margin-top:6px;flex:none}
aside .who{min-width:0;overflow-wrap:anywhere}
aside .sub{font-size:12px;color:var(--mut)}
aside .typing{font-size:12px;color:var(--live)}
@media (max-width:640px){main{flex-direction:column-reverse}aside{width:auto;border-left:none;border-bottom:1px solid var(--line);max-height:30vh}}
form{display:flex;gap:8px;padding:12px 16px;border-top:1px solid var(--line);background:var(--card)}
form input{flex:1}
#st{font-size:12px;color:var(--mut)}
</style></head><body>
<header><b>💬 HTTP Chat</b><span id="st">conectando…</span><input id="name" placeholder="Tu nombre" size="20" title="Vacío = tu IP"></header>
<main><div id="log"><div id="live"></div></div><aside><h3>Conectados (<span id="cnt">0</span>)</h3><ul id="hosts"></ul></aside></main>
<form id="f"><input id="t" placeholder="Escribe… los demás lo ven en vivo. Enter para enviar" autocomplete="off" autofocus><button>Enviar</button></form>
<script>
const $=id=>document.getElementById(id), log=$('log'), live=$('live');
const cid=Math.random().toString(36).slice(2)+Date.now().toString(36);
let last=0, ver=-1, seq=0, myIp='';
try{$('name').value=localStorage.getItem('hc-name')||''}catch(e){}
$('name').onchange=()=>{try{localStorage.setItem('hc-name',$('name').value.trim())}catch(e){} renderMine(); pushDraft();};
const myName=()=>$('name').value.trim()||myIp;
fetch('/whoami').then(r=>r.json()).then(j=>{myIp=j.ip; $('name').placeholder=j.ip+' (tu IP)';}).catch(()=>{});

const nearBottom=()=>log.scrollHeight-log.scrollTop-log.clientHeight<80;
function bubble(m,cls){
  const d=document.createElement('div'); d.className='m '+cls;
  const meta=document.createElement('div'); meta.className='meta';
  const txt=document.createElement('div'); txt.className='txt';
  d.append(meta,txt); return d;
}
function addMsg(m){
  const me=m.cid===cid, d=bubble(m,me?'me':'');
  d.children[0].textContent=(m.name===m.ip?m.name:m.name+' · '+m.ip)+' · '+new Date(m.ts*1000).toLocaleTimeString();
  d.children[1].textContent=m.text;
  const stick=nearBottom()||me;
  log.insertBefore(d,live); if(stick) log.scrollTop=log.scrollHeight;
}
const mine=bubble({},'draft mine');
function renderMine(){
  const text=$('t').value;
  if(!text){mine.remove();return}
  const stick=nearBottom();
  mine.children[0].textContent='✎ Tú ('+myName()+') estás escribiendo…';
  mine.children[1].textContent=text;
  live.append(mine);  // siempre al final
  if(stick) log.scrollTop=log.scrollHeight;
}
const draftEls={};
function renderDrafts(list){
  const stick=nearBottom(), seen={};
  for(const dr of list){
    if(dr.cid===cid) continue;
    seen[dr.cid]=1;
    let el=draftEls[dr.cid];
    if(!el){el=draftEls[dr.cid]=bubble(dr,'draft'); live.append(el);}
    el.children[0].textContent='✎ '+dr.name+' está escribiendo…';
    el.children[1].textContent=dr.text;
  }
  for(const k in draftEls) if(!seen[k]){draftEls[k].remove(); delete draftEls[k];}
  if(mine.isConnected) live.append(mine);
  if(stick) log.scrollTop=log.scrollHeight;
}
function renderHosts(list,drafts){
  const typing=new Set(drafts.map(d=>d.cid)), ul=$('hosts');
  if($('t').value) typing.add(cid);
  ul.textContent=''; $('cnt').textContent=list.length;
  list.sort((a,b)=>(b.cid===cid)-(a.cid===cid));
  for(const c of list){
    const li=document.createElement('li'), me=c.cid===cid;
    if(me) li.className='me';
    const dot=document.createElement('span'); dot.className='dot';
    const who=document.createElement('div'); who.className='who';
    const n=document.createElement('div'); n.textContent=c.name+(me?' (tú)':'');
    who.append(n);
    if(c.name!==c.ip){const s=document.createElement('div'); s.className='sub'; s.textContent=c.ip; who.append(s);}
    if(typing.has(c.cid)){const t=document.createElement('div'); t.className='typing'; t.textContent='✎ escribiendo…'; who.append(t);}
    li.append(dot,who); ul.append(li);
  }
}
let lastClients=[], lastDrafts=[];
async function poll(){
  for(;;){
    try{
      const r=await fetch('/poll?since='+last+'&v='+ver+'&cid='+cid+'&name='+encodeURIComponent($('name').value.trim()));
      const j=await r.json(); $('st').textContent='conectado';
      for(const m of j.messages) if(m.id>last){addMsg(m); last=m.id;}
      renderDrafts(j.drafts); lastClients=j.clients; lastDrafts=j.drafts;
      renderHosts(lastClients,lastDrafts); ver=j.v;
    }catch(e){ $('st').textContent='sin conexión, reintentando…'; await new Promise(r=>setTimeout(r,2000)); }
  }
}
// Envío del borrador en vivo: una petición a la vez, siempre con el texto más reciente.
let busy=false, dirty=false;
async function pushDraft(){
  if(busy){dirty=true;return}
  busy=true;
  do{ dirty=false;
    await fetch('/typing',{method:'POST',body:JSON.stringify({cid,seq:++seq,name:myName(),text:$('t').value})}).catch(()=>{});
  }while(dirty);
  busy=false;
}
$('t').addEventListener('input',()=>{renderMine(); renderHosts(lastClients,lastDrafts); pushDraft();});
$('f').onsubmit=e=>{
  e.preventDefault(); const text=$('t').value.trim(); if(!text) return;
  $('t').value=''; renderMine();
  fetch('/send',{method:'POST',body:JSON.stringify({cid,seq:++seq,name:myName(),text})});
};
addEventListener('pagehide',()=>{ navigator.sendBeacon('/leave',JSON.stringify({cid})); });
poll();
</script></body></html>
"""
