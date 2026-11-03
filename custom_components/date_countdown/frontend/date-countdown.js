/* Date Countdown — local, dependency-free Home Assistant panel and card. */
const esc = (value = "") => String(value).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const unitLabels = {days:"天", months:"個月", years:"年"};
const statusLabels = {healthy:"使用中", soon:"即將到期", due:"今天到期", overdue:"已逾期"};
const daysLabel = n => n < 0 ? `已逾期 ${Math.abs(n)} 天` : n === 0 ? "今天到期" : `剩餘 ${n} 天`;
const lifeLabel = item => item.mode === "fixed" ? "固定到期日" : `${item.duration} ${unitLabels[item.unit] || item.unit}`;
const progress = item => `<div class="track" role="progressbar" aria-label="剩餘進度" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${Number(item.remaining_percentage) || 0}"><span style="width:${Math.max(0, Math.min(100, Number(item.remaining_percentage) || 0))}%"></span></div>`;
const icon = (fixed = false) => fixed
  ? '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><rect x="4" y="5" width="16" height="16" rx="3"/><path d="M8 3v4m8-4v4M4 10h16m-11 5 2 2 4-4"/></svg>'
  : '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="M8 3h8l3 5v9l-3 4H8l-3-4V8zM5 9h14M5 16h14M9 6h6M9 12h6"/></svg>';
