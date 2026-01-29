import React, { useState, useEffect } from 'react';
import { db } from '../../firebaseConfig';
import { doc, onSnapshot } from 'firebase/firestore'; 
import { Treemap, ResponsiveContainer, Tooltip } from 'recharts';

const KRTable = () => {
    const [data, setData] = useState(null);

    useEffect(() => {
        // [2026-01-28] 파이어베이스 경로: rs_data/latest
        const unsub = onSnapshot(doc(db, 'rs_data', 'latest'), (docSnapshot) => {
            if (docSnapshot.exists()) setData(docSnapshot.data());
        });
        return () => unsub();
    }, []);

    if (!data || !data.rankings) return <div style={{ color: '#fff', padding: '20px', textAlign: 'center' }}>데이터 로딩 중...</div>;

    const treemapData = data.rankings.map(item => ({
        name: item.name,
        size: item.rs_avg || 0,
        rs_avg: item.rs_avg
    }));

    // ★ 히트맵 내부 글자 제어 로직 ★
    const CustomizedContent = (props) => {
        const { x, y, width, height, name, rs_avg } = props;
        const bgColor = rs_avg >= 70 ? '#2ecc71' : '#ff4d94';

        // 1. 큰 박스는 14px 고정, 작은 박스는 너비/높이에 맞춰 자동 축소
        const nameFontSize = Math.min(width / (name.length * 0.95), height / 2.5, 14);
        const scoreFontSize = Math.min(nameFontSize * 0.85, 12);

        return (
            <g>
                <rect 
                    x={x} y={y} width={width} height={height} 
                    style={{ fill: bgColor, stroke: '#000', strokeWidth: 1 }} 
                />
                {/* 박스가 너무 작아서 글자가 아예 안 보이는 수준(10px 이하)이 아니면 무조건 렌더링 */}
                {width > 12 && height > 12 && (
                    <>
                        <text 
                            x={x + width / 2} 
                            y={y + height / 2 - (scoreFontSize / 3)} 
                            textAnchor="middle" 
                            fill="#fff" 
                            fontSize={nameFontSize} 
                            fontWeight="900"
                            style={{ pointerEvents: 'none', dominantBaseline: 'central' }}
                        >
                            {name}
                        </text>
                        <text 
                            x={x + width / 2} 
                            y={y + height / 2 + (nameFontSize / 1.1)} 
                            textAnchor="middle" 
                            fill="#fff" 
                            fontSize={scoreFontSize} 
                            fontWeight="700"
                            style={{ opacity: 0.9, pointerEvents: 'none', dominantBaseline: 'central' }}
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
                
                <h3 style={{ color: '#ff6b00', marginBottom: '20px', paddingLeft: '10px' }}>KOREA RS HEATMAP & ANALYSIS</h3>
                
                <div style={{ width: '100%', height: '550px', marginBottom: '40px' }}>
                    <ResponsiveContainer width="100%" height="100%">
                        <Treemap data={treemapData} dataKey="size" aspectRatio={1.8} content={<CustomizedContent />}>
                            <Tooltip active={false} />
                        </Treemap>
                    </ResponsiveContainer>
                </div>

                <div style={{ borderTop: '2px solid #ff6b00', paddingLeft: '10px' }}>
                    <div style={{ 
                        display: 'flex', padding: '15px 0', color: '#ff6b00', 
                        fontWeight: '900', fontSize: '14px', borderBottom: '2px solid #ff6b00',
                        textAlign: 'center'
                    }}>
                        <span style={{ width: '40px' }}>RK</span>
                        <span style={{ width: '85px' }}>CODE</span>
                        <span style={{ width: '180px', textAlign: 'left' }}>NAME</span>
                        <span style={{ width: '55px' }}>180D</span>
                        <span style={{ width: '55px' }}>90D</span>
                        <span style={{ width: '55px' }}>60D</span>
                        <span style={{ width: '55px' }}>30D</span>
                        <span style={{ width: '55px' }}>10D</span>
                        <span style={{ width: '55px' }}>AVG</span>
                        <span style={{ width: '75px', textAlign: 'right' }}>DISP</span>
                    </div>

                    {data.rankings.map((s, idx) => (
                        <div key={idx} style={{ 
                            display: 'flex', padding: '12px 0', borderBottom: '1px solid #333', 
                            fontSize: '15px', color: '#fff', textAlign: 'center',
                            alignItems: 'center'
                        }}>
                            <span style={{ width: '40px' }}>{idx + 1}</span>
                            <span style={{ width: '85px' }}>{s.code}</span>
                            <span style={{ width: '180px', textAlign: 'left', fontWeight: 'bold' }}>{s.name}</span>
                            <span style={{ width: '55px' }}>{s.rs_180}</span>
                            <span style={{ width: '55px' }}>{s.rs_90}</span>
                            <span style={{ width: '55px' }}>{s.rs_60}</span>
                            <span style={{ width: '55px' }}>{s.rs_30}</span>
                            <span style={{ width: '55px' }}>{s.rs_10}</span>
                            <span style={{ width: '55px', fontWeight: '900', color: s.rs_avg >= 75 ?  '#2ecc71' : '#ff6b00' }}>{s.rs_avg}</span>
                            <span style={{ width: '75px', textAlign: 'right' }}>{s.disparity}%</span>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default KRTable;