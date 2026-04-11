import React from 'react'

export default function AlertBanner({ alerts }) {
    if (!alerts || alerts.length === 0) return null

    return (
        <>
            {alerts.map((alert, i) => (
                <div key={i} className="alert-banner">
                    <span className="alert-icon">🚨</span>
                    <span className="alert-text">
                        <strong>{alert.charger_id}</strong> is blocked
                        {alert.duration_min && <> for <strong>{alert.duration_min} min</strong></>}
                        <span> — Vehicle has finished charging but hasn't moved</span>
                    </span>
                </div>
            ))}
        </>
    )
}
