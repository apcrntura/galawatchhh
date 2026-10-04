// Turns a destination row + live count row into everything the dashboard shows.
export const LEVEL_COLOR = { high: '#dc2626', med: '#d97706', low: '#16a34a' }
export const FRESH_MS = 60000

export function derive(d, row, settings, trend, cameras, now) {
  const live = !!d.is_live
  let visitors, cap, peopleIn = null, peopleOut = null, updatedAt = null

  if (live) {
    visitors = row?.current_inside ?? 0
    peopleIn = row?.people_in ?? 0
    peopleOut = row?.people_out ?? 0
    updatedAt = row?.updated_at ?? null
    cap = d.capacity ? Math.min(100, Math.round((visitors / d.capacity) * 100)) : 0
  } else {
    visitors = d.sample_visitors || 0
    cap = d.sample_cap || 0
  }

  const high = live && d.alert_at != null ? visitors >= d.alert_at : cap > settings.high
  const level = high ? 'high' : cap > settings.medium ? 'med' : 'low'

  const cams = cameras.filter(c => c.destination_id === d.id)
  const fresh = live && updatedAt && now - new Date(updatedAt).getTime() < FRESH_MS
  const camTotal = live ? Math.max(cams.length, 1) : cams.length
  const camOnline = live ? (fresh ? 1 : 0) : cams.filter(c => c.status === 'Active').length

  let note, tone
  if (live) {
    if (!row) { note = 'Waiting for live camera data.'; tone = 'info' }
    else if (high) {
      note = `Overcrowding alert: ${visitors} people inside (limit ${d.alert_at}). IN: ${peopleIn} | OUT: ${peopleOut}`
      tone = 'warn'
    } else {
      note = `Live camera: ${visitors} people inside. IN: ${peopleIn} | OUT: ${peopleOut}`
      tone = 'info'
    }
  } else {
    note = d.sample_note
    tone = high ? 'warn' : level === 'med' ? 'info' : 'ok'
  }

  return {
    ...d, live, visitors, cap, level, high, color: LEVEL_COLOR[level],
    peopleIn, peopleOut, updatedAt, camTotal, camOnline, note, tone,
    trend: live ? (trend?.values || [0, 0, 0, 0, 0, 0, 0]) : (d.sample_trend || [0, 0, 0, 0, 0, 0, 0]),
    trendLabels: live ? (trend?.labels || null) : null
  }
}
