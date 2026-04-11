import { useState, useEffect, useCallback } from 'react'
import axios from 'axios'
import ParkingGrid from './components/ParkingGrid'
import ChargerStatus from './components/ChargerStatus'
import EnergyChart from './components/EnergyChart'
import OccupancyTrend from './components/OccupancyTrend'
import EnvironmentPanel from './components/EnvironmentPanel'
import AlertBanner from './components/AlertBanner'
import './index.css'

const API = 'http://localhost:5000/api'

export default function App() {
  const [data, setData] = useState(null)
  const [occHistory, setOccHistory] = useState([])
  const [energyHistory, setEnergyHistory] = useState([])
  const [envHistory, setEnvHistory] = useState([])
  const [loading, setLoading] = useState(true)
  const [lastUpdate, setLastUpdate] = useState(null)

  const fetchData = useCallback(async () => {
    try {
      const [summary, occ, energy, env] = await Promise.all([
        axios.get(`${API}/dashboard/summary`),
        axios.get(`${API}/parking/occupancy-history`),
        axios.get(`${API}/chargers/energy`),
        axios.get(`${API}/environment/history`),
      ])
      setData(summary.data)
      setOccHistory(occ.data.reverse().slice(-30))
      setEnergyHistory(energy.data.reverse().slice(-30))
      setEnvHistory(env.data.reverse().slice(-30))
      setLastUpdate(new Date())
      setLoading(false)
    } catch (err) {
      console.error('API fetch failed:', err)
    }
  }, [])

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 5000)
    return () => clearInterval(interval)
  }, [fetchData])

  if (loading) {
    return (
      <div className="loading">
        <div className="loading-spinner" />
        Connecting to Smart Parking API …
      </div>
    )
  }

  const p = data?.parking || {}
  const chargers = data?.chargers || []
  const energy = data?.energy || {}
  const env = data?.environment || {}
  const alerts = data?.blocked_alerts || []
  const activeChargers = chargers.filter(c => c.status === 'in_use').length
  const blockedChargers = chargers.filter(c => c.is_blocked).length

  return (
    <>
      {/* ─── Header ─────────────────────────────────────────── */}
      <header className="header">
        <div className="header-left">
          <div className="header-icon">🅿️</div>
          <h1>Smart Parking <span>+ EV Charger</span></h1>
        </div>
        <div className="header-right">
          <div className="live-badge">
            <div className="live-dot" />
            LIVE
          </div>
          {lastUpdate && (
            <span className="last-update">
              Updated {lastUpdate.toLocaleTimeString()}
            </span>
          )}
        </div>
      </header>

      {/* ─── Dashboard ──────────────────────────────────────── */}
      <main className="dashboard">

        {/* Alerts */}
        {alerts.length > 0 && <AlertBanner alerts={alerts} />}

        {/* Stat Cards */}
        <div className="stats-row">
          <div className="stat-card blue">
            <div className="stat-icon blue">🅿️</div>
            <div className="stat-info">
              <div className="stat-label">Available Spots</div>
              <div className="stat-value">{p.available ?? '—'}</div>
              <div className="stat-sub">of {p.total_spots} total</div>
            </div>
          </div>

          <div className="stat-card green">
            <div className="stat-icon green">📊</div>
            <div className="stat-info">
              <div className="stat-label">Occupancy</div>
              <div className="stat-value">{p.occupancy_pct ?? 0}%</div>
              <div className="stat-sub">{p.occupied} spots occupied</div>
            </div>
          </div>

          <div className="stat-card purple">
            <div className="stat-icon purple">⚡</div>
            <div className="stat-info">
              <div className="stat-label">Active Chargers</div>
              <div className="stat-value">{activeChargers}</div>
              <div className="stat-sub">of {data?.total_chargers} total</div>
            </div>
          </div>

          <div className="stat-card amber">
            <div className="stat-icon amber">🔋</div>
            <div className="stat-info">
              <div className="stat-label">Energy Used</div>
              <div className="stat-value">{energy.total_kwh?.toFixed(1) ?? '0'}</div>
              <div className="stat-sub">kWh total</div>
            </div>
          </div>

          {blockedChargers > 0 && (
            <div className="stat-card red">
              <div className="stat-icon red">🚫</div>
              <div className="stat-info">
                <div className="stat-label">Blocked</div>
                <div className="stat-value">{blockedChargers}</div>
                <div className="stat-sub">charger{blockedChargers > 1 ? 's' : ''} blocked</div>
              </div>
            </div>
          )}
        </div>

        {/* Parking Grid (full width) */}
        <div className="panels-grid" style={{ gridTemplateColumns: '1fr' }}>
          <ParkingGrid parking={p} />
        </div>

        {/* Charger Status + Energy Chart */}
        <div className="panels-grid">
          <ChargerStatus chargers={chargers} />
          <EnergyChart history={energyHistory} />
        </div>

        {/* Occupancy Trend + Environment */}
        <div className="panels-grid">
          <OccupancyTrend history={occHistory} />
          <EnvironmentPanel current={env} history={envHistory} />
        </div>

      </main>
    </>
  )
}
