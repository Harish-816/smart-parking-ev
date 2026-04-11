import React from 'react'
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
    ResponsiveContainer, Area, AreaChart
} from 'recharts'

const CustomTooltip = ({ active, payload }) => {
    if (!active || !payload?.length) return null
    const d = payload[0].payload
    return (
        <div style={{
            background: '#1e2235', border: '1px solid #2a2f4a',
            borderRadius: 8, padding: '10px 14px', fontSize: 12
        }}>
            <div style={{ color: '#3b82f6', fontWeight: 600 }}>
                {d.occ_pct?.toFixed(1)}% occupied
            </div>
            <div style={{ color: '#9ca3b8', marginTop: 4 }}>
                {d.occupied}/{d.total_spots} spots
            </div>
        </div>
    )
}

export default function OccupancyTrend({ history }) {
    const data = (history || []).map((item, i) => ({
        ...item,
        index: i + 1,
        occ_pct: item.occ_pct || 0
    }))

    return (
        <div className="panel">
            <div className="panel-title">
                <span className="icon">📈</span>
                Occupancy Trend
            </div>
            {data.length > 0 ? (
                <div className="chart-container">
                    <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={data}>
                            <defs>
                                <linearGradient id="occGradient" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="#2a2f4a" />
                            <XAxis dataKey="index" tick={{ fill: '#6b7280', fontSize: 10 }} />
                            <YAxis
                                domain={[0, 100]}
                                tick={{ fill: '#6b7280', fontSize: 10 }}
                                tickFormatter={v => `${v}%`}
                            />
                            <Tooltip content={<CustomTooltip />} />
                            <Area
                                type="monotone"
                                dataKey="occ_pct"
                                stroke="#3b82f6"
                                strokeWidth={2}
                                fill="url(#occGradient)"
                                dot={false}
                                activeDot={{ r: 5, fill: '#3b82f6', stroke: '#1e2235', strokeWidth: 2 }}
                            />
                        </AreaChart>
                    </ResponsiveContainer>
                </div>
            ) : (
                <div className="empty-state">Waiting for occupancy history…</div>
            )}
        </div>
    )
}
