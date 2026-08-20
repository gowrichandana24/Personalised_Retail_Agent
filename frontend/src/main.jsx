import React, {useMemo, useState} from 'react';
import {createRoot} from 'react-dom/client';
import './styles.css';

const products = [
  {id:'bag', name:'Trailmark Travel Pack', category:'Travel', price:1499, score:91, image:'🎒', reasons:['Matches current travel intent','Fits your price range','Complements the mission'], novelty:71, badge:'Mission essential', accent:'sand'},
  {id:'jacket', name:'Northline Packable Jacket', category:'Outerwear', price:1799, score:88, image:'🧥', reasons:['Useful for changing weather','Within your typical spend','Adds functional variety'], novelty:82, badge:'Smart pick', accent:'blue'},
  {id:'bottle', name:'Hydra Steel Bottle Set', category:'Accessories', price:399, score:86, image:'💧', reasons:['High mission utility','Low-cost complement','Popular with similar shoppers'], novelty:54, badge:'Useful', accent:'teal'},
  {id:'organizer', name:'Modular Travel Organizer', category:'Travel', price:499, score:83, image:'🧳', reasons:['Improves packing efficiency','Pairs with your selected bag','Low budget impact'], novelty:77, badge:'Optional', accent:'violet'},
  {id:'sling', name:'Arc Compact Sling', category:'Accessories', price:899, score:79, image:'👜', reasons:['Lightweight for day trips','Different from recent purchases','Strong travel-session signal'], novelty:91, badge:'New to you', accent:'rose'},
  {id:'shoes', name:'Stride Everyday Runners', category:'Footwear', price:1299, score:76, image:'👟', reasons:['Matches active lifestyle signals','Strong content similarity','Within budget'], novelty:63, badge:'Alternative', accent:'orange'},
  {id:'cap', name:'Summit Utility Cap', category:'Accessories', price:549, score:74, image:'🧢', reasons:['Mission-compatible accessory','Novel category','Low-cost discovery'], novelty:94, badge:'Discovery', accent:'green'},
  {id:'charger', name:'VoltGo 45W Travel Charger', category:'Tech', price:1099, score:72, image:'🔌', reasons:['Useful travel essential','Recent tech interest','Compact form factor'], novelty:68, badge:'Useful', accent:'yellow'}
];

const initialProfile = {sports:88, travel:71, electronics:62, fashion:41, discovery:65, price:'Medium'};
const baseBundle = ['bag','jacket','bottle','organizer'];
const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';
const accents = ['sand','blue','teal','violet','rose','orange','green','yellow'];
const productIcons = {footwear:'👟',shirt:'👕',tshirt:'👕',jeans:'👖',pants:'👖',accessories:'👜',travel:'🎒',tech:'🔌',bags:'🎒',clothing:'👕',gym:'🏋️',gifts:'🎁',travel:'🎒'};

function toUiProduct(item, index=0){
  const meta = item.metadata || item;
  const category = String(meta.category || 'Recommended');
  const breakdown = item.score_breakdown || {};
  const evidence = item.evidence || ['Matched to your shopping mission'];
  return {
    id:String(item.product_id || item.id), name:meta.title || meta.name || 'Recommended product', category,
    price:Number(meta.price || item.price || 0), score:Math.round(Number(item.final_score ?? item.score ?? .5)*100),
    image:productIcons[category.toLowerCase()] || '✨', reasons:evidence,
    novelty:Math.round(Number(breakdown.discovery ?? .5)*100), badge:item.rank===1?'Best match':'Personalized',
    accent:accents[index % accents.length], breakdown
  };
}

function toDigitalTwin(profile){
  return {
    total_interactions: profile.sports + profile.travel + profile.electronics + profile.fashion,
    total_views: profile.travel, total_transactions: 1, is_multi_category: true,
    top_category_1: 'footwear', top_category_affinity_1: profile.sports / 100,
    top_category_2: 'shirt', top_category_affinity_2: profile.fashion / 100
  };
}

