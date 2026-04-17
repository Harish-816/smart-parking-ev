import { useState, useEffect, useCallback } from 'react'
import axios from 'axios'
import ParkingGrid from './components/ParkingGrid'
import ChargerStatus from './components/ChargerStatus'
import EnergyChart from './components/EnergyChart'
import OccupancyTrend from './components/OccupancyTrend'
import EnvironmentPanel from './components/EnvironmentPanel'
import AlertBanner from './components/AlertBanner'
import './index.css'

const API = `/api`

export default function App() {
  const [data, setData] = useState(null)
  const [occHistory, setOccHistory] = useState([])
  const [energyHistory, setEnergyHistory] = useState([])
  const [envHistory, setEnvHistory] = useState([])
  const [loading, setLoading] = useState(true)
  const [lastUpdate, setLastUpdate] = useState(null)

  const fetchData = useCallback(async () => {
    try {
      const summary = await axios.get(`${API}/dashboard/summary`)
      setData(summary.data)

      // Build history snapshots from the summary data itself
      const now = new Date().toISOString()
      const p = summary.data?.parking || {}
      const env = summary.data?.environment || {}

      setOccHistory(prev => [...prev.slice(-29), {
        recorded_at: now,
        occupied: p.occupied || 0,
        available: p.available || 0,
        occ_pct: p.occupancy_pct || 0
      }])

      const chargerList = summary.data?.chargers || []
      const perCharger = {}
      chargerList.forEach(c => {
        // Prefer energy_kwh per charger (AWS), fallback to power_kw as proxy (local)
        perCharger[c.charger_id] = parseFloat(c.energy_kwh || c.power_kw || 0)
      })
      const totalKwh = chargerList.some(c => c.energy_kwh)
        ? chargerList.reduce((s, c) => s + parseFloat(c.energy_kwh || 0), 0)
        : parseFloat(summary.data?.energy?.total_kwh || 0)

      setEnergyHistory(prev => [...prev.slice(-29), {
        recorded_at: now,
        total_kwh: totalKwh,
        per_charger: perCharger
      }])

      setEnvHistory(prev => [...prev.slice(-29), {
        recorded_at: now,
        avg_temp_c: env.avg_temp_c || 0,
        avg_humidity: env.avg_humidity || env.avg_humidity_pct || 0,
        avg_lux: env.avg_lux || 0
      }])

      setLastUpdate(new Date())
      setLoading(false)
    } catch (err) {
      console.error('API fetch failed:', err)
      setLoading(false)
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
  const env = data?.environment || {}
  const alerts = data?.blocked_alerts || []
  const activeChargers = chargers.filter(c => c.status === 'in_use').length
  const blockedChargers = chargers.filter(c => c.status === 'blocked').length
  // Support both AWS (energy_kwh per charger) and local Flask (energy object)
  const totalEnergy = chargers.some(c => c.energy_kwh)
    ? chargers.reduce((sum, c) => sum + parseFloat(c.energy_kwh || 0), 0)
    : parseFloat(data?.energy?.total_kwh || 0)

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
              <div className="stat-value">{totalEnergy.toFixed(1)}</div>
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
