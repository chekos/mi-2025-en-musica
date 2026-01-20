// Charts.js - Funciones de visualización para Mi 2025 en Música

function renderMetrics(overview) {
  document.getElementById('total-minutes').textContent =
    overview.total_minutes.toLocaleString();

  document.getElementById('metrics-secondary').innerHTML = `
    <div><strong>${overview.total_days}</strong> <span>días</span></div>
    <div><strong>${overview.unique_artists}</strong> <span>artistas</span></div>
    <div><strong>${overview.unique_tracks.toLocaleString()}</strong> <span>canciones</span></div>
  `;
}

function renderTopArtists(artists) {
  const container = document.getElementById('top-artists');
  if (!container) return;
  container.innerHTML = artists.map((a, i) => `
    <li>
      <span class="rank">${i + 1}</span>
      <span class="top-name">${a.artist}</span>
      <span class="top-stats">${a.hours}h</span>
    </li>
  `).join('');
}

function renderTopTracks(tracks) {
  const container = document.getElementById('top-tracks');
  if (!container) return;
  container.innerHTML = tracks.map((t, i) => `
    <li>
      <span class="rank">${i + 1}</span>
      <div>
        <div class="top-name">${t.track}</div>
        <div class="top-artist">${t.artist}</div>
      </div>
      <span class="top-stats">${t.minutes}m</span>
    </li>
  `).join('');
}

function renderHourlyChart(hourlyData, peakHours) {
  const container = document.getElementById('hourly-chart');
  if (!container) return;

  const chart = Plot.plot({
    height: 180,
    marginLeft: 40,
    marginBottom: 30,
    x: {
      label: null,
      tickFormat: d => `${d}h`
    },
    y: {
      label: "reproducciones",
      grid: false
    },
    marks: [
      Plot.barY(hourlyData, {
        x: "hour",
        y: "plays",
        fill: "#1a1a1a",
        tip: true
      }),
      Plot.ruleY([0])
    ]
  });

  container.appendChild(chart);

  const annotation = document.getElementById('hourly-annotation');
  if (annotation) {
    annotation.textContent = `Hora pico: ${peakHours.peak_hour}:00 · ${peakHours.description}`;
  }
}

function renderHeatmap(heatmapData) {
  const container = document.getElementById('heatmap-chart');
  if (!container) return;
  const monthNames = ["", "Ene", "Feb", "Mar", "Abr", "May", "Jun",
                       "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"];

  const chart = Plot.plot({
    height: 280,
    marginLeft: 40,
    marginBottom: 30,
    padding: 0.05,
    x: {
      label: null,
      tickFormat: d => monthNames[d]
    },
    y: {
      label: null,
      tickFormat: d => `${d}h`
    },
    color: {
      scheme: "greys",
      legend: true,
      label: "plays"
    },
    marks: [
      Plot.cell(heatmapData, {
        x: "month",
        y: "hour",
        fill: "plays",
        tip: true
      })
    ]
  });

  container.appendChild(chart);
}

function renderFacetedHeatmap(heatmapData) {
  const container = document.getElementById('faceted-heatmap');
  if (!container) return;
  const dayNames = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"];
  const monthNamesShort = ["", "Ene", "Feb", "Mar", "Abr", "May", "Jun",
                           "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"];

  const maxPlays = Math.max(...heatmapData.map(d => d.plays));

  container.style.display = 'flex';
  container.style.flexDirection = 'column';

  for (let month = 1; month <= 12; month++) {
    const monthData = heatmapData.filter(d => d.month === month);
    const chartData = monthData.length > 0 ? monthData : [];

    const isFirst = month === 1;
    const isLast = month === 12;

    const rowContainer = document.createElement('div');
    rowContainer.style.display = 'flex';
    rowContainer.style.alignItems = 'center';
    rowContainer.style.margin = '0';
    rowContainer.style.padding = '0';

    const label = document.createElement('div');
    label.textContent = monthNamesShort[month];
    label.style.fontSize = '0.7rem';
    label.style.fontWeight = '600';
    label.style.width = '30px';
    label.style.textAlign = 'right';
    label.style.paddingRight = '6px';
    label.style.color = '#525252';
    rowContainer.appendChild(label);

    const marginTop = isFirst ? 18 : 0;
    const marginBottom = isLast ? 18 : 0;

    const chart = Plot.plot({
      height: 52 + marginTop + marginBottom,
      width: container.clientWidth - 36 || 820,
      marginLeft: 26,
      marginBottom: marginBottom,
      marginTop: marginTop,
      marginRight: 2,
      padding: 0,
      x: {
        domain: [0, 1, 2, 3, 4, 5, 6],
        tickFormat: d => dayNames[d],
        label: null,
        axis: isFirst ? "top" : (isLast ? "bottom" : null)
      },
      y: {
        domain: d3.range(0, 24),
        tickFormat: d => d % 6 === 0 ? `${d}h` : "",
        label: null,
        reverse: false
      },
      color: {
        domain: [0, maxPlays],
        scheme: "greys",
        legend: false
      },
      marks: [
        Plot.cell(chartData, {
          x: "weekday",
          y: "hour",
          fill: "plays",
          tip: {
            format: {
              x: d => dayNames[d],
              y: d => `${d}:00`
            }
          }
        })
      ]
    });

    rowContainer.appendChild(chart);
    container.appendChild(rowContainer);
  }
}