const emit = (node, type, detail) => node.dispatchEvent(new CustomEvent(type, {detail, bubbles:true, composed:true}));
const styles = `
:host{--dc-accent:#327764;--dc-wash:#edf5f1;--dc-border:var(--divider-color,#e2e7e3);--dc-text:var(--primary-text-color,#24362e);--dc-muted:var(--secondary-text-color,#738078);display:block;color:var(--dc-text);font-family:var(--paper-font-body1_-_font-family,system-ui,-apple-system,"Noto Sans TC",sans-serif)}
*{box-sizing:border-box}button,input,select,textarea{font:inherit}button,a,input,select,textarea{outline-offset:4px}
button{cursor:pointer;min-height:40px;border:1px solid var(--dc-border);background:var(--card-background-color,#fff);color:var(--dc-text);border-radius:10px;padding:8px 14px;font-size:14px;font-weight:550}
button:hover{border-color:var(--dc-accent);background:var(--dc-wash);color:#245b4b}button:disabled{opacity:.5;cursor:wait}
.primary{background:var(--dc-accent);color:white;border-color:var(--dc-accent)}.primary:hover{background:#245b4b;color:white}
.quiet{border-color:transparent;background:transparent}.danger{color:#b5473a}.small{font-size:12px;padding:5px 10px;min-height:34px}
input,select,textarea{background:var(--card-background-color,#fff);color:var(--dc-text);border:1px solid var(--dc-border);padding:11px 12px;border-radius:9px;min-height:44px;width:100%}
input:focus,textarea:focus,select:focus{outline:2px solid var(--dc-accent)}textarea{resize:vertical;min-height:85px}
svg{width:26px;height:26px;flex-shrink:0}.muted{color:var(--dc-muted)}.eyebrow{color:var(--dc-accent);letter-spacing:2.5px;font-size:11px;font-weight:700}
h1,h2,h3,p{margin:0}h1{font-size:34px;font-weight:650;letter-spacing:-1px;line-height:1.4}h2{font-size:21px}h3{font-size:18px;font-weight:600}
.header{height:64px;display:flex;align-items:center;gap:16px;padding:0 24px;border-bottom:1px solid var(--dc-border);background:var(--card-background-color,#fff);font-size:15px}
.page{min-height:calc(100vh - 64px);background:var(--primary-background-color,#f6f8f5);padding:38px clamp(16px,4vw,64px) 60px}
.wrap{max-width:1250px;margin:auto}.hero{display:flex;justify-content:space-between;align-items:center;gap:20px;margin-bottom:28px}.hero p{margin-top:9px;font-size:14px;color:var(--dc-muted)}
.hero .eyebrow{margin-bottom:10px}.hero button{padding:12px 20px}.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:30px}
.stat{background:var(--card-background-color,#fff);border:1px solid var(--dc-border);border-radius:14px;padding:18px 22px}.stat span{font-size:13px;color:var(--dc-muted)}.stat strong{font-size:30px;font-weight:600;display:block;margin-top:6px;line-height:1.2}
.stat.soon strong{color:#ae751a}.stat.overdue strong{color:#b5473a}.toolbar{display:flex;flex-wrap:wrap;align-items:center;gap:12px;margin-bottom:20px}
.search{max-width:300px;flex:1;min-width:180px}.toolbar select{width:auto;max-width:180px}.tabs{display:flex;gap:3px;background:var(--card-background-color,#fff);border:1px solid var(--dc-border);border-radius:10px;padding:3px}.tabs button{border:0;min-height:34px;font-size:13px}.tabs button.active{background:var(--dc-wash);color:#245b4b}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,310px),1fr));gap:18px}.item{background:var(--card-background-color,#fff);border:1px solid var(--dc-border);border-radius:16px;overflow:hidden}
.item-body{padding:22px}.item-head{display:flex;align-items:center;gap:12px;margin-bottom:22px}.item-head .names{min-width:0;flex:1}.names h3{overflow-wrap:anywhere}.names p{font-size:12px;color:var(--dc-muted);margin-top:5px}
.item-icon{display:flex;align-items:center;justify-content:center;background:var(--dc-wash);color:#327764;border-radius:12px;width:46px;height:46px;flex-shrink:0}
.badge{font-size:11px;border-radius:6px;padding:5px 8px;white-space:nowrap;background:var(--dc-wash);color:#327764}.soon .badge{color:#956415;background:#fff3d8}.overdue .badge,.due .badge{color:#ad4639;background:#fbece8}
.balance{display:flex;justify-content:space-between;align-items:baseline;gap:12px;margin-bottom:13px}.balance strong{font-size:24px;font-weight:600;letter-spacing:-.5px}.balance span{font-size:12px;color:var(--dc-muted)}
.track{height:8px;background:var(--secondary-background-color,#edf0ec);border-radius:8px;overflow:hidden}.track span{display:block;height:100%;border-radius:8px;background:var(--dc-accent);transition:width .3s}
.soon .track span{background:#d29c3f}.due .track span,.overdue .track span{background:#c66050}.dates{margin-top:16px;display:grid;gap:7px;color:var(--dc-muted);font-size:12px}.dates div{display:flex;justify-content:space-between;gap:12px}.dates b{font-weight:450;color:var(--dc-text)}
.item-footer{border-top:1px solid var(--dc-border);padding:10px 14px;display:flex;align-items:center;gap:2px;flex-wrap:wrap}.item-footer .replace{margin-left:auto}
.footnote{font-size:12px;color:var(--dc-muted);margin-top:24px;line-height:1.7}.error{background:#fbece8;color:#923b30;padding:12px 15px;border-radius:10px;margin-bottom:16px;white-space:pre-wrap;font-size:14px}.error:empty{display:none}
.empty{text-align:center;padding:55px 20px;background:var(--card-background-color,#fff);border:1px dashed var(--dc-border);border-radius:14px;color:var(--dc-muted);grid-column:1/-1}.empty h3{margin-bottom:10px;color:var(--dc-text)}
dialog{background:var(--card-background-color,#fff);color:var(--dc-text);border:1px solid var(--dc-border);border-radius:18px;width:min(560px,calc(100vw - 28px));padding:0;max-height:90vh;box-shadow:0 20px 100px #0003}
dialog::backdrop{background:#11241d66}.dialog-head{padding:22px 24px 16px;display:flex;align-items:center;justify-content:space-between;gap:12px;border-bottom:1px solid var(--dc-border)}
.dialog-body{padding:22px 24px}.dialog-body>p{font-size:14px;line-height:1.7;margin-bottom:18px;color:var(--dc-muted)}
.form-grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}.form-grid .full{grid-column:1/-1}label{display:grid;gap:7px;font-size:13px;font-weight:550}label small{font-weight:400;color:var(--dc-muted);line-height:1.6}
.actions{display:flex;justify-content:flex-end;gap:8px;flex-wrap:wrap;margin-top:22px}.actions .delete{margin-right:auto}
.history{list-style:none;margin:0 0 24px;padding:0;max-height:290px;overflow-y:auto}.history li{padding:12px 0;border-bottom:1px solid var(--dc-border)}.history .record-head{display:flex;justify-content:space-between;gap:12px;font-size:14px}.history p{font-size:13px;color:var(--dc-muted);white-space:pre-wrap;overflow-wrap:anywhere;margin:8px 0}.record-actions{display:flex;gap:6px;margin-top:8px}
.form-caption{font-size:14px;font-weight:600;margin:16px 0}.card{border-radius:var(--ha-card-border-radius,14px);border:1px solid var(--dc-border);background:var(--ha-card-background,var(--card-background-color,#fff));overflow:hidden}
.card-title{display:flex;align-items:center;justify-content:space-between;padding:20px 20px 4px;font-size:20px}.card-title a{font-size:12px;color:var(--dc-accent);text-decoration:none}
.card-row{padding:18px 20px;cursor:pointer}.card-row+.card-row{border-top:1px solid var(--dc-border)}.card-row .item-head{margin-bottom:13px}.card-row .balance{margin-bottom:10px}.card-row .balance strong{font-size:18px}.card-row .dates{margin-top:10px}.card-row .item-icon{height:38px;width:38px}.card-row h3{font-size:15px}
@media(max-width:600px){.header{padding:0 12px}.page{padding-top:24px}.hero{display:block}.hero h1{font-size:28px}.hero button{padding:10px 12px;white-space:nowrap;margin-top:16px}.hero p{max-width:none;line-height:1.8}.stats{grid-template-columns:repeat(2,1fr);gap:10px}.stat{padding:14px 18px}.toolbar .tabs{order:3;width:100%}.tabs button{flex:1}.search{max-width:none}.toolbar select{flex:1;max-width:140px}.dialog-body{padding:18px}.dialog-head{padding:16px 18px}.form-grid{gap:13px}}
`;

