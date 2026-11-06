import React,{useCallback,useEffect,useState} from 'react';
import {alertsAPI} from '../services/api';
const panel={background:'#fff',borderRadius:12,padding:18,boxShadow:'0 4px 16px rgba(15,23,42,.06)'};
export default function ValidationsView({onRefresh}) {
 const [alerts,setAlerts]=useState([]),[loading,setLoading]=useState(true),[busy,setBusy]=useState(null),[error,setError]=useState('');
 const refresh=useCallback(async()=>{setLoading(true);setError('');try{setAlerts(await alertsAPI.getAlerts())}catch(e){setError(e.message)}finally{setLoading(false)}},[]);
 useEffect(()=>{refresh()},[refresh]);
 const decide=async(item,action)=>{setBusy(item.id);setError('');try{await alertsAPI.validateAlert(item.id,action,'',{...item,alert_id:item.id});await refresh();onRefresh?.()}catch(e){setError(e.message||'La decision n\'a pas pu etre enregistree.')}finally{setBusy(null)}};
 const details=(item)=>{const v=item.alert;if(typeof v==='string')return v;return v?.message||v?.recommendation||v?.resume||JSON.stringify(v||{})};
 return <section style={{maxWidth:1100,margin:'0 auto'}}><header style={{marginBottom:22}}><h1>Validations</h1><p>Consultez les d&eacute;cisions qui attendent la revue d'un gestionnaire.</p></header>{error&&<p role="alert" style={{color:'#b91c1c'}}>{error}</p>}{loading?<p>Chargement des validations...</p>:!alerts.length?<div style={panel}>Aucune validation en attente.</div>:<div style={{display:'grid',gap:14}}>{alerts.map(item=><article key={item.id} style={panel}><div style={{display:'flex',justifyContent:'space-between',gap:12,flexWrap:'wrap'}}><strong>Dossier {item.contrat_id||`#${item.id}`}</strong><span style={{color:'#b45309'}}>{String(item.validation_status||'En attente').replaceAll('_',' ')}</span></div><p style={{whiteSpace:'pre-wrap',color:'#475569'}}>{details(item)}</p><div style={{display:'flex',gap:8}}>{[['validate','Valider'],['reject','Rejeter'],['pas_maintenant','Reporter']].map(([action,label])=><button key={action} disabled={busy===item.id} onClick={()=>decide(item,action)}>{busy===item.id?'Enregistrement...':label}</button>)}</div></article>)}</div>}</section>;
}