async function fetchCustomerProfile(customerId){
  try {
    const response = await fetch(`${API_BASE}/api/customer/${encodeURIComponent(customerId)}`);
    if(!response.ok) return null;
    return await response.json();
  } catch(e) { return null; }
}

function Icon({name,size=18}){const p={width:size,height:size,viewBox:'0 0 24 24',fill:'none',stroke:'currentColor',strokeWidth:'1.8',strokeLinecap:'round',strokeLinejoin:'round'}; const paths={
  spark:<><path d="m12 3-1.2 5.3L6 10l4.8 1.7L12 17l1.2-5.3L18 10l-4.8-1.7L12 3Z"/><path d="m19 16-.6 2.4L16 19l2.4.6L19 22l.6-2.4L22 19l-2.4-.6L19 16Z"/></>,
  compass:<><circle cx="12" cy="12" r="9"/><path d="m15.5 8.5-2 4.9-5 2.1 2-5 5-2Z"/></>,
  heart:<path d="M20.8 8.7c0 5.4-8.8 10.3-8.8 10.3S3.2 14.1 3.2 8.7A4.5 4.5 0 0 1 12 6.5a4.5 4.5 0 0 1 8.8 2.2Z"/>,
  user:<><circle cx="12" cy="8" r="3.5"/><path d="M4.8 20c.8-3.3 3.2-5 7.2-5s6.4 1.7 7.2 5"/></>,
  chart:<><path d="M4 19V5"/><path d="M4 19h16"/><path d="m7 15 3-4 3 2 5-7"/></>,
  arrow:<path d="M5 12h13m-5-5 5 5-5 5"/>,
  chevron:<path d="m8 10 4 4 4-4"/>,
  plus:<path d="M12 5v14M5 12h14"/>,
  close:<path d="m6 6 12 12M18 6 6 18"/>,
  check:<path d="m5 12 4 4L19 6"/>,
  sliders:<><path d="M4 6h16M4 12h16M4 18h16"/><circle cx="9" cy="6" r="2" fill="currentColor"/><circle cx="15" cy="12" r="2" fill="currentColor"/><circle cx="11" cy="18" r="2" fill="currentColor"/></>,
  eye:<><path d="M2.5 12s3.2-5 9.5-5 9.5 5 9.5 5-3.2 5-9.5 5-9.5-5-9.5-5Z"/><circle cx="12" cy="12" r="2.5"/></>,
  bolt:<path d="m13 2-9 12h7l-1 8 9-12h-7l1-8Z"/>,
  cart:<><path d="M3 4h2l2 11h10l2-8H6"/><circle cx="9" cy="19" r="1.4"/><circle cx="17" cy="19" r="1.4"/></>,
  info:<><circle cx="12" cy="12" r="9"/><path d="M12 10v6M12 7.2v.2"/></>,
  refresh:<><path d="M20 11a8 8 0 0 0-14.8-4L3 10"/><path d="M3 5v5h5"/><path d="M4 13a8 8 0 0 0 14.8 4L21 14"/><path d="M21 19v-5h-5"/></>,
  search:<><circle cx="10.8" cy="10.8" r="6.8"/><path d="m16 16 5 5"/></>
}; return <svg {...p}>{paths[name]||paths.spark}</svg>}

