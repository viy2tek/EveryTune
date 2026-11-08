import home from './home.mjs';

window.Home=home;
let phase=0;
window.setHomePhase=event=>{
  phase=home.transition(phase,event);
  document.body.dataset.homePhase=String(phase);
};

try {
  for (const [src,module] of [['app.js',false],['preferences.js',true],['coverage.js',false],['downloads.js',false]]) {
    await new Promise((resolve,reject)=>{
      const script=document.createElement('script');script.src='/static/'+src;
      if(module) script.type='module';
      script.onload=resolve;script.onerror=()=>reject(new Error('Não foi possível carregar a interface. Reabra o aplicativo.'));
      document.head.append(script);
    });
  }
} catch(error) {
  const message=document.createElement('p');message.className='startup-error';message.setAttribute('role','alert');
  message.textContent=error.message;document.querySelector('main').prepend(message);
}
