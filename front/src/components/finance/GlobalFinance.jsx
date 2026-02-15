import React from 'react';

const GlobalFinance = ({ data }) => {
    if (!data || !data.items) return null;
    const { bonds, items, update_time } = data;

    // ★ CSS 애니메이션 스타일 (깜박이 효과)
    const blinkStyle = `
        @keyframes blink-green {
            0% { opacity: 1; }
            50% { opacity: 0.3; }
            100% { opacity: 1; }
        }
    `;

    const orangeColStyle = { 
        width: '280px', 
        borderLeft: '3px solid #ff6b00', 
        paddingLeft: '15px', 
        marginRight: '20px' 
    };

    const renderVal = (val) => {
        const num = parseFloat(val);
        const isPlus = num >= 0;
        return (
            <span style={{ 
                fontSize: '13px', 
                color: isPlus ? '#ff4d4d' : '#007aff', 
                fontWeight: '800',
                width: '60px',
                textAlign: 'right', 
                display: 'inline-block',
                marginLeft: '10px'
            }}>
                {isPlus ? `+${num.toFixed(2)}` : num.toFixed(2)}%
            </span>
        );
    };

    // ★ 지표 이름 렌더링 함수 (2% 로직 포함)
    const renderName = (name, change) => {
        const num = Math.abs(parseFloat(change));
        const isHighVolatility = num >= 2;

        return (
            <span style={{ 
                fontSize: '12px', 
                width: '100px', 
                whiteSpace: 'nowrap', 
                overflow: 'hidden', 
                textOverflow: 'ellipsis',
                // 2% 넘으면 밝은 초록색(#00ff41), 아니면 기존 회색(#aaa)
                color: isHighVolatility ? '#00ff41' : '#aaa',
                fontWeight: isHighVolatility ? '900' : '400',
                // 2% 넘으면 깜박이 애니메이션 작동
                animation: isHighVolatility ? 'blink-green 1s infinite' : 'none'
            }}>
                {name}
            </span>
        );
    };

    return (
        <div style={{ 
            backgroundColor: '#000', 
            width: '100%', 
            display: 'flex', 
            flexDirection: 'column', 
            alignItems: 'center', 
            padding: '40px 0', 
            color: '#fff' 
        }}>
            {/* 애니메이션 정의 삽입 */}
            <style>{blinkStyle}</style>
            
            <div style={{ display: 'flex', justifyContent: 'center' }}>
                
                {/* 1열: TREASURY */}
                <div style={orangeColStyle}>
                    <div style={{ fontSize: '14px', color: '#ff6b00', fontWeight: '900', marginBottom: '15px' }}>TREASURY</div>
                    {["5Y", "10Y", "30Y"].map((key) => (
                        <div key={key} 
                             onClick={() => bonds?.[`${key}_link`] && window.open(bonds[`${key}_link`], "_blank")}
                             style={{ display: 'flex', alignItems: 'center', padding: '8px 0', borderBottom: '1px solid #111', cursor: 'pointer' }}>
                            {renderName(`${key} BOND`, bonds?.[`${key}_chg`] || 0)}
                            <div style={{ flex: 1, display: 'flex', justifyContent: 'flex-end', alignItems: 'center' }}>
                                <span style={{ fontSize: '14px', fontWeight: '700' }}>{bonds?.[`${key}_val`]}%</span>
                                {renderVal(bonds?.[`${key}_chg`] || 0)}
                            </div>
                        </div>
                    ))}
                </div>

                {/* 2열: MARKET I */}
                <div style={orangeColStyle}>
                    <div style={{ fontSize: '14px', color: '#ff6b00', fontWeight: '900', marginBottom: '15px' }}>MARKET I</div>
                    {items.slice(0, 7).map((item, idx) => (
                        <div key={idx} 
                             onClick={() => item.Link && window.open(item.Link, "_blank")}
                             style={{ display: 'flex', alignItems: 'center', padding: '8px 0', borderBottom: '1px solid #111', cursor: 'pointer' }}>
                            {renderName(item.name, item.change)}
                            <div style={{ flex: 1, display: 'flex', justifyContent: 'flex-end', alignItems: 'center' }}>
                                <span style={{ fontSize: '14px', fontWeight: '700' }}>{item.price}</span>
                                {renderVal(item.change)}
                            </div>
                        </div>
                    ))}
                </div>

                {/* 3열: MARKET II */}
                <div style={orangeColStyle}>
                    <div style={{ fontSize: '14px', color: '#ff6b00', fontWeight: '900', marginBottom: '15px' }}>MARKET II</div>
                    {items.slice(7).map((item, idx) => (
                        <div key={idx} 
                             onClick={() => item.Link && window.open(item.Link, "_blank")}
                             style={{ display: 'flex', alignItems: 'center', padding: '8px 0', borderBottom: '1px solid #111', cursor: 'pointer' }}>
                            {renderName(item.name, item.change)}
                            <div style={{ flex: 1, display: 'flex', justifyContent: 'flex-end', alignItems: 'center' }}>
                                <span style={{ fontSize: '14px', fontWeight: '700' }}>{item.price}</span>
                                {renderVal(item.change)}
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            <div style={{ width: '900px', fontSize: '10px', color: '#333', textAlign: 'right', marginTop: '15px' }}>
                {update_time}
            </div>
        </div>
    );
};

export default GlobalFinance;