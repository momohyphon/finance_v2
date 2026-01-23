import React, { useState, useEffect } from 'react';
import { db } from '../../firebaseConfig';
import { doc, onSnapshot } from 'firebase/firestore';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, LabelList } from 'recharts';

const USGraphTrend = () => {
  const [chartData, setChartData] = useState([]);
  const [stocks, setStocks] = useState([]);

  useEffect(() => {
    // 💎 미국 데이터 조준: us_latest
    const unsub = onSnapshot(doc(db, 'rs_data', 'us_latest'), (docSnapshot) => {
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
          ...filtered.reduce((acc, s) => ({ ...acc, [s.code]: s[p.key] }), {})
        }));

        setChartData(formatted);
        setStocks(filtered);
      }
    });
    return () => unsub();
  }, []);

  const autoColors = stocks.map((_, i) => `hsl(${(i * 360) / (stocks.length || 1)}, 70%, 45%)`);

  // 💎 영문 세련된 폰트 + 맑은 고딕 조합
  const malgunStyle = {
    fill: '#000',
    color: '#000',
    fontSize: '14px',
    fontWeight: '700',
    fontFamily: '"Segoe UI", Roboto, "Malgun Gothic", "맑은 고딕", sans-serif'
  };

  return (
    <div style={{ width: '90%', margin: '0 auto', backgroundColor: '#000', paddingBottom: '60px' }}>
      <div style={{ backgroundColor: '#ffffff', padding: '15px' }}>
        <header style={{ marginBottom: '20px', borderLeft: '8px solid #000', paddingLeft: '12px' }}>
          <h2 style={{ margin: 0, fontSize: '20px', fontWeight: '900', color: '#000', fontFamily: malgunStyle.fontFamily }}>
            S&P 500 RS MOMENTUM (US)
          </h2>
        </header>

        <div style={{ display: 'flex', width: '100%', height: '580px' }}>
          <div style={{ flex: 1 }}>
            <ResponsiveContainer width="100%" height="100%">
              {/* 💎 right: 120으로 Ticker 글자 잘림 완벽 방지 */}
              <LineChart data={chartData} margin={{ top: 10, right: 120, left: 10, bottom: 10 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#ccc" />
                <XAxis dataKey="name" stroke="#000" tick={{ ...malgunStyle }} />
                <YAxis domain={[30, 100]} ticks={[30, 40, 50, 60, 70, 80, 90, 100]} stroke="#000" tick={{ ...malgunStyle }} />
                <Tooltip contentStyle={{ ...malgunStyle, border: '2px solid #000' }} isAnimationActive={false} />
                
                {/* 💎 75 라벨: dx: -2로 Y축에 딱 붙임 */}
                <ReferenceLine 
                  y={75} 
                  stroke="#ff0000" 
                  strokeWidth={3} 
                  strokeDasharray="8 4" 
                  label={{ 
                    value: '75', position: 'left', dx: -2, fill: '#ff0000', 
                    fontSize: 16, fontWeight: '900', fontFamily: '맑은 고딕'
                  }} 
                />

                {stocks.map((s, idx) => (
                  <Line key={s.code} type="monotone" dataKey={s.code} stroke={autoColors[idx]} strokeWidth={2.5} dot={{ r: 3 }} isAnimationActive={false}>
                    <LabelList 
                      dataKey={s.code} 
                      content={(props) => (
                        props.index === chartData.length - 1 
                        ? <text x={props.x + 8} y={props.y + 4} fill={autoColors[idx]} fontSize="13px" fontWeight="900" fontFamily={malgunStyle.fontFamily}>{s.code}</text> 
                        : null
                      )} 
                    />
                  </Line>
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* 💎 범례: 세로선 제거 및 간격 최적화 */}
          <div style={{ width: '150px', marginLeft: '30px', padding: '5px', overflowY: 'auto' }}>
            <div style={{ ...malgunStyle, fontSize: '15px', marginBottom: '15px', textDecoration: 'underline' }}>RANKING (RS)</div>
            <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
              {stocks.map((s, idx) => (
                <li key={s.code} style={{ marginBottom: '8px', ...malgunStyle, fontSize: '13.5px', color: autoColors[idx], whiteSpace: 'nowrap' }}>
                  {s.code} ({s.rs_avg})
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default USGraphTrend;