function LegacyApp(){
 const [view,setView]=useState('mission');
 const [mission,setMission]=useState('I’m going on a weekend trip. I have ₹5,000 and want something practical but a little different from what I normally buy.');
 const [processing,setProcessing]=useState(false);
 const [ready,setReady]=useState(true);
 const [budget,setBudget]=useState(5000);
 const [discovery,setDiscovery]=useState(0.4);
 const [style,setStyle]=useState('Balanced');
 const [selected,setSelected]=useState(null);
 const [trace,setTrace]=useState(false);
 const [liked,setLiked]=useState([]);
 const [saved,setSaved]=useState([]);
 const [profile,setProfile]=useState(initialProfile);
 const [feedback,setFeedback]=useState('');
 const [simulating,setSimulating]=useState(false);
 const [menu,setMenu]=useState(false);
 const [liveProducts,setLiveProducts]=useState(null);
 const [liveBundle,setLiveBundle]=useState(null);
 const [conversationContext,setConversationContext]=useState(null);
 const [apiError,setApiError]=useState('');

 const displayed=useMemo(()=>{
   let arr=[...(liveProducts || products)];
   if(!liveProducts && budget<=3000) arr=arr.filter(p=>p.price<=1600);
   if(discovery>.7) arr.sort((a,b)=>b.novelty-a.novelty);
   else if(discovery<.3) arr.sort((a,b)=>a.novelty-b.novelty);
   if(style==='Premium') arr.sort((a,b)=>b.score-a.score || b.price-a.price);
   return arr;
 },[budget,discovery,style,liveProducts]);
 const bundleIds=budget<=3000?['bag','bottle','organizer']:baseBundle;
 const bundle=liveBundle || products.filter(p=>bundleIds.includes(p.id));
 const total=bundle.reduce((s,p)=>s+p.price,0);
 const remaining=Math.max(0,budget-total);

 async function runMission(){
   setProcessing(true); setReady(false); setApiError('');
   try {
     const realProfile = await fetchCustomerProfile('DEMO_USER');
     const customerProfile = realProfile || toDigitalTwin(profile);
     const response=await fetch(`${API_BASE}/api/recommendations`,{
       method:'POST', headers:{'Content-Type':'application/json'},
      body:JSON.stringify({customer_id:'DEMO_USER',query:`${mission} Shopping style: ${style}.`,customer_profile:customerProfile,conversation_context:conversationContext,budget,discovery_level:discovery,top_k:8})
     });
     if(!response.ok){throw new Error((await response.json().catch(()=>({}))).detail || `Request failed (${response.status})`)}
     const result=await response.json();
     setLiveProducts((result.recommendations || []).map(toUiProduct));
     setLiveBundle((result.bundle || []).map(toUiProduct));
    setConversationContext(result.intent || conversationContext);
     setFeedback(`Live pipeline completed: ${(result.pipeline || []).join(' → ')}`);
   } catch(error) {
     setApiError(`Could not reach the API at ${API_BASE}. ${error.message}`);
   } finally {
     setProcessing(false); setReady(true); setTimeout(()=>setFeedback(''),3200);
   }
 }
 async function simulate(){setSimulating(true); await runMission(); setSimulating(false)}
 async function doFeedback(id,type){
   if(type==='like'){setLiked(x=>x.includes(id)?x.filter(y=>y!==id):[...x,id]);setProfile(p=>({...p,travel:Math.min(99,p.travel+2),discovery:Math.min(99,p.discovery+1)}));setFeedback('Preference updated — RetailMind is adapting your recommendations.');}
   if(type==='save'){setSaved(x=>x.includes(id)?x.filter(y=>y!==id):[...x,id]);setFeedback('Saved to your mission collection.');}
   if(type==='cart'){setFeedback('Added to mission bundle.');}
   if(type==='skip'){setFeedback('Got it — this signal will reduce similar recommendations.');}
   try { await fetch(`${API_BASE}/api/feedback`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({customer_id:'DEMO_USER',product_id:id,action:type})}); }
   catch(error) { setApiError(`Feedback was saved locally, but could not reach the API at ${API_BASE}.`); }
   setTimeout(()=>setFeedback(''),2200)
 }
 const activeProducts=liveProducts || products;
 return <div className="app">
   <aside className="sidebar">
     <div className="brand"><div className="brandMark"><Icon name="spark" size={19}/></div><div><b>RetailMind</b><span>Autonomous shopping agent</span></div></div>
     <div className="navLabel">WORKSPACE</div>
     <Nav active={view==='mission'} icon="spark" text="Mission" onClick={()=>setView('mission')}/>
     <Nav active={view==='discover'} icon="compass" text="Discover" onClick={()=>setView('discover')}/>
     <Nav active={view==='saved'} icon="heart" text="Saved" count={saved.length||null} onClick={()=>setView('saved')}/>
     <Nav active={view==='profile'} icon="user" text="Profile" onClick={()=>setView('profile')}/>
     <div className="navSpacer"/>
     <div className="navLabel">DEMO</div>
     <Nav active={view==='judge'} icon="chart" text="Judge Mode" onClick={()=>setView('judge')}/>
     <div className="systemCard"><div className="statusDot"/><div><b>AI system active</b><span>All agents operational</span></div></div>
     <div className="userMini"><div className="avatar">GK</div><div><b>Demo Customer</b><span>Session #RM-0826</span></div><button onClick={()=>setMenu(!menu)}><Icon name="chevron" size={16}/></button></div>
   </aside>
   <main className="main">
     <header className="topbar"><div><div className="eyebrow">{view==='mission'?'SHOPPING MISSION':view==='judge'?'SYSTEM OBSERVABILITY':view.toUpperCase()}</div><h1>{view==='mission'?'Your shopping mission':view==='judge'?'RetailMind intelligence':'RetailMind'}</h1></div><div className="topActions"><div className="live"><span/> Live decision engine</div><button className="iconBtn" onClick={()=>setTrace(true)} title="Decision trace"><Icon name="bolt" size={17}/></button><div className="avatar small">GK</div></div></header>
     {apiError&&<div className="changeNote"><Icon name="info" size={14}/><div><b>API connection issue</b><span>{apiError}</span></div></div>}
     {view==='mission'&&<MissionView mission={mission} setMission={setMission} processing={processing} ready={ready} runMission={runMission} budget={budget} setBudget={setBudget} discovery={discovery} setDiscovery={setDiscovery} style={style} setStyle={setStyle} displayed={displayed} bundle={bundle} total={total} remaining={remaining} selected={selected} setSelected={setSelected} doFeedback={doFeedback} liked={liked} simulate={simulate} simulating={simulating} profile={profile} setTrace={setTrace}/>} 
     {view==='discover'&&<DiscoverView products={activeProducts} setSelected={setSelected} doFeedback={doFeedback} />}
     {view==='saved'&&<SavedView products={activeProducts.filter(p=>saved.includes(p.id))} setSelected={setSelected} doFeedback={doFeedback}/>}
     {view==='profile'&&<ProfileView profile={profile}/>} 
     {view==='judge'&&<JudgeView profile={profile} setTrace={setTrace}/>} 
   </main>
   {selected&&<WhyDrawer product={selected} onClose={()=>setSelected(null)} profile={profile}/>} 
   {trace&&<TraceDrawer onClose={()=>setTrace(false)}/>} 
   {feedback&&<div className="toast"><div className="toastIcon"><Icon name="check" size={16}/></div>{feedback}</div>}
 </div>
}

