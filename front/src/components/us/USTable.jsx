import React, { useState, useEffect } from 'react';
import { db } from '../../firebaseConfig';
import { doc, onSnapshot } from 'firebase/firestore'; 
import { Treemap, ResponsiveContainer, Tooltip } from 'recharts';

const USTable = () => {
    const [data, setData] = useState(null);

    useEffect(() => {
        const unsub = onSnapshot(doc(db, 'rs_data', 'us_latest'), (docSnapshot) => {
            if (docSnapshot.exists()) {
                setData(docSnapshot.data());
            }
        });
        return () => unsub();
    }, []);

    if (!data || !data.rankings) return <div style={{ color: '#fff', padding: '20px', textAlign: 'center' }}>데이터 로딩 중...</div>;

    const treemapData = data.rankings.map(item => ({
        name: item.name, // 회사 이름 표시
        size: item.rs_avg || 0,
        rs_avg: item.rs_avg
    }));

    const CustomizedContent = (props) => {
        const { x, y, width, height, name, rs_avg } = props;
        
        // [수정] 히트맵은 오빠 말대로 75점 이상이면 초록색!
        const bgColor = rs_avg >= 75 ? '#2ecc71' : '#ff4d94';
        
        const nameFontSize = Math.min(width / (name.length * 0.65), height / 2.5, 14);
        const scoreFontSize = Math.min(nameFontSize * 0.8, 11);

        return (
            <g>
                <rect 
                    x={x} y={y} width={width} height={height} 
                    style={{ fill: bgColor, stroke: '#000', strokeWidth: 1 }} 
                />
                {width > 2 && height > 2 && (
                    <>
                        <text 
                            x={x + width / 2} 
                            y={y + height / 2 - (scoreFontSize / 2)} 
                            textAnchor="middle" 
                            fill="#fff" 
                            fontSize={nameFontSize} 
                            fontWeight="900"
                            style={{ pointerEvents: 'none' }}
                        >
                            {name}
                        </text>
                        <text 
                            x={x + width / 2} 
                            y={y + height / 2 + (scoreFontSize)} 
                            textAnchor="middle" 
                            fill="#fff" 
                            fontSize={scoreFontSize} 
                            fontWeight="700"
                            style={{ opacity: 0.9, pointerEvents: 'none' }}
                        >
                            {rs_avg}
                        </text>
                    </>
                )}
            </g>
        );
    };

    return (
        <div style={{ 
            backgroundColor: '#000', color: '#fff', padding: '20px 0', 
            display: 'flex', flexDirection: 'column', alignItems: 'center',
            minHeight: '100vh'
        }}>
            <div style={{ width: '100%', maxWidth: '1020px' }}>
                <h3 style={{ color: '#ff6b00', marginBottom: '20px', paddingLeft: '10px' }}>USA RS HEATMAP & ANALYSIS</h3>
                
                <div style={{ width: '100%', height: '550px', marginBottom: '40px' }}>
                    <ResponsiveContainer width="100%" height="100%">
                        <Treemap data={treemapData} dataKey="size" aspectRatio={1.8} content={<CustomizedContent />}>
                            <Tooltip active={false} />
                        </Treemap>
                    </ResponsiveContainer>
                </div>

                <div style={{ borderTop: '2px solid #ff6b00', paddingLeft: '10px' }}>
                    {/* 리스트 헤더 생략 (기존과 동일) */}
                    {data.rankings.map((s, idx) => (
                        <div key={idx} style={{ display: 'flex', padding: '12px 0', borderBottom: '1px solid #333', fontSize: '15px', color: '#fff', textAlign: 'center', alignItems: 'center' }}>
                            <span style={{ width: '40px' }}>{idx + 1}</span>
                            <span style={{ width: '85px' }}>{s.code}</span>
                            <span style={{ width: '180px', textAlign: 'left', fontWeight: 'bold' }}>{s.name}</span>
                            <span style={{ width: '55px' }}>{s.rs_180}</span>
                            <span style={{ width: '55px' }}>{s.rs_90}</span>
                            <span style={{ width: '55px' }}>{s.rs_60}</span>
                            <span style={{ width: '55px' }}>{s.rs_30}</span>
                            <span style={{ width: '55px' }}>{s.rs_10}</span>
                            {/* 리스트 점수 색상도 75점 기준으로 변경 */}
                            <span style={{ width: '55px', fontWeight: '900', color: s.rs_avg >= 75 ? '#2ecc71' : '#ff6b00' }}>
                                {s.rs_avg}
                            </span>
                            <span style={{ width: '75px', textAlign: 'right' }}>{s.disparity}%</span>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default USTable;