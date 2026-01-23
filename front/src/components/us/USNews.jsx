import React, {useState} from 'react';

const USNews = ({data}) => {
    const stockKeys = Object.keys(data).filter(key => key !== 'update_time')
        .sort((a, b) => {
            const nameA = a.split('_')[1].toUpperCase();
            const nameB = b.split('_')[1].toUpperCase();
            return nameA.localeCompare(nameB);
        });

    const[activeTab, setActiveTab] = useState(stockKeys[0] || '');

    if (stockKeys.length === 0) return <div className = "news-card">미국 뉴스를 불러오는 중...</div>

    return (
        <div className = "news-card glass-card">
            <h3 className="section-title">주요 종목 뉴스(USA)</h3>

            <div className="tabs">
                {stockKeys.map((key) => (
                    <button
                    key={key}
                    className={`tab-btn ${activeTab === key ? 'active' : ''}`}
                    onClick ={() => setActiveTab(key)}
                    >{key.split('_')[1]}</button>
                ))}
            </div>
        <div className = "news_list">
            {data[activeTab]?.articles?.map((art, idx) => (
                <a key={idx} href={art.link} target="_blank" rel="noreferrer" className="news-item" >
                    <p className="news-title">{art.title}</p>
                    <div className="news-meta">
                        <span>{art.publisher}</span> · <span>{art.time}</span>
                    </div>
                </a>
            ))}
        </div>
        </div>
    );

};

export default USNews;