class DateCountdownPanel extends HTMLElement {
  constructor() {
    super(); this.attachShadow({mode:"open"});
    this.items=[]; this.filter="all"; this.query=""; this.group=""; this.sort="due";
    this._refreshing=false; this._again=false;
  }
  set hass(value) {
    const changed=this._hass?.connection !== value.connection;
    this._hass=value;
    if (this.isConnected && (!this._started || changed)) this.start();
  }
  connectedCallback() {
    if(!this._built) this.build();
    if(this._hass) this.start();
  }
  disconnectedCallback() {
    this._generation=(this._generation||0)+1;
    this._unsubscribe?.(); this._unsubscribe=null; this._started=false;
  }
  build() {
    this._built=true;
    this.shadowRoot.innerHTML=`<style>${styles}:host{height:100%;overflow:auto}</style>
      <header class="header"><button class="quiet" id="menu" aria-label="開啟側邊欄">☰</button><span>日期倒數</span></header>
      <main class="page"><div class="wrap">
      <section class="hero"><div><div class="eyebrow">DATE COUNTDOWN</div><h1>每個期限，都有安排。</h1><p>管理耗材更換與到期日，讓日常維護更從容。</p></div><button class="primary" id="add">＋ 新增項目</button></section>
      <section class="stats" aria-label="倒數概況"></section>
      <div class="toolbar"><input class="search" type="search" placeholder="搜尋名稱或分組…" aria-label="搜尋項目">
      <div class="tabs" role="group" aria-label="到期狀態"><button data-filter="all" class="active">全部</button><button data-filter="soon">即將到期</button><button data-filter="overdue">已到期</button></div>
      <select id="group" aria-label="分組"><option value="">所有分組</option></select>
      <select id="sort" aria-label="排序"><option value="due">到期日排序</option><option value="name">名稱排序</option></select></div>
      <div class="error" role="alert" id="error"></div><section class="grid" aria-live="polite"><div class="empty">載入中…</div></section>
      <p class="footnote">資料保存在你的 Home Assistant。依 HA 時區每日更新，補登歷史後會自動重新計算。<br>固定到期日的進度從建立日起算；逾期項目會保留，直到你編輯或刪除。</p>
      </div></main><dialog aria-labelledby="dialog-title"></dialog>`;
    const r=this.shadowRoot;
    r.querySelector("#menu").onclick=()=>emit(this,"hass-toggle-menu");
    r.querySelector("#add").onclick=()=>this.itemDialog();
    r.querySelector(".search").oninput=e=>{this.query=e.target.value;this.renderItems();};
    r.querySelector("#group").onchange=e=>{this.group=e.target.value;this.renderItems();};
    r.querySelector("#sort").onchange=e=>{this.sort=e.target.value;this.renderItems();};
    r.querySelectorAll("[data-filter]").forEach(button=>button.onclick=()=>{
      this.filter=button.dataset.filter;
      r.querySelectorAll("[data-filter]").forEach(b=>b.classList.toggle("active",b===button));
      this.renderItems();
    });
    r.querySelector(".grid").onclick=e=>{
      const button=e.target.closest("button[data-action]"); if(!button)return;
      const item=this.items.find(i=>i.id===button.dataset.id); if(!item)return;
      if(button.dataset.action==="edit")this.itemDialog(item);
      else this.historyDialog(item,button.dataset.action==="replace");
    };
  }
  async start() {
    this._started=true;
    const generation=this._generation=(this._generation||0)+1;
    this._unsubscribe?.(); this._unsubscribe=null;
    try {
      const unsubscribe=await this._hass.connection.subscribeMessage(()=>this.refresh(), {type:"date_countdown/subscribe"});
      if(generation!==this._generation || !this.isConnected) {unsubscribe();return;}
      this._unsubscribe=unsubscribe;
      await this.refresh();
    } catch(err) {this.showError(err);}
  }
  async api(operation, item=null, data={}) {
    return this._hass.callWS({type:"date_countdown/manage",operation,
      ...(item ? {entry_id:item.id,revision:item.revision} : {}),data});
  }
  showError(err, target=null) {
    (target||this.shadowRoot.querySelector("#error")).textContent=err?.message || String(err);
  }
  async refresh() {
    if(this._refreshing){this._again=true;return;}
    this._refreshing=true;
    try {
      const data=await this.api("list");
      this.items=data.items;this.today=data.today;
      this.shadowRoot.querySelector("#error").textContent="";
      const counts=[this.items.length,this.items.filter(i=>i.status==="healthy").length,
        this.items.filter(i=>i.status==="soon").length,this.items.filter(i=>i.days_remaining<=0).length];
      this.shadowRoot.querySelector(".stats").innerHTML=["所有項目","使用中","即將到期","已到期"].map((t,n)=>
        `<div class="stat ${n===2?"soon":n===3?"overdue":""}"><span>${t}</span><strong>${counts[n]}</strong></div>`).join("");
      const groups=[...new Set(this.items.map(i=>i.group).filter(Boolean))].sort();
      const select=this.shadowRoot.querySelector("#group");
      select.innerHTML='<option value="">所有分組</option>'+groups.map(g=>`<option value="${esc(g)}">${esc(g)}</option>`).join("");
      if(!groups.includes(this.group))this.group="";
      select.value=this.group;this.renderItems();
    }catch(err){this.showError(err);}
    finally{this._refreshing=false;if(this._again){this._again=false;this.refresh();}}
  }
  renderItems() {
    const q=this.query.toLocaleLowerCase();
    const items=this.items.filter(i=>(!q||`${i.name} ${i.group}`.toLocaleLowerCase().includes(q))&&
      (!this.group||i.group===this.group)&&(this.filter==="all"||(this.filter==="soon"?i.status==="soon":i.days_remaining<=0)))
      .sort((a,b)=>this.sort==="name"?a.name.localeCompare(b.name):a.due_date.localeCompare(b.due_date)||a.name.localeCompare(b.name));
    this.shadowRoot.querySelector(".grid").innerHTML=items.map(i=>`
      <article class="item ${i.status}">
        <div class="item-body"><div class="item-head"><div class="item-icon">${icon(i.mode==="fixed")}</div>
        <div class="names"><h3>${esc(i.name)}</h3><p>${esc(i.group||"未分組")} · ${esc(lifeLabel(i))}</p></div><span class="badge">${statusLabels[i.status]}</span></div>
        <div class="balance"><strong>${daysLabel(i.days_remaining)}</strong><span>${i.remaining_percentage}% 剩餘</span></div>${progress(i)}
        <div class="dates">${i.mode==="lifetime"?`<div><span>上次更換</span><b>${esc(i.start_date)}</b></div>`:""}
        <div><span>到期日期</span><b>${esc(i.due_date)}</b></div></div></div>
        <div class="item-footer"><button class="quiet small" data-action="history" data-id="${esc(i.id)}">歷史 ${i.history_count}</button>
        <button class="quiet small" data-action="edit" data-id="${esc(i.id)}">編輯</button>
        ${i.mode==="lifetime"?`<button class="small replace" data-action="replace" data-id="${esc(i.id)}">記錄更換 ↗</button>`:""}</div>
      </article>`).join("")||`<div class="empty"><h3>${this.items.length?"沒有符合的項目":"從第一個項目開始"}</h3><p>${this.items.length?"試試其他搜尋或篩選條件。":"新增濾心、耗材、食品或保固，集中掌握每個期限。"}</p></div>`;
  }
  openDialog(title,body) {
    const dialog=this.shadowRoot.querySelector("dialog");
    if(dialog.open)dialog.close();
    dialog.innerHTML=`<div class="dialog-head"><h2 id="dialog-title">${esc(title)}</h2><button class="quiet" id="close" aria-label="關閉">✕</button></div><div class="dialog-body">${body}</div>`;
    dialog.querySelector("#close").onclick=()=>dialog.close();
    dialog.showModal();return dialog;
  }
  async submit(form, task) {
    const error=form.querySelector(".error");error.textContent="";
    const buttons=form.querySelectorAll("button");buttons.forEach(b=>b.disabled=true);
    try{await task();await this.refresh();}
    catch(err){this.showError(err,error);}
    finally{buttons.forEach(b=>b.disabled=false);}
  }
  itemDialog(item=null) {
    const mode=item?.mode||"lifetime";
    const d=this.openDialog(item?"編輯項目":"新增倒數項目",`
      <form><div class="error" role="alert"></div><div class="form-grid">
      <label class="full">倒數類型<select name="mode" ${item?"disabled":""}><option value="lifetime">耗材壽命 · 更換日期＋使用期限</option><option value="fixed">固定到期日 · 食品、保固等</option></select></label>
      <label class="full">名稱<input name="name" required maxlength="100" placeholder="例如：後置濾心" value="${esc(item?.name||"")}"></label>
      <label class="full">分組<input name="group" maxlength="100" placeholder="例如：淨水器（選填）" value="${esc(item?.group||"")}"></label>
      <div class="full type-fields"></div>
      <label class="full">提前提醒天數<input type="number" name="reminder_days" min="0" max="36500" step="1" required value="${item?.reminder_days??14}"><small>用於狀態與進度條變色；推播通知可另用 HA 自動化設定。</small></label>
      </div><div class="actions">${item?'<button type="button" class="danger delete">刪除項目</button>':""}<button type="button" class="cancel">取消</button><button class="primary" type="submit">${item?"儲存變更":"建立項目"}</button></div></form>`);
    const form=d.querySelector("form");
    const typeFields=()=>{
      const fixed=form.elements.mode.value==="fixed";
      form.querySelector(".type-fields").innerHTML=fixed
        ?`<label>到期日期<input type="date" name="due_date" required value="${esc(item?.due_date||this.today)}"></label>`
        :`<div class="form-grid"><label class="full">上次更換日期<input type="date" name="start_date" required max="${this.today}" value="${esc(item?.start_date||this.today)}"><small>編輯此日期會修正最新一筆更換紀錄；新增更換請使用「記錄更換」。</small></label><label>使用期限<input type="number" name="duration" min="1" max="36500" step="1" required value="${item?.duration||6}"></label><label>單位<select name="unit">${Object.entries(unitLabels).map(([v,l])=>`<option value="${v}">${l}</option>`).join("")}</select></label></div>`;
      if(!fixed)form.elements.unit.value=item?.unit||"months";
    };
    form.elements.mode.value=mode;typeFields();form.elements.mode.onchange=typeFields;
    form.querySelector(".cancel").onclick=()=>d.close();
    form.querySelector(".delete")?.addEventListener("click",()=>this.deleteDialog(item));
    form.onsubmit=e=>{
      e.preventDefault();const data=Object.fromEntries(new FormData(form));
      data.mode=mode;
      if(!item)data.mode=form.elements.mode.value;
      for(const key of ["duration","reminder_days"])if(key in data)data[key]=Number(data[key]);
      this.submit(form,async()=>{await this.api(item?"update":"create",item,data);d.close();});
    };
  }
  deleteDialog(item) {
    const d=this.openDialog("刪除項目",`<p>確定刪除「${esc(item.name)}」嗎？此項目的更換歷史與實體也會一起移除，無法從此頁復原。</p><form><div class="error" role="alert"></div><div class="actions"><button type="button">取消</button><button type="submit" class="danger">確認刪除</button></div></form>`);
    const form=d.querySelector("form");form.querySelector('[type="button"]').onclick=()=>d.close();
    form.onsubmit=e=>{e.preventDefault();this.submit(form,async()=>{await this.api("delete",item);d.close();});};
  }
  async historyDialog(item,add=false) {
    try {
      const detail=await this.api("get",item);
      const records=[...detail.history].sort((a,b)=>b.date.localeCompare(a.date)||b.created_at.localeCompare(a.created_at));
      const d=this.openDialog(add?"記錄更換":`${item.name} · 歷史`,`
        <p>${esc(item.name)}${item.mode==="lifetime"?" · 最新的更換日期決定目前倒數。":" · 保留建立及到期日變更紀錄。"}</p>
        <ul class="history">${records.map(record=>`<li><div class="record-head"><strong>${esc(record.date)}</strong><span class="muted">${({replacement:"更換紀錄",created:"建立項目",due_changed:"調整到期日"})[record.kind]||esc(record.kind)}</span></div>
        ${record.due_date?`<p>${record.previous_due_date?esc(record.previous_due_date)+" → ":""}到期：${esc(record.due_date)}</p>`:""}<p>${esc(record.note||"無備註")}</p>
        ${record.kind==="replacement"?`<div class="record-actions"><button class="small quiet" data-edit="${esc(record.id)}">修正</button><button class="small quiet danger" data-delete="${esc(record.id)}">刪除</button></div>`:""}</li>`).join("")}</ul>
        ${item.mode==="lifetime"?`<form><div class="error" role="alert"></div><div class="form-caption">新增更換紀錄</div><div class="form-grid">
        <label class="full">實際更換日期<input type="date" name="day" required max="${this.today}" value="${this.today}"></label>
        <label class="full">備註<textarea name="note" maxlength="2000" placeholder="型號、使用情況等（選填）"></textarea></label>
        </div><div class="actions"><button class="cancel" type="button">關閉</button><button class="primary" type="submit">儲存更換紀錄</button></div></form>`:""}`);
      if(item.mode!=="lifetime")return;
      const form=d.querySelector("form");let editing=null;
      form.querySelector(".cancel").onclick=()=>d.close();
      const save=async(action,payload)=>{
        await this.api("history",detail,{action,...payload});
        await this.refresh();await this.historyDialog({...item,revision:detail.revision+1});
      };
      form.onsubmit=e=>{e.preventDefault();this.submit(form,()=>save(editing?"edit":"add",
        {...Object.fromEntries(new FormData(form)),...(editing?{record_id:editing}:{})}));};
      d.querySelectorAll("[data-edit]").forEach(button=>button.onclick=()=>{
        const record=records.find(r=>r.id===button.dataset.edit);editing=record.id;
        form.elements.day.value=record.date;form.elements.note.value=record.note;
        form.querySelector(".form-caption").textContent="修正更換紀錄";
        form.querySelector('[type="submit"]').textContent="儲存修正";
        form.elements.day.focus();
      });
      d.querySelectorAll("[data-delete]").forEach(button=>button.onclick=()=>{
        if(button.dataset.confirm!=="yes"){button.dataset.confirm="yes";button.textContent="確定刪除這筆？";return;}
        this.submit(form,()=>save("delete",{record_id:button.dataset.delete}));
      });
      if(add)form.elements.day.focus();
    }catch(err){this.showError(err);}
  }
}

