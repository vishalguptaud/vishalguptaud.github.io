'use strict';
window.CMS_MANUAL_INIT=true;
fetch('settings.json',{credentials:'same-origin'}).then(response=>{if(!response.ok)throw new Error('CMS settings could not be loaded.');return response.json();}).then(settings=>{
  const message=document.getElementById('cms-message');
  if(!settings.enabled){message.textContent='GitHub publishing is not connected yet. No login or publishing action is available here until the repository and secure authentication service are configured. You can use the local editor to try the content fields and download changes.';return;}
  message.textContent='Loading the authenticated content editor…';
  const script=document.createElement('script');script.src='https://cdn.jsdelivr.net/npm/decap-cms@3.16.3/dist/decap-cms.js';
  script.onload=()=>{document.getElementById('cms-status').hidden=true;window.CMS.init({config:settings.config});};
  script.onerror=()=>{message.textContent='The CMS could not load. No changes have been published. Use the local editor or try again later.';};
  document.head.append(script);
}).catch(error=>{document.getElementById('cms-message').textContent=error.message+' No changes have been published.';});
