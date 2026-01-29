import React from 'react';

const GlobalFinance = ({ data }) => {
    if (!data || !data.items) return null;
    const { bonds, items, update_time } = data;

    // 기둥 상자 폭 고정 (오빠가 괜찮다고 한 그 사이즈)
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

    return (
        /* ★ 화면 전체 중앙 정렬을 위한 컨테이너 ★ */
        <div style={{ 
            backgroundColor: '#000', 
            width: '100%', 
            display: 'flex', 
            flexDirection: 'column', 
            alignItems: 'center', // 가로축 중앙 정렬
            padding: '40px 0', 
            color: '#fff' 
        }}>
            
            {/* 실제 지표 기둥들이 들어가는 영역 */}
            <div style={{ display: 'flex', justifyContent: 'center' }}>
                
                {/* 1열: TREASURY */}
                <div style={orangeColStyle}>
                    <div style={{ fontSize: '14px', color: '#ff6b00', fontWeight: '900', marginBottom: '15px' }}>TREASURY</div>
                    {["2Y", "10Y", "30Y"].map((key) => (
                        <div key={key} 
                             onClick={() => bonds?.[`${key}_link`] && window.open(bonds[`${key}_link`], "_blank")}
                             style={{ display: 'flex', alignItems: 'center', padding: '8px 0', borderBottom: '1px solid #111', cursor: 'pointer' }}>
                            <span style={{ fontSize: '12px', color: '#aaa', width: '80px' }}>{key} BOND</span>
                            <div style={{ flex: 1, display: 'flex', justifyContent: 'flex-end', alignItems: 'center' }}>
                                <span style={{ fontSize: '14px', fontWeight: '700' }}>{bonds?.[`${key}_val`]}%</span>
                                {renderVal(bonds?.[`${key}_chg` || 0])}
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
                            <span style={{ fontSize: '12px', color: '#aaa', width: '100px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{item.name}</span>
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
                            <span style={{ fontSize: '12px', color: '#aaa', width: '100px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{item.name}</span>
                            <div style={{ flex: 1, display: 'flex', justifyContent: 'flex-end', alignItems: 'center' }}>
                                <span style={{ fontSize: '14px', fontWeight: '700' }}>{item.price}</span>
                                {renderVal(item.change)}
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* 시간 정보도 정렬된 상자에 맞춰 배치 */}
            <div style={{ width: '900px', fontSize: '10px', color: '#333', textAlign: 'right', marginTop: '15px' }}>
                {update_time}
            </div>
        </div>
    );
};

export default GlobalFinance;