import React from 'react'

export default function ParkingGrid({ parking }) {
    const spots = parking?.spots || []
    const total = parking?.total_spots || 50

    // If no data yet, generate placeholder spots
    const displaySpots = spots.length > 0
        ? spots
        : Array.from({ length: total }, (_, i) => ({
            spot_id: `SPOT-${String(i + 1).padStart(3, '0')}`,
            occupied: 0
        }))

    return (
        <div className="panel parking-grid-container">
            <div className="panel-title">
                <span className="icon">🗺️</span>
                Parking Grid — Real-Time Availability
            </div>
            <div className="parking-grid">
                {displaySpots.map(spot => (
                    <div
                        key={spot.spot_id}
                        className={`parking-spot ${spot.occupied ? 'occupied' : 'vacant'}`}
                        title={`${spot.spot_id}: ${spot.occupied ? 'Occupied' : 'Vacant'}`}
                    >
                        {spot.spot_id.replace('SPOT-', '')}
                    </div>
                ))}
            </div>
            <div className="parking-legend">
                <div className="legend-item">
                    <div className="legend-dot green" />
                    Vacant ({parking?.available ?? '—'})
                </div>
                <div className="legend-item">
                    <div className="legend-dot red" />
                    Occupied ({parking?.occupied ?? '—'})
                </div>
            </div>
        </div>
    )
}
