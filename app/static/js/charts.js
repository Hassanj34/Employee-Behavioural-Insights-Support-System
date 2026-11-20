(function () {
  const node = document.getElementById("trend-data");
  if (!node || typeof Chart === "undefined") return;
  const data = JSON.parse(node.textContent);
  if (!data.labels || !data.labels.length) return;

  const specs = [
    ["workloadChart", "workload", "#0e7c74"],
    ["motivationChart", "motivation", "#1f7a4d"],
    ["learningChart", "learning", "#c56a32"],
  ];

  specs.forEach(function (spec) {
    const canvas = document.getElementById(spec[0]);
    if (!canvas) return;
    new Chart(canvas, {
      type: "line",
      data: {
        labels: data.labels,
        datasets: [{
          data: data[spec[1]],
          borderColor: spec[2],
          backgroundColor: spec[2],
          tension: 0.25,
          pointRadius: 4,
          borderWidth: 2,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          y: { min: 1, max: 5, ticks: { stepSize: 1 } },
        },
      },
    });
  });
})();
