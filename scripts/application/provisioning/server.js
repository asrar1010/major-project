const express = require("express");
const os = require("os");
const path = require("path");

const app = express();
const PORT = 5000;

/* ------------ DETERMINISTIC CPU TASK ------------ */
function cpuTask(iterations = 1000000) {
  let x = 0;
  for (let i = 1; i <= iterations; i++) {
    x += Math.sqrt(i);
  }
  return x;
}

/* ------------ DISABLE CACHING ------------ */
app.use((req, res, next) => {
  res.setHeader("Cache-Control", "no-store, no-cache, must-revalidate, private");
  res.setHeader("Pragma", "no-cache");
  res.setHeader("Expires", "0");
  next();
});

/* ------------ VIEW SETUP ------------ */
app.set("view engine", "ejs");
app.set("views", path.join(__dirname, "views"));

/* ------------ ROUTE ------------ */
app.get("/", (req, res) => {
  const start = process.hrtime();
  const hostname = os.hostname();

  // 🔥 SAME CPU WORK EVERY REQUEST
  cpuTask(1_000_000);

  const diff = process.hrtime(start);
  const responseTimeMs =
    (diff[0] * 1e3 + diff[1] / 1e6).toFixed(2);

  res.render("index", {
    hostname,
    responseTime: responseTimeMs
  });
});

/* ------------ START SERVER ------------ */
app.listen(PORT, () => {
  console.log(`🚀 Express app running on port ${PORT}`);
});