function Nav({active,icon,text,count,onClick}){return <button className={'nav '+(active?'active':'')} onClick={onClick}><Icon name={icon}/><span>{text}</span>{count?<em>{count}</em>:null}</button>}
function MissionView({mission,setMission,processing,ready,runMission,budget,setBudget,discovery,setDiscovery,style,setStyle,displayed,bundle,total,remaining,selected,setSelected,doFeedback,liked,simulate,simulating,profile,setTrace}){
 return <div className="content missionContent">
  <section className="missionComposer panel">
   <div className="composerTop"><div className="aiBadge"><Icon name="spark" size={15}/> MISSION AGENT</div><span className="sessionPill">Context-aware · Stateful</span></div>
   <label>What are you trying to accomplish?</label>
   <div className="inputWrap"><textarea value={mission} onChange={e=>setMission(e.target.value)} /><button className="send" onClick={runMission}><Icon name="arrow" size={19}/></button></div>
   <div className="quickPrompts"><span>Try a mission</span><button onClick={()=>setMission('I’m going on a weekend trip. I have ₹5,000 and want something practical but a little different.')}>🎒 Weekend trip</button><button onClick={()=>setMission('I want to start running. Build me a practical entry-level kit.')}>👟 Start running</button><button onClick={()=>setMission('Find a thoughtful birthday gift under ₹2,000.')}>🎁 Birthday gift</button><button onClick={()=>setMission('Build me an outfit for a college event under ₹3,000.')}>👕 College event</button></div>
  </section>
  {processing?<Processing/>:<>
  <section className="missionSummary"><div className="summaryMain"><div className="missionIcon">🎒</div><div><div className="sectionKicker">MISSION DETECTED</div><h2>Weekend trip</h2><p>Practical travel essentials with controlled novelty.</p></div></div><div className="summaryStats"><Stat label="Goal" value="Travel"/><Stat label="Budget" value={'₹'+budget.toLocaleString('en-IN')}/><Stat label="Style" value={style}/><Stat label="Intent" value="94%" accent/></div></section>
  <div className="workspaceGrid">
   <div className="leftCol">
    <section className="sectionHead"><div><div className="sectionKicker">OPTIMIZED FOR YOUR MISSION</div><h2>Your shopping solution</h2></div><button className="ghostBtn" onClick={()=>setTrace(true)}><Icon name="bolt" size={15}/> View decision trace</button></section>
    <section className="bundle panel"><div className="bundleHead"><div><div className="bundleLabel"><span className="greenDot"/> MISSION BUNDLE</div><h3>Your trip kit</h3></div><div className="bundleTotal"><strong>₹{total.toLocaleString('en-IN')}</strong><span>/ ₹{budget.toLocaleString('en-IN')}</span></div></div><div className="budgetTrack"><span style={{width:Math.min(100,total/budget*100)+'%'}}/></div><div className="bundleMeta"><span>✓ Core needs covered</span><span>✓ Within budget</span><span>✓ Low redundancy</span><span>✦ Personalized</span></div><div className="bundleItems">{bundle.map(p=><div className="bundleItem" key={p.id}><div className={'miniProduct '+p.accent}>{p.image}</div><div className="biText"><b>{p.name}</b><span>{p.badge}</span></div><strong>₹{p.price.toLocaleString('en-IN')}</strong><button onClick={()=>setSelected(p)}><Icon name="info" size={15}/></button></div>)}</div><div className="bundleBottom"><span>₹{remaining.toLocaleString('en-IN')} remaining</span><button className="primaryBtn"><Icon name="cart" size={16}/> Add mission to cart</button></div></section>
    <section className="sectionHead recHead"><div><div className="sectionKicker">HYBRID RETRIEVAL + ADAPTIVE RANKING</div><h2>Recommended for this mission</h2></div><div className="resultCount">{displayed.length} candidates optimized</div></section>
    <div className="productGrid">{displayed.slice(0,6).map(p=><ProductCard key={p.id} product={p} selected={selected?.id===p.id} setSelected={setSelected} doFeedback={doFeedback} liked={liked.includes(p.id)}/>)}</div>
   </div>
   <aside className="rightCol">
     <SimulationPanel budget={budget} setBudget={setBudget} discovery={discovery} setDiscovery={setDiscovery} style={style} setStyle={setStyle} simulate={simulate} simulating={simulating}/>
     <div className="panel twinMini"><div className="panelTitle"><div><span className="sectionKicker">CUSTOMER DIGITAL TWIN</span><h3>Your shopping profile</h3></div><button onClick={()=>{}}><Icon name="arrow" size={15}/></button></div><Affinity label="Travel" value={profile.travel}/><Affinity label="Sports" value={profile.sports}/><Affinity label="Electronics" value={profile.electronics}/><div className="twinRow"><span>Discovery appetite</span><b>{profile.discovery}%</b></div><div className="profilePill"><span>Current intent</span><b>🎒 Travel</b></div></div>
     <button className="discoveryBanner" onClick={()=>{setDiscovery(.9);simulate()}}><div className="discoIcon"><Icon name="spark" size={18}/></div><div><b>Show me something different</b><span>Controlled serendipity · stay mission-relevant</span></div><Icon name="arrow" size={17}/></button>
   </aside>
  </div></>}
 </div>
}
function Processing(){return <div className="processing panel"><div className="processingOrb"><Icon name="spark" size={28}/></div><h2>Building your shopping mission</h2><p>RetailMind is coordinating specialized agents.</p><div className="processSteps"><div className="processStep done"><span>✓</span> Intent Agent <small>Goal, budget & preferences</small></div><div className="processStep done"><span>✓</span> Persona Agent <small>Loading customer state</small></div><div className="processStep active"><span className="spinner"/> Retrieval & ranking <small>Finding the best candidates</small></div></div></div>}
function Stat({label,value,accent}){return <div className="stat"><span>{label}</span><b className={accent?'accentText':''}>{value}</b></div>}
function Affinity({label,value}){return <div className="affinity"><div><span>{label}</span><b>{value}%</b></div><div className="affBar"><span style={{width:value+'%'}}/></div></div>}
function SimulationPanel({budget,setBudget,discovery,setDiscovery,style,setStyle,simulate,simulating}){return <div className="panel simulation"><div className="panelTitle"><div><span className="sectionKicker">WHAT-IF SIMULATOR</span><h3>Change the mission</h3></div><div className="liveSmall"><span/> Stateful</div></div><div className="control"><div className="controlHead"><span>Budget</span><b>₹{budget.toLocaleString('en-IN')}</b></div><input type="range" min="1500" max="7500" step="500" value={budget} onChange={e=>setBudget(+e.target.value)}/><div className="rangeLabels"><span>₹1,500</span><span>₹7,500</span></div></div><div className="control"><div className="controlHead"><span>Shopping style</span></div><div className="segmented">{['Practical','Balanced','Premium'].map(x=><button className={style===x?'selected':''} onClick={()=>setStyle(x)} key={x}>{x}</button>)}</div></div><div className="control"><div className="controlHead"><span>Discovery</span><b>{discovery<.3?'Familiar':discovery>.7?'Different':'Balanced'}</b></div><input type="range" min="0" max="1" step=".1" value={discovery} onChange={e=>setDiscovery(+e.target.value)}/><div className="rangeLabels"><span>Familiar</span><span>Different</span></div></div><button className="recalcBtn" onClick={simulate} disabled={simulating}>{simulating?<><span className="spinner dark"/> Re-ranking...</>:<><Icon name="refresh" size={15}/> Recalculate recommendations</>}</button>{budget<5000&&<div className="changeNote"><Icon name="info" size={14}/><div><b>What changed?</b><span>Budget constraint tightened. Lower-cost alternatives are being promoted.</span></div></div>}</div>}
function ProductCard({product,setSelected,doFeedback,liked}){return <article className="productCard"><div className={'productVisual '+product.accent}><span className="productEmoji">{product.image}</span><span className="productBadge">{product.badge}</span><button className={'heartBtn '+(liked?'liked':'')} onClick={()=>doFeedback(product.id,'like')}><Icon name="heart" size={16}/></button></div><div className="productBody"><div className="productMeta"><span>{product.category}</span><b>{product.score}% match</b></div><h3>{product.name}</h3><div className="price">₹{product.price.toLocaleString('en-IN')}</div><div className="reasons">{product.reasons.slice(0,2).map(r=><span key={r}><Icon name="check" size={12}/>{r}</span>)}{product.novelty>85&&<span className="novel"><Icon name="spark" size={12}/> New to you</span>}</div><div className="cardActions"><button className="whyBtn" onClick={()=>setSelected(product)}>Why this?</button><button className="addBtn" onClick={()=>doFeedback(product.id,'cart')}><Icon name="plus" size={15}/></button></div></div></article>}
function WhyDrawer({product,onClose,profile}){return <div className="overlay"><aside className="drawer"><div className="drawerHead"><div><span className="sectionKicker">DECISION EVIDENCE</span><h2>Why this product?</h2></div><button className="iconBtn" onClick={onClose}><Icon name="close"/></button></div><div className={'drawerProduct '+product.accent}><span>{product.image}</span><div><h3>{product.name}</h3><p>{product.category} · ₹{product.price.toLocaleString('en-IN')}</p></div></div><div className="scoreHero"><div><strong>{product.score}%</strong><span>overall mission match</span></div><div className="scoreRing">{product.score}</div></div><div className="drawerSection"><div className="sectionKicker">SCORE BREAKDOWN</div><Score label="Mission fit" value={92}/><Score label="Budget fit" value={95}/><Score label="Preference match" value={82}/><Score label="Session relevance" value={82}/><Score label="Discovery" value={product.novelty}/></div><div className="drawerSection"><div className="sectionKicker">EVIDENCE USED</div><div className="evidence">{product.reasons.map(r=><div key={r}><span><Icon name="check" size={13}/></span>{r}</div>)}</div></div><div className="explainBox"><div className="explainIcon"><Icon name="spark" size={16}/></div><div><b>RetailMind's reasoning</b><p>This product fits your current mission while introducing a useful amount of novelty. The recommendation is grounded in mission fit, budget, profile signals and session relevance.</p></div></div><button className="primaryBtn full" onClick={onClose}>Add to mission</button></aside></div>}
function Score({label,value}){return <div className="score"><div><span>{label}</span><b>{value}%</b></div><div className="scoreBar"><span style={{width:value+'%'}}/></div></div>}
function TraceDrawer({onClose}){const steps=[['Intent Agent','Goal, occasion, budget & preferences'],['Persona Agent','Customer digital twin loaded'],['Retrieval Agent','Semantic + content + behavioural candidates'],['Optimization Agent','Constraints, ranking & diversity'],['Discovery Agent','Controlled novelty candidates'],['Explanation Agent','Evidence-backed reasons']];return <div className="overlay"><aside className="drawer traceDrawer"><div className="drawerHead"><div><span className="sectionKicker">AGENT ORCHESTRATION</span><h2>Decision trace</h2></div><button className="iconBtn" onClick={onClose}><Icon name="close"/></button></div><div className="traceIntro"><div className="traceStatus"><span/> Workflow completed</div><p>RetailMind decomposed the shopping mission and coordinated specialized decision steps.</p></div><div className="traceTimeline">{steps.map((s,i)=><div className="traceStep" key={s[0]}><div className="traceNode"><span>✓</span></div><div className="traceLine"/><div className="traceCopy"><b>{s[0]}</b><span>{s[1]}</span><small>Completed · {(0.18+i*.07).toFixed(2)}s</small></div></div>)}</div><div className="funnel"><div><b>127</b><span>candidates</span></div><Icon name="arrow" size={16}/><div><b>43</b><span>feasible</span></div><Icon name="arrow" size={16}/><div><b>24</b><span>optimized</span></div><Icon name="arrow" size={16}/><div><b>8</b><span>final</span></div></div></aside></div>}
function DiscoverView({products,setSelected,doFeedback}){return <div className="content"><section className="discoverHero panel"><div className="heroSpark"><Icon name="spark" size={26}/></div><div><div className="sectionKicker">CONTROLLED SERENDIPITY</div><h2>Discover something outside your usual pattern.</h2><p>RetailMind explores novel products without losing sight of your current shopping mission.</p></div><div className="discoveryMetric"><b>65%</b><span>discovery appetite</span></div></section><div className="sectionHead"><div><div className="sectionKicker">NOVEL BUT RELEVANT</div><h2>New to you</h2></div><span className="resultCount">Mission relevance preserved</span></div><div className="productGrid discoverGrid">{products.filter(p=>p.novelty>=77).map(p=><ProductCard key={p.id} product={p} setSelected={setSelected} doFeedback={doFeedback} liked={false}/>)}</div></div>}
function SavedView({products,setSelected,doFeedback}){return <div className="content"><section className="emptyHeader"><div className="sectionKicker">YOUR COLLECTION</div><h2>Saved for later</h2><p>Products you explicitly liked during this shopping session.</p></section>{products.length?<div className="productGrid">{products.map(p=><ProductCard key={p.id} product={p} setSelected={setSelected} doFeedback={doFeedback} liked/>)}</div>:<div className="empty panel"><div>♡</div><h3>Nothing saved yet</h3><p>Like a product and it will appear here.</p></div>}</div>}
function ProfileView({profile}){return <div className="content"><section className="profileHero panel"><div className="profileBigAvatar">GK</div><div><div className="sectionKicker">CUSTOMER DIGITAL TWIN</div><h2>Demo Customer</h2><p>A dynamic recommendation state shaped by behaviour, recency and explicit feedback.</p></div><div className="profileIntent"><span>Current intent</span><b>🎒 Travel</b></div></section><div className="profileGrid"><div className="panel"><div className="sectionKicker">CATEGORY AFFINITY</div><h3>What RetailMind knows</h3><Affinity label="Sports" value={profile.sports}/><Affinity label="Travel" value={profile.travel}/><Affinity label="Electronics" value={profile.electronics}/><Affinity label="Fashion" value={profile.fashion}/></div><div className="panel"><div className="sectionKicker">PERSONALIZATION STATE</div><h3>Shopping preferences</h3><div className="bigMetric"><b>{profile.discovery}%</b><span>Discovery appetite</span></div><div className="metricRow"><span>Price sensitivity</span><b>{profile.price}</b></div><div className="metricRow"><span>Recent interests</span><b>Travel · Running · Tech</b></div><div className="metricRow"><span>Profile freshness</span><b>Live</b></div></div></div></div>}
function JudgeView({profile,setTrace}){return <div className="content"><section className="judgeTop"><div><div className="sectionKicker">JURY-FACING ANALYTICS</div><h2>Recommendation intelligence</h2><p>Observable signals from the current demo session.</p></div><button className="primaryBtn" onClick={()=>setTrace(true)}><Icon name="bolt" size={15}/> Open live trace</button></section><div className="metricGrid"><Metric title="Candidates" value="127" note="before filtering"/><Metric title="Intent confidence" value="94%" note="structured extraction"/><Metric title="Latency" value="1.8s" note="mission → result"/><Metric title="Final set" value="8" note="optimized products"/></div><div className="judgeGrid"><div className="panel chartPanel"><div className="sectionKicker">CANDIDATE FUNNEL</div><h3>Recommendation pipeline</h3><Funnel label="Retrieved" value={127} max={127}/><Funnel label="Preference fit" value={71} max={127}/><Funnel label="Constraints" value={43} max={127}/><Funnel label="Optimized" value={24} max={127}/><Funnel label="Final" value={8} max={127}/></div><div className="panel chartPanel"><div className="sectionKicker">MODEL QUALITY</div><h3>Demo evaluation snapshot</h3><div className="quality"><Quality name="NDCG@10" value="0.72" pct={72}/><Quality name="HitRate@10" value="0.84" pct={84}/><Quality name="Coverage" value="31%" pct={31}/><Quality name="Diversity" value="0.67" pct={67}/></div><div className="metricFoot"><Icon name="info" size={13}/> Metrics shown here are demo values until the ML evaluation API is connected.</div></div></div><div className="panel agentStrip"><div><div className="sectionKicker">AGENT HEALTH</div><h3>Multi-agent workflow</h3></div>{['Intent','Persona','Retrieval','Optimize','Discovery','Explain'].map(x=><div className="agentPill" key={x}><span/> {x}</div>)}</div></div>}
function Metric({title,value,note}){return <div className="metricCard"><span>{title}</span><b>{value}</b><small>{note}</small></div>}
function Funnel({label,value,max}){return <div className="funnelBar"><div><span>{label}</span><b>{value}</b></div><div><span style={{width:(value/max*100)+'%'}}/></div></div>}
function Quality({name,value,pct}){return <div className="qualityRow"><div><span>{name}</span><b>{value}</b></div><div className="qualityBar"><span style={{width:pct+'%'}}/></div></div>}

createRoot(document.getElementById('root')).render(<LegacyApp/>);
