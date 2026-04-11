import React from 'react'

export default function ChargerStatus({ chargers }) {
    if (!chargers || chargers.length === 0) {
        return (
            <div className="panel">
                <div className="panel-title">
                    <span className="icon">🔌</span>
                    EV Charger Status
                </div>
                <div className="empty-state">Waiting for charger data…</div>
            </div>
        )
    }

    return (
        <div className="panel">
            <div className="panel-title">
                <span className="icon">🔌</span>
                EV Charger Status
            </div>
            <div className="charger-grid">
                {chargers.map(ch => {
                    const displayStatus = ch.is_blocked ? 'blocked' : (ch.status || 'available')
                    return (
                        <div key={ch.charger_id} className="charger-card">
                            <div className="name">⚡ {ch.charger_id}</div>
                            <span className={`status-badge ${displayStatus}`}>
                                {displayStatus.replace('_', ' ')}
                            </span>
                            <div className="power" style={{
                                color: ch.power_kw > 0 ? '#3b82f6' : '#6b7280'
                            }}>
                                {(ch.power_kw || 0).toFixed(1)} <span style={{ fontSize: 12, fontWeight: 400 }}>kW</span>
                            </div>
                            {ch.vehicle_id && (
                                <div className="vehicle">🚗 {ch.vehicle_id}</div>
                            )}
                        </div>
                    )
                })}
            </div>
        </div>
    )
}