function renderDayHourHeatmap(heatmapData) {
  const container = document.getElementById('day-hour-heatmap');
  if (!container) return;
  const monthNamesShort = ["", "Ene", "Feb", "Mar", "Abr", "May", "Jun",
                           "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"];
  const daysInMonth = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];

  // Nombres de los bloques de 4 horas
  const timeBlockNames = [
    "Madrugada",   // 0: 1am-5am
    "Mañana",      // 1: 5am-9am
    "Mediodía",    // 2: 9am-1pm
    "Tarde",       // 3: 1pm-5pm
    "Noche",       // 4: 5pm-9pm
    "Medianoche"   // 5: 9pm-1am
  ];

  const maxPlays = Math.max(...heatmapData.map(d => d.plays));

  container.style.display = 'flex';
  container.style.flexDirection = 'column';

  for (let month = 1; month <= 12; month++) {
    const monthData = heatmapData.filter(d => d.month === month);
    const chartData = monthData.length > 0 ? monthData : [];
    const maxDay = daysInMonth[month];

    const isFirst = month === 1;
    const isLast = month === 12;

    const rowContainer = document.createElement('div');
    rowContainer.style.display = 'flex';
    rowContainer.style.alignItems = 'center';
    rowContainer.style.margin = '0';
    rowContainer.style.padding = '0';

    const label = document.createElement('div');
    label.textContent = monthNamesShort[month];
    label.style.fontSize = '0.7rem';
    label.style.fontWeight = '600';
    label.style.width = '30px';
    label.style.textAlign = 'right';
    label.style.paddingRight = '6px';
    label.style.color = '#525252';
    rowContainer.appendChild(label);

    const marginTop = isFirst ? 22 : 8;
    const marginBottom = isLast ? 22 : 8;
    const baseHeight = 18 * 6; // 6 bloques de tiempo

    const chart = Plot.plot({
      height: baseHeight + marginTop + marginBottom,
      width: container.clientWidth - 36 || 820,
      marginLeft: 75,
      marginBottom: marginBottom,
      marginTop: marginTop,
      marginRight: 8,
      padding: 0,
      clip: false,
      x: {
        domain: d3.range(1, maxDay + 1),
        tickFormat: d => d % 5 === 1 ? `${d}` : "",
        label: null,
        axis: isFirst ? "top" : (isLast ? "bottom" : null)
      },
      y: {
        domain: d3.range(0, 6),
        tickFormat: d => timeBlockNames[d],
        label: null,
        reverse: false
      },
      color: {
        domain: [0, maxPlays],
        scheme: "greys",
        legend: false
      },
      marks: [
        Plot.dot(chartData, {
          x: "day",
          y: "time_block",
          r: d => Math.sqrt(d.plays) * 3,
          fill: "plays",
          tip: {
            format: {
              x: d => `día ${d}`,
              y: d => timeBlockNames[d]
            }
          }
        })
      ]
    });

    rowContainer.appendChild(chart);
    container.appendChild(rowContainer);
  }
}

function renderMonthlyChart(monthlyData) {
  const container = document.getElementById('monthly-chart');
  if (!container) return;

  const getBarColor = (d) => {
    if (d.is_inflection) return "#1a1a1a";
    if (d.is_peak) return "#525252";
    return "#d4d4d4";
  };

  const chart = Plot.plot({
    height: 180,
    marginLeft: 40,
    marginBottom: 30,
    x: {
      label: null,
      tickFormat: d => monthlyData.find(m => m.month === d)?.month_name || d
    },
    y: {
      label: "horas",
      grid: false
    },
    marks: [
      Plot.barY(monthlyData, {
        x: "month",
        y: "hours",
        fill: getBarColor,
        tip: {
          format: {
            x: false,
            y: true
          }
        }
      }),
      Plot.ruleY([0])
    ]
  });

  container.appendChild(chart);
}

function renderWeekdayComparison(data) {
  const container = document.getElementById('weekday-comparison');
  if (!container) return;

  const weekdayAvg = data.weekday.avg_hours_per_day;
  const weekendAvg = data.weekend.avg_hours_per_day;
  const winner = weekendAvg > weekdayAvg ? "weekend" : "weekday";

  container.innerHTML = `
    <div class="comparison-card">
      <div class="comparison-title">Lun – Vie</div>
      <div class="comparison-value">${weekdayAvg}</div>
      <div class="comparison-unit">horas/día</div>
      <div class="comparison-label">promedio</div>
      <div class="comparison-secondary">
        ${data.weekday.total_hours}h total · ${data.weekday.days_count} días
      </div>
    </div>
    <div class="comparison-card">
      <div class="comparison-title">Sáb – Dom</div>
      <div class="comparison-value">${weekendAvg}</div>
      <div class="comparison-unit">horas/día</div>
      <div class="comparison-label">promedio ${winner === 'weekend' ? '↑' : ''}</div>
      <div class="comparison-secondary">
        ${data.weekend.total_hours}h total · ${data.weekend.days_count} días
      </div>
    </div>
  `;
}

function renderSkippedTracks(tracks) {
  const container = document.getElementById('skipped-tracks');
  if (!container) return;

  if (tracks.length === 0) {
    container.innerHTML = '<li>No hay canciones con alto skip rate (10+ plays)</li>';
    return;
  }

  container.innerHTML = tracks.map(t => `
    <li>
      <span class="skip-rate">${t.skip_rate}%</span>
      <div class="skip-info">
        <div class="skip-track">${t.track}</div>
        <div class="skip-artist">${t.artist} · ${t.skipped}/${t.total_plays} skips</div>
      </div>
    </li>
  `).join('');
}

// Función para cargar datos
async function loadData() {
  const response = await fetch('data/spotify-2025.json');
  return await response.json();
}
