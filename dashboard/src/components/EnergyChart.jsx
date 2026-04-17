import React from 'react'
import {
    BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
    ResponsiveContainer, Cell
} from 'recharts'

const COLORS = ['#3b82f6', '#06b6d4', '#8b5cf6', '#ec4899', '#10b981', '#f59e0b', '#ef4444', '#6366f1']

const CustomTooltip = ({ active, payload, label, unit = 'kWh' }) => {
    if (!active || !payload?.length) return null
    return (
        <div style={{
            background: '#1e2235', border: '1px solid #2a2f4a',
            borderRadius: 8, padding: '10px 14px', fontSize: 12
        }}>
            <div style={{ color: '#9ca3b8', marginBottom: 4 }}>{label}</div>
            <div style={{ color: '#e8eaf0', fontWeight: 600 }}>
                {payload[0].value.toFixed(2)} {unit}
            </div>
        </div>
    )
}

export default function EnergyChart({ history }) {
    // Get latest per_charger data from most recent record
    const latest = history && history.length > 0 ? history[history.length - 1] : null
    const perCharger = latest?.per_charger || {}

    const chartData = Object.entries(perCharger)
        .filter(([, v]) => v > 0)  // only show chargers with non-zero value
        .map(([id, val]) => ({
            name: id,
            kwh: val
        }))

    // Detect if values look like power (kW) or energy (kWh)
    const maxVal = Math.max(...chartData.map(d => d.kwh), 0)
    const isPower = maxVal > 5  // energy_kwh per interval is tiny (<1); power_kw is >5
    const unit = isPower ? 'kW' : 'kWh'
    const title = isPower ? 'Live Power Draw (kW)' : 'Energy per Charger (kWh)'

    if (chartData.length === 0) {
        // Fallback: show energy trend over time
        const trendData = (history || []).map((item, i) => ({
            name: `T${i + 1}`,
            kwh: item.total_kwh || 0
        }))

        return (
            <div className="panel">
                <div className="panel-title">
                    <span className="icon">📊</span>
                    Energy Consumption Trend
                </div>
                {trendData.length > 0 ? (
                    <div className="chart-container">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={trendData}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#2a2f4a" />
                                <XAxis dataKey="name" tick={{ fill: '#6b7280', fontSize: 10 }} />
                                <YAxis tick={{ fill: '#6b7280', fontSize: 10 }} />
                                <Tooltip content={<CustomTooltip unit="kWh" />} />
                                <Bar dataKey="kwh" radius={[4, 4, 0, 0]}>
                                    {trendData.map((_, i) => (
                                        <Cell key={i} fill={COLORS[i % COLORS.length]} />
                                    ))}
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                ) : (
                    <div className="empty-state">Waiting for energy data…</div>
                )}
            </div>
        )
    }

    return (
        <div className="panel">
            <div className="panel-title">
                <span className="icon">📊</span>
                {title}
            </div>
            <div className="chart-container">
                <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={chartData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#2a2f4a" />
                        <XAxis dataKey="name" tick={{ fill: '#6b7280', fontSize: 10 }} />
                        <YAxis tick={{ fill: '#6b7280', fontSize: 10 }} />
                        <Tooltip content={<CustomTooltip unit={unit} />} />
                        <Bar dataKey="kwh" radius={[4, 4, 0, 0]}>
                            {chartData.map((_, i) => (
                                <Cell key={i} fill={COLORS[i % COLORS.length]} />
                            ))}
                        </Bar>
                    </BarChart>
                </ResponsiveContainer>
            </div>
        </div>
    )
}
