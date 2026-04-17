import React from 'react'
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
    ResponsiveContainer
} from 'recharts'

const CustomTooltip = ({ active, payload }) => {
    if (!active || !payload?.length) return null
    const d = payload[0].payload
    return (
        <div style={{
            background: '#1e2235', border: '1px solid #2a2f4a',
            borderRadius: 8, padding: '10px 14px', fontSize: 12
        }}>
            <div style={{ color: '#ef4444', fontWeight: 600 }}>🌡️ {d.avg_temp_c?.toFixed(1)}°C</div>
            <div style={{ color: '#06b6d4', fontWeight: 600, marginTop: 2 }}>💧 {d.avg_humidity?.toFixed(1)}%</div>
            <div style={{ color: '#f59e0b', fontWeight: 600, marginTop: 2 }}>💡 {d.avg_lux?.toFixed(0)} lux</div>
        </div>
    )
}

export default function EnvironmentPanel({ current, history }) {
    const data = (history || []).map((item, i) => ({
        ...item,
        index: i + 1
    }))

    return (
        <div className="panel">
            <div className="panel-title">
                <span className="icon">🌤️</span>
                Environment
            </div>

            {/* Gauges */}
            <div className="env-gauges">
                <div className="env-gauge">
                    <div className="icon">🌡️</div>
                    <div className="value" style={{ color: '#ef4444' }}>
                        {current?.avg_temp_c?.toFixed(1) ?? '—'}°C
                    </div>
                    <div className="label">Temperature</div>
                </div>
                <div className="env-gauge">
                    <div className="icon">💧</div>
                    <div className="value" style={{ color: '#06b6d4' }}>
                        {(current?.avg_humidity ?? current?.avg_humidity_pct)?.toFixed(0) ?? '—'}%
                    </div>
                    <div className="label">Humidity</div>
                </div>
                <div className="env-gauge">
                    <div className="icon">💡</div>
                    <div className="value" style={{ color: '#f59e0b' }}>
                        {current?.avg_lux?.toFixed(0) ?? '—'}
                    </div>
                    <div className="label">Lux</div>
                </div>
            </div>

            {/* Mini trend chart */}
            {data.length > 0 && (
                <div className="chart-container" style={{ marginTop: 16, height: 140 }}>
                    <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={data}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#2a2f4a" />
                            <XAxis dataKey="index" tick={{ fill: '#6b7280', fontSize: 9 }} />
                            <YAxis tick={{ fill: '#6b7280', fontSize: 9 }} />
                            <Tooltip content={<CustomTooltip />} />
                            <Line type="monotone" dataKey="avg_temp_c" stroke="#ef4444"
                                strokeWidth={2} dot={false} />
                            <Line type="monotone" dataKey="avg_lux" stroke="#f59e0b"
                                strokeWidth={2} dot={false} />
                        </LineChart>
                    </ResponsiveContainer>
                </div>
            )}
        </div>
    )
}
