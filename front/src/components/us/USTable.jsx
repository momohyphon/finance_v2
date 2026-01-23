import React, { useState, useEffect } from 'react';
import { db } from '../../firebaseConfig';
import { doc, onSnapshot } from 'firebase/firestore'; 
import { Treemap, ResponsiveContainer, Tooltip } from 'recharts';

const USTable = () => {
    const [data, setData] = useState(null);

    useEffect(() => {
        // 파이썬이 쏜 미국 데이터 'us_latest' 조준
        const unsub = onSnapshot(doc(db, 'rs_data', 'us_latest'), (docSnapshot) => {
            if (docSnapshot.exists()) {
                setData(docSnapshot.data());
            }
        });
        return () => unsub();
    }, []);

    if (!data || !data.rankings) return <div style={{ color: '#fff', padding: '20px', textAlign: 'center' }}>데이터 로딩 중...</div>;

    // 히트맵용 데이터 가공
    const treemapData = data.rankings.map(item => ({
        name: item.code,
        size: item.rs_avg || 0,
        rs_avg: item.rs_avg
    }));

    // 히트맵 사각형 디자인 (한국과 동일)
    const CustomizedContent = (props) => {
        const { x, y, width, height, name, rs_avg } = props;
        const bgColor = rs_avg >= 70 ? '#2ecc71' : '#ff4d94';
        return (
            <g>
                <rect x={x} y={y} width={width} height={height} style={{ fill: bgColor, stroke: '#000', strokeWidth: 1 }} />
                {width > 35 && height > 25 && (
                    <>
                        <text x={x + width / 2} y={y + height / 2 - 5} textAnchor="middle" fill="#fff" fontSize={14} fontWeight="900">{name}</text>
                        <text x={x + width / 2} y={y + height / 2 + 12} textAnchor="middle" fill="#fff" fontSize={12} fontWeight="700">{rs_avg}</text>
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
                
                {/* [1. 히트맵 영역] - 여기서 히트맵이 나옵니다 */}
                <div style={{ width: '100%', height: '550px', marginBottom: '40px' }}>
                    <ResponsiveContainer width="100%" height="100%">
                        <Treemap data={treemapData} dataKey="size" aspectRatio={1.8} content={<CustomizedContent />}>
                            <Tooltip active={false} />
                        </Treemap>
                    </ResponsiveContainer>
                </div>

                {/* [2. 리스트 영역] - 여기서 표가 나집니다 */}
                <div style={{ borderTop: '2px solid #ff6b00', paddingLeft: '10px' }}>
                    <div style={{ 
                        display: 'flex', padding: '15px 0', color: '#ff6b00', 
                        fontWeight: '900', fontSize: '14px', borderBottom: '2px solid #ff6b00',
                        textAlign: 'center'
                    }}>
                        <span style={{ width: '40px' }}>RK</span>
                        <span style={{ width: '85px' }}>TICKER</span>
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
                            <span style={{ width: '55px', fontWeight: '900', color: '#ff6b00' }}>{s.rs_avg}</span>
                            <span style={{ width: '75px', textAlign: 'right' }}>{s.disparity}%</span>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default USTable;