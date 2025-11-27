(function () {
  const onTimeEl = document.getElementById('statOnTime');
  const studentsEl = document.getElementById('statStudents');
  const gatesEl = document.getElementById('statGates');
  const scanEl = document.getElementById('statScan');
  const updatedEl = document.getElementById('liveUpdated');
  const feedEl = document.getElementById('liveFeed');

  if (!onTimeEl) return;

  function renderFeed(items) {
    if (!items.length) {
      feedEl.innerHTML = '<p class="muted">No gate events yet today.</p>';
      return;
    }
    feedEl.innerHTML = items
      .map(
        (item) => `
        <div class="feed-item ${item.success ? 'ok' : 'warn'}">
            <div>
                <p class="feed-label">${item.action.toUpperCase()}</p>
                <p class="muted">Student ${item.student}</p>
            </div>
            <span>${new Date(item.time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
        </div>`
      )
      .join('');
  }

  async function loadStats() {
    try {
      const response = await fetch('/api/live-stats/');
      const data = await response.json();

      onTimeEl.textContent = `${data.success_rate.toFixed(1)}%`;
      studentsEl.textContent = data.students.toLocaleString();
      gatesEl.textContent = data.active_gates.toString();
      scanEl.textContent = `${data.average_scan_time}s`;
      updatedEl.textContent = `Updated ${new Date(data.last_updated).toLocaleTimeString()}`;
      renderFeed(data.live_feed || []);

      document.documentElement.style.setProperty(
        '--live-accent',
        data.success_rate >= 95 ? '#22d3ee' : '#f97316'
      );
    } catch (error) {
      console.error('Unable to load live stats', error);
      updatedEl.textContent = 'Live snapshot unavailable';
    }
  }

  loadStats();
  setInterval(loadStats, 10000);
})();
