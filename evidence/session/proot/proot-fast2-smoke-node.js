const { Worker } = require("worker_threads");
new Worker("require('worker_threads').parentPort.postMessage(21*2)", { eval: true }).on("message", m => {
  console.log("node_worker", m);
  require("child_process").exec("echo child", (e, o) => console.log("node_child", o.trim()));
});