class DateCountdownCard extends HTMLElement {
  constructor(){super();this.attachShadow({mode:"open"});}
  static getConfigElement(){return document.createElement("date-countdown-card-editor");}
  static getStubConfig(){return {title:"日期倒數",entities:[]};}
  setConfig(config){
    if(config.entities!==undefined && (!Array.isArray(config.entities)||config.entities.some(e=>typeof e!=="string")))
      throw new Error("entities 必須是剩餘天數實體 ID 陣列");
    this.config={title:"日期倒數",...config};this.render();
  }
  set hass(value){this._hass=value;this.render();}
  getCardSize(){return Math.max(2,(this.config?.entities?.length||3)*2);}
  render(){
    if(!this.config||!this._hass)return;
    const ids=this.config.entities?.length?this.config.entities:Object.keys(this._hass.states).filter(id=>{
      const a=this._hass.states[id].attributes;return a.countdown_id && a.unit_of_measurement==="d";
    });
    const entries=ids.map(id=>{
      const s=this._hass.states[id];
      if(!s||["unknown","unavailable"].includes(s.state)||!Number.isFinite(Number(s.state)))return {id,unavailable:true,name:s?.attributes.friendly_name||id};
      const a=s.attributes,n=Number(s.state);
      return {...a,id,name:a.name||a.friendly_name||id,days_remaining:n,status:n<0?"overdue":n===0?"due":n<=(a.reminder_days??14)?"soon":"healthy"};
    }).filter(i=>!this.config.group||i.group===this.config.group)
      .sort((a,b)=>this.config.sort==="name"?a.name.localeCompare(b.name):(a.days_remaining??Infinity)-(b.days_remaining??Infinity));
    this.shadowRoot.innerHTML=`<style>${styles}</style><ha-card class="card"><div class="card-title"><span>${esc(this.config.title)}</span>${this._hass.user?.is_admin?'<a href="/date-countdown">管理 ↗</a>':""}</div>
      ${entries.map(i=>`<div class="card-row ${i.status||""}" role="button" tabindex="0" data-entity="${esc(i.id)}" aria-label="${esc(i.name)}">
        <div class="item-head"><div class="item-icon">${icon(i.mode==="fixed")}</div><div class="names"><h3>${esc(i.name)}</h3><p>${esc(i.group||"未分組")}${i.unavailable?"":" · "+esc(lifeLabel(i))}</p></div></div>
        ${i.unavailable?'<p class="muted">實體目前無法使用</p>':`<div class="balance"><strong>${daysLabel(i.days_remaining)}</strong><span>${Number(i.remaining_percentage)||0}%</span></div>${progress(i)}<div class="dates"><div><span>到期日期</span><b>${esc(i.due_date)}</b></div></div>`}</div>`).join("")||'<div class="empty">尚無倒數項目，請先新增項目或選擇實體。</div>'}</ha-card>`;
    this.shadowRoot.querySelectorAll("[data-entity]").forEach(row=>{
      const open=()=>emit(this,"hass-more-info",{entityId:row.dataset.entity});
      row.onclick=open;row.onkeydown=e=>{if(["Enter"," "].includes(e.key)){e.preventDefault();open();}};
    });
  }
}

