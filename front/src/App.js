import React, {useEffect, useState} from 'react';
import { db} from'./firebaseConfig';
import { doc, onSnapshot} from "firebase/firestore";

import KRGraph from './components/kr/KRGraph';
import KRTable from './components/kr/KRTable';
import KRNews from './components/kr/KRNews';
import USGraph from'./components/us/USGraph';
import USTable from './components/us/USTable';
import USNews from './components/us/USNews';
import GlobalFinance from './components/finance/GlobalFinance';

import './App.css';

function App() {
  const [krRank, setKrRank] = useState([]);
  const [usRank, setUsRank] = useState([]);
  const [krNews, setKrNews] = useState({});
  const [usNews, setUsNews] = useState({});
  const [globalFinance, setGlobalFinance] = useState({ bonds:{}, items: []});
  
  const [activeTab, setActiveTab] = useState('FINANCE');

  const[activeSubMenu, setActiveSubMenu] = useState('NEWS');

  useEffect(() => {
    onSnapshot(doc(db, 'market_data', 'global_indices'), (d) => setGlobalFinance(d.data() || {bonds:{}, items:[]}));
    onSnapshot(doc(db, 'stock_news', 'news_kr'), (d) => setKrNews(d.data() || {}));
    onSnapshot(doc(db, 'stock_news', 'news_us'), (d) => setUsNews(d.data() || {}));
    onSnapshot(doc(db, 'rs_data', 'latest'), (d) => setKrRank(d.data()?.rankings || []));
    onSnapshot(doc(db, 'rs_data', 'us_latest'), (d) => setUsRank(d.data()?.rankings || []));
    
  })

    return (  
      <div className = "dashboard">
        <header className = "main-header">
          <h2>Finance Summary</h2>
        
        <div className="main-tab-group">
          <button
            className={`main-btn ${activeTab === 'FINANCE' ? 'active' : ''}`}
            onClick={() => setActiveTab('FINANCE')}
            >FINANCE</button>
          <button
          className = {` main-btn ${activeTab === 'KOREA' ? 'active' : ''}`}
          onClick={() => {setActiveTab('KOREA'); setActiveSubMenu('NEWS');}}
          >KOREA</button>
           <button
          className = {` main-btn ${activeTab === 'USA' ? 'active' : ""}`}
          onClick={() => {setActiveTab('USA'); setActiveSubMenu('NEWS');}}
          >USA</button>   
        </div>

        {(activeTab === 'KOREA' || activeTab === 'USA') && (
          <div className = "sub-menu-group">
            <button className = {`sub-btn ${activeSubMenu === 'NEWS' ? 'active' : ''}`} onClick={()=> setActiveSubMenu('NEWS')}>뉴스</button>
            <button className = {`sub-btn ${activeSubMenu === 'RS_INDEX' ? 'active' : ''}`} onClick={()=> setActiveSubMenu('RS_INDEX')}>RS지표</button>
            <button className = {`sub-btn ${activeSubMenu === 'RS_GRAPH' ? 'active' : ''}`} onClick={()=> setActiveSubMenu('RS_GRAPH')}>RS그래프</button>
          </div>
        )}
      </header>

      <div className="container">
        {activeTab === 'FINANCE' && <GlobalFinance data = {globalFinance}/>}

        {activeTab === 'KOREA' && (
          <div className="market-content">
            {activeSubMenu === 'NEWS' && <KRNews data={krNews} />}
              {activeSubMenu === 'RS_INDEX' && <KRTable/>}
            {activeSubMenu === 'RS_GRAPH' && <KRGraph/>}
          </div>
        )}
        {activeTab === 'USA' && (
          <div className="market-content">
            {activeSubMenu === 'NEWS' && <USNews data={usNews} />}
            {activeSubMenu === 'RS_INDEX' && <USTable/>}
            {activeSubMenu === 'RS_GRAPH' && <USGraph/>}
          </div>
        )}
      </div>
   </div>
    
  );
}



export default App;
