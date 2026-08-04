async function drawDayChart() {
  const res = await fetch("/api/sample-day");
  const data = await res.json();

  const canvas = document.getElementById("day-chart");
  const ctx = canvas.getContext("2d");
  const W = canvas.width, H = canvas.height;
  const padL = 60, padR = 20, padT = 20, padB = 30;

  ctx.clearRect(0, 0, W, H);

  const all = [...data.actual, ...data.our_model, ...data.operator];
  const min = Math.min(...all) * 0.98;
  const max = Math.max(...all) * 1.02;

  const x = (i) => padL + (i / (data.labels.length - 1)) * (W - padL - padR);
  const y = (v) => H - padB - ((v - min) / (max - min)) * (H - padT - padB);

  // Gridlines + y-axis labels
  ctx.strokeStyle = "#232936";
  ctx.fillStyle = "#9ca3af";
  ctx.font = "11px sans-serif";
  for (let i = 0; i <= 4; i++) {
    const val = min + (i / 4) * (max - min);
    const yy = y(val);
    ctx.beginPath();
    ctx.moveTo(padL, yy);
    ctx.lineTo(W - padR, yy);
    ctx.stroke();
    ctx.fillText(Math.round(val).toLocaleString(), 4, yy + 4);
  }

  function drawLine(series, color, dashed) {
    ctx.beginPath();
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.setLineDash(dashed ? [6, 4] : []);
    series.forEach((v, i) => {
      const px = x(i), py = y(v);
      if (i === 0) ctx.moveTo(px, py);
      else ctx.lineTo(px, py);
    });
    ctx.stroke();
    ctx.setLineDash([]);
  }

  drawLine(data.actual, "#f3f4f6", false);
  drawLine(data.our_model, "#8b5cf6", false);
  drawLine(data.operator, "#10b981", true);

  // x-axis labels (every 4 hours)
  ctx.fillStyle = "#9ca3af";
  data.labels.forEach((label, i) => {
    if (i % 4 === 0) ctx.fillText(label, x(i) - 12, H - 8);
  });

  // legend
  const legend = [["Actual", "#f3f4f6"], ["Our model", "#8b5cf6"], ["Grid operator", "#10b981"]];
  legend.forEach(([label, color], i) => {
    const lx = padL + i * 140;
    ctx.fillStyle = color;
    ctx.fillRect(lx, 6, 10, 10);
    ctx.fillStyle = "#f3f4f6";
    ctx.fillText(label, lx + 14, 15);
  });
}

drawDayChart();