class DateCountdownCardEditor extends HTMLElement {
  constructor(){super();this.attachShadow({mode:"open"});}
  setConfig(config){this.config={...config};this.render();}
  set hass(value){this._hass=value;if(!this._rendered)this.render();}
  render(){
    if(!this.config||!this._hass)return;
    this._rendered=true;
    const entities=Object.entries(this._hass.states).filter(([,s])=>s.attributes.countdown_id&&s.attributes.unit_of_measurement==="d");
    this.shadowRoot.innerHTML=`<style>${styles}label.pick{display:flex;align-items:center;gap:10px;padding:8px 0}input[type=checkbox]{width:18px;min-height:18px}p{font-size:13px;line-height:1.8;margin:12px 0}</style>
      <label>標題<input name="title" value="${esc(this.config.title||"日期倒數")}"></label>
      <p class="muted">勾選要顯示的項目；全部不勾選時會自動顯示所有項目。</p>
      ${entities.map(([id,s])=>`<label class="pick"><input type="checkbox" value="${esc(id)}" ${this.config.entities?.includes(id)?"checked":""}>${esc(s.attributes.name||s.attributes.friendly_name||id)}</label>`).join("")}
      <label>排序<select name="sort"><option value="due">到期日排序</option><option value="name">名稱排序</option></select></label>`;
    this.shadowRoot.querySelector('[name="sort"]').value=this.config.sort||"due";
    this.shadowRoot.onchange=()=>{
      const config={...this.config,title:this.shadowRoot.querySelector('[name="title"]').value,
        sort:this.shadowRoot.querySelector('[name="sort"]').value,
        entities:[...this.shadowRoot.querySelectorAll('input[type="checkbox"]:checked')].map(e=>e.value)};
      this.config=config;emit(this,"config-changed",{config});
    };
  }
}

if(!customElements.get("date-countdown-panel"))customElements.define("date-countdown-panel",DateCountdownPanel);
if(!customElements.get("date-countdown-card"))customElements.define("date-countdown-card",DateCountdownCard);
if(!customElements.get("date-countdown-card-editor"))customElements.define("date-countdown-card-editor",DateCountdownCardEditor);
window.customCards=window.customCards||[];
if(!window.customCards.some(c=>c.type==="date-countdown-card"))
  window.customCards.push({type:"date-countdown-card",name:"日期倒數",description:"耗材與固定到期日的進度、剩餘天數及到期狀態",preview:true});
