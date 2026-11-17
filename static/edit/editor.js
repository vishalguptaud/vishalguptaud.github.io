'use strict';
(() => {
  let schema=[],content={},section='',history=[],counter=0;
  const el=id=>document.getElementById(id);
  const make=(tag,text,className)=>{const node=document.createElement(tag);if(text!==undefined)node.textContent=text;if(className)node.className=className;return node;};
  const status=text=>{el('editor-status').textContent=text;};
  const clone=value=>JSON.parse(JSON.stringify(value));
  function remember(){history.push({section,data:clone(content[section])});if(history.length>30)history.shift();el('undo').disabled=false;}
  function get(path){return path.reduce((obj,key)=>obj[key],content[section]);}
  function set(path,value){let obj=content[section];for(const key of path.slice(0,-1))obj=obj[key];obj[path[path.length-1]]=value;status('Unsaved local changes. Download this file to keep them; the website has not changed.');}
  function defaults(fields){return Object.fromEntries(fields.map(f=>[f.name,f.widget==='list'?[]:f.widget==='boolean'?false:f.widget==='number'?new Date().getFullYear():f.widget==='select'?f.options[0]:f.widget==='color'?'#1f4d3a':'']));}
  function valid(value,field){
    const type=field.widget;
    if(type==='list')return Array.isArray(value)&&value.every(v=>field.fields?validObject(v,field.fields):valid(v,field.field));
    if(type==='boolean')return typeof value==='boolean';
    if(type==='number')return Number.isFinite(value);
    return typeof value==='string';
  }
  function validObject(value,fields){return value&&typeof value==='object'&&!Array.isArray(value)&&fields.every(f=>Object.hasOwn(value,f.name)&&valid(value[f.name],f));}
  function fieldUI(field,path){
    if(field.widget==='list')return listUI(field,path);
    const wrap=make('div',undefined,'editor-field');
    const id='field-'+(++counter);const label=make('label',field.label);label.htmlFor=id;
    const value=get(path);let input;
    if(field.widget==='text')input=make('textarea');
    else if(field.widget==='select'){input=make('select');for(const option of field.options){const op=make('option',option);op.value=option;input.append(op);}}
    else{input=make('input');input.type=field.widget==='boolean'?'checkbox':field.widget==='number'?'number':field.widget==='color'?'color':'text';}
    input.id=id;input.name=path.join('.');
    if(field.widget==='boolean')input.checked=value;else input.value=value;
    if(field.min!==undefined)input.min=field.min;if(field.max!==undefined)input.max=field.max;
    let recorded=false;input.addEventListener('focus',()=>{recorded=false;});
    input.addEventListener('input',()=>{if(!recorded){remember();recorded=true;}set(path,field.widget==='boolean'?input.checked:field.widget==='number'?Number(input.value):input.value);});
    wrap.append(label,input);if(field.hint)wrap.append(make('small',field.hint));
    return wrap;
  }
  function listUI(field,path){
    const wrap=make('section',undefined,'editor-list');wrap.append(make('h2',field.label));
    const values=get(path);
    values.forEach((value,index)=>{
      const item=make('details',undefined,'editor-item');
      const title=field.fields?(value.title||value.event||value.degree||value.label||value.code||field.label_singular||'Entry'):(value.slice(0,70)||'Paragraph');
      item.append(make('summary',(index+1)+'. '+title));
      const body=make('div',undefined,'editor-item-body');
      const itemPath=[...path,index];
      if(field.fields){for(const sub of field.fields)body.append(fieldUI(sub,[...itemPath,sub.name]));}
      else body.append(fieldUI(field.field,itemPath));
      const remove=make('button','Remove '+(field.label_singular||'entry'), 'remove-entry');remove.type='button';
      remove.addEventListener('click',()=>{remember();values.splice(index,1);status('Entry removed from this tab only. Use Undo to restore it.');render();});
      const moveUp=make('button','Move up');moveUp.type='button';moveUp.disabled=index===0;
      moveUp.addEventListener('click',()=>{remember();[values[index-1],values[index]]=[values[index],values[index-1]];render();status('Entry moved up locally.');});
      const moveDown=make('button','Move down');moveDown.type='button';moveDown.disabled=index===values.length-1;
      moveDown.addEventListener('click',()=>{remember();[values[index+1],values[index]]=[values[index],values[index+1]];render();status('Entry moved down locally.');});
      const tools=make('div',undefined,'editor-actions');tools.append(moveUp,moveDown,remove);body.append(tools);item.append(body);wrap.append(item);
    });
    const add=make('button','Add '+(field.label_singular||'entry'),'add-entry');add.type='button';
    add.addEventListener('click',()=>{remember();const atFront=['publications:items','teaching:courses','talks:items','photos:albums'].includes(section+':'+path.join('.'));const entry=field.fields?defaults(field.fields):'';if(atFront)values.unshift(entry);else values.push(entry);status('New entry added locally. Fill its fields, then download the updated file.');render();const items=Array.from(el('editor-form').querySelectorAll('details')).filter(d=>d.parentElement.dataset.path===path.join('.'));const target=atFront?items[0]:items[items.length-1];if(target){target.open=true;target.querySelector('input,textarea,select')?.focus();}});
    wrap.dataset.path=path.join('.');wrap.append(add);return wrap;
  }
  function render(){
    const form=el('editor-form');form.replaceChildren();counter=0;
    const def=schema.find(s=>s.name===section);
    for(const f of def.fields)form.append(fieldUI(f,[f.name]));
    el('file-path').textContent='Repository file: content/'+section+'.json';
  }
  function download(blob,name){const url=URL.createObjectURL(blob);const a=make('a');a.href=url;a.download=name;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),30000);}
  el('editor-form').addEventListener('submit',ev=>ev.preventDefault());
  el('section').addEventListener('change',()=>{section=el('section').value;render();status('Editing a local working copy. Other sections retain their changes in this tab.');});
  el('undo').addEventListener('click',()=>{const previous=history.pop();if(!previous)return;content[previous.section]=previous.data;section=previous.section;el('section').value=section;el('undo').disabled=!history.length;render();status('Last change undone locally.');});
  el('download').addEventListener('click',()=>{const def=schema.find(s=>s.name===section);if(!validObject(content[section],def.fields)){status('This content has an invalid field. Review it before downloading.');return;}download(new Blob([JSON.stringify(content[section],null,2)+'\n'],{type:'application/json'}),section+'.json');status('Downloaded '+section+'.json. This does not publish it; replace the matching repository file to publish through the build workflow.');});
  el('import-file').addEventListener('change',async()=>{
    const file=el('import-file').files[0];if(!file)return;
    try{if(file.size>4*1024*1024)throw new Error('The content file exceeds 4 MB.');const value=JSON.parse(await file.text());const def=schema.find(s=>s.name===section);if(!validObject(value,def.fields))throw new Error('This file does not match the selected content section.');remember();content[section]=value;render();status('Imported '+file.name+' into this tab only.');}catch(error){status('Import failed: '+error.message);}finally{el('import-file').value='';}
  });
  let photo=null;
  el('photo-file').addEventListener('change',()=>{photo=el('photo-file').files[0]||null;el('prepare-photo').disabled=!photo;el('photo-status').textContent=photo?'Ready to prepare a local JPEG copy.':'';});
  el('prepare-photo').addEventListener('click',async()=>{
    if(!photo)return;
    const file=photo;let source;
    try{
      if(!['image/jpeg','image/png','image/webp'].includes(file.type))throw new Error('Choose a JPEG, PNG, or WebP image.');
      if(file.size>40*1024*1024)throw new Error('Choose an image smaller than 40 MB.');
      source=URL.createObjectURL(file);const image=new Image();await new Promise((resolve,reject)=>{image.onload=resolve;image.onerror=()=>reject(new Error('The image could not be decoded.'));image.src=source;});
      if(image.width*image.height>50000000)throw new Error('Choose a photograph with fewer than 50 million pixels.');
      const scale=Math.min(1,2000/Math.max(image.width,image.height));const canvas=make('canvas');canvas.width=Math.max(1,Math.round(image.width*scale));canvas.height=Math.max(1,Math.round(image.height*scale));
      const ctx=canvas.getContext('2d');ctx.fillStyle='#ffffff';ctx.fillRect(0,0,canvas.width,canvas.height);ctx.drawImage(image,0,0,canvas.width,canvas.height);
      const blob=await new Promise(resolve=>canvas.toBlob(resolve,'image/jpeg',.88));if(!blob)throw new Error('JPEG export failed.');
      const name=(file.name.replace(/\.[^.]+$/,'').toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'')||'conference-photo')+'.jpg';
      download(blob,name);el('photo-status').textContent='Downloaded '+name+' ('+canvas.width+' × '+canvas.height+'). Upload this prepared copy to the CMS; keep the original private.';
    }catch(error){el('photo-status').textContent=error.message;}finally{if(source)URL.revokeObjectURL(source);}
  });
  Promise.all([fetch('schema.json',{credentials:'same-origin'}).then(r=>{if(!r.ok)throw new Error('Schema unavailable');return r.json();}),fetch('content.json',{credentials:'same-origin'}).then(r=>{if(!r.ok)throw new Error('Content unavailable');return r.json();})]).then(([defs,data])=>{
    schema=defs;content=data;for(const def of schema){if(!validObject(content[def.name],def.fields))throw new Error('Content does not match '+def.label);const option=make('option',def.label);option.value=def.name;el('section').append(option);}section=schema[0].name;render();status('Ready. Changes remain in this tab until downloaded.');
  }).catch(error=>{status('Unable to open the editor: '+error.message);el('download').disabled=true;});
})();
