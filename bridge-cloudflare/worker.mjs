const reply=(data,status=200)=>Response.json(data,{status});
const kinds={torre:'rbxmx',arco:'rbxmx','blender-chanfro':'obj'};
const ticketPattern=/^[a-f0-9]{32}$/;
async function auth(req,key){
  if(typeof key!=='string'||key.length<32)return false;
  const enc=new TextEncoder();
  const [a,b]=await Promise.all([crypto.subtle.digest('SHA-256',enc.encode(req.headers.get('Authorization')||'')),crypto.subtle.digest('SHA-256',enc.encode('Bearer '+key))]);
  const x=new Uint8Array(a),y=new Uint8Array(b);let diff=0;
  for(let i=0;i<x.length;i++)diff|=x[i]^y[i];
  return diff===0;
}
async function readJson(req,max){
  const reader=req.body?.getReader(); if(!reader)throw Error('body');
  const decoder=new TextDecoder('utf-8',{fatal:true});let total=0,text='';
  for(;;){const {done,value}=await reader.read();if(done)break;total+=value.length;if(total>max){await reader.cancel();throw Error('size');} text+=decoder.decode(value,{stream:true});}
  return JSON.parse(text+decoder.decode());
}
export default {async fetch(req,env){
  const path=new URL(req.url).pathname;
  if(path==='/healthz'&&req.method==='GET')return reply({status:'ok'});
  const callback=path==='/delivery'&&req.method==='POST';
  if(!await auth(req,callback?env.WINDOWS_DELIVERY_KEY:env.STUDIO_BRIDGE_KEY))return reply({error:'Não autorizado.'},401);
  try{
    if(path==='/jobs'&&req.method==='POST'){
      let data;try{data=await readJson(req,2048);}catch{return reply({error:'Pedido inválido.'},400);}
      const preset=data?.preset;if(typeof preset!=='string'||!Object.hasOwn(kinds,preset))return reply({error:'Preset não permitido.'},400);
      const ticket=crypto.randomUUID().replaceAll('-',''), now=Math.floor(Date.now()/1000);
      const db=env.JOBS;
      const [,ins]=await db.batch([db.prepare('DELETE FROM jobs WHERE expires<=?').bind(now),db.prepare("INSERT INTO jobs(ticket,preset,expires,status) SELECT ?,?,?,'queued' WHERE (SELECT COUNT(*) FROM jobs)<32 AND (SELECT COUNT(*) FROM jobs WHERE status='queued')<8").bind(ticket,preset,now+900)]);
      if(!ins.meta.changes)return reply({error:'Fila cheia.'},429);
      let dispatched;
      try{dispatched=await fetch(`https://api.github.com/repos/${env.GITHUB_REPO}/actions/workflows/bloodyray-windows.yml/dispatches`,{method:'POST',headers:{Authorization:`Bearer ${env.GITHUB_TOKEN}`,'Content-Type':'application/json','User-Agent':'BloodyRayBridge','X-GitHub-Api-Version':'2022-11-28'},body:JSON.stringify({ref:'main',inputs:{ticket,preset}})});}catch{}
      if(!dispatched?.ok){await db.prepare("UPDATE jobs SET status='failed' WHERE ticket=? AND status='queued'").bind(ticket).run();return reply({error:'GitHub não confirmou o job.'},502);}
      return reply({ticket,status:'queued'});
    }
    if(callback){
      let data;try{data=await readJson(req,70000);}catch{return reply({error:'Entrega inválida.'},400);}
      if(typeof data?.ticket!=='string'||!ticketPattern.test(data.ticket))return reply({error:'Ticket inválido.'},400);
      const now=Math.floor(Date.now()/1000), job=await env.JOBS.prepare('SELECT preset FROM jobs WHERE ticket=? AND expires>?').bind(data.ticket,now).first();
      if(!job)return reply({error:'Ticket expirado ou inexistente.'},404);
      const good=data.status==='ready'&&data.format===kinds[job.preset]&&typeof data.content==='string'&&new TextEncoder().encode(data.content).length<=32000;
      if(!good&&data.status!=='failed')return reply({error:'Arquivo inválido.'},400);
      await env.JOBS.prepare("UPDATE jobs SET status=?,format=?,content=? WHERE ticket=? AND status='queued'").bind(good?'ready':'failed',good?data.format:null,good?data.content:null,data.ticket).run();
      return reply({status:'accepted'});
    }
    if(req.method==='GET'&&path.startsWith('/jobs/')){
      const ticket=path.slice(6);if(!ticketPattern.test(ticket))return reply({error:'Ticket inválido.'},404);
      const job=await env.JOBS.prepare('SELECT status,format,content FROM jobs WHERE ticket=? AND expires>?').bind(ticket,Math.floor(Date.now()/1000)).first();
      if(!job)return reply({error:'Pedido expirado ou inexistente.'},404);
      return reply(job.status==='ready'?job:{status:job.status});
    }
    return reply({error:'Rota não encontrada.'},404);
  }catch{return reply({error:'Ponte temporariamente indisponível.'},502);}
}};
