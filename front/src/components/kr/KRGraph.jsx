import React, { useState, useEffect } from 'react';
import { db } from '../../firebaseConfig';
import { doc, onSnapshot } from 'firebase/firestore';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, LabelList } from 'recharts';

const KRGraphTrend = () => {
  const [chartData, setChartData] = useState([]);
  const [stocks, setStocks] = useState([]);

  useEffect(() => {
    const unsub = onSnapshot(doc(db, 'rs_data', 'latest'), (docSnapshot) => {
      if (docSnapshot.exists()) {
        const rankings = docSnapshot.data().rankings || [];
        const filtered = rankings
          .filter(item => item.rs_avg >= 75)
          .sort((a, b) => b.rs_avg - a.rs_avg)
          .slice(0, 12);

        const periods = [
          { name: '180D', key: 'rs_180' }, { name: '90D', key: 'rs_90' },
          { name: '60D', key: 'rs_60' }, { name: '30D', key: 'rs_30' },
          { name: '10D', key: 'rs_10' },
        ];

        const formatted = periods.map(p => ({
          name: p.name,
          ...filtered.reduce((acc, s) => ({ ...acc, [s.name]: s[p.key] }), {})
        }));

        setChartData(formatted);
        setStocks(filtered);
      }
    });
    return () => unsub();
  }, []);

  const autoColors = stocks.map((_, i) => `hsl(${(i * 360) / (stocks.length || 1)}, 70%, 45%)`);

  const malgunStyle = {
    fill: '#000',
    color: '#000',
    fontSize: '14px',
    fontWeight: '700',
    fontFamily: '"Malgun Gothic", "맑은 고딕", sans-serif'
  };

  return (
    <div style={{ width: '90%', margin: '0 auto', backgroundColor: '#000', paddingBottom: '60px' }}>
      <div style={{ backgroundColor: '#ffffff', padding: '15px' }}>
        <header style={{ marginBottom: '20px', borderLeft: '8px solid #000', paddingLeft: '12px' }}>
          <h2 style={{ margin: 0, fontSize: '20px', fontWeight: '900', color: '#000', fontFamily: '"Malgun Gothic", "맑은 고딕"' }}>
            KOSPI RS MOMENTUM (KR)
          </h2>
        </header>

        <div style={{ display: 'flex', width: '100%', height: '580px' }}>
          <div style={{ flex: 1 }}>
            <ResponsiveContainer width="100%" height="100%">
              {/* 💎 right 마진을 120으로 늘려 그래프 끝 글자 잘림 방지 */}
              <LineChart data={chartData} margin={{ top: 10, right: 120, left: 10, bottom: 10 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#ccc" />
                <XAxis dataKey="name" stroke="#000" tick={{ ...malgunStyle }} />
                
                <YAxis 
                  domain={[30, 100]} 
                  ticks={[30, 40, 50, 60, 70, 80, 90, 100]} 
                  stroke="#000" 
                  tick={{ ...malgunStyle }} 
                />
                
                <Tooltip contentStyle={{ ...malgunStyle, border: '2px solid #000' }} isAnimationActive={false} />
                
                <ReferenceLine 
                  y={75} 
                  stroke="#ff0000" 
                  strokeWidth={3} 
                  strokeDasharray="8 4" 
                  label={{ 
                    value: '75', 
                    position: 'left', 
                    dx: -2, // 💎 Y축 선에 딱 붙도록 수정 완료
                    dy: 0,
                    fill: '#ff0000', 
                    fontSize: 16, 
                    fontWeight: '900',
                    fontFamily: '맑은 고딕'
                  }} 
                />

                {stocks.map((s, idx) => (
                  <Line key={s.name} type="monotone" dataKey={s.name} stroke={autoColors[idx]} strokeWidth={2.5} dot={{ r: 3 }} isAnimationActive={false}>
                    <LabelList 
                      dataKey={s.name} 
                      content={(props) => (
                        props.index === chartData.length - 1 
                        ? <text x={props.x + 8} y={props.y + 4} fill={autoColors[idx]} fontSize="13px" fontWeight="900" fontFamily='"Malgun Gothic", "맑은 고딕"'>{s.name}</text> 
                        : null
                      )} 
                    />
                  </Line>
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* 💎 범례 영역: marginLeft 조절로 그래프와의 간격 유지 */}
          <div style={{ width: '150px', marginLeft: '30px', padding: '5px', overflowY: 'auto' }}>
            <div style={{ ...malgunStyle, fontSize: '15px', marginBottom: '15px', textDecoration: 'underline' }}>RANKING (RS)</div>
            <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
              {stocks.map((s, idx) => (
                <li key={s.name} style={{ marginBottom: '8px', ...malgunStyle, fontSize: '13.5px', color: autoColors[idx], whiteSpace: 'nowrap' }}>
                  {s.name} ({s.rs_avg})
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default KRGraphTrend;