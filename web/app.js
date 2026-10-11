/* app.js — 数据获取、渲染、使用建议
 *
 * 数据来源由 config.js 的 USE_MOCK 决定：
 *   true  → mock-data.js
 *   false → 后端 /api/v1/devices/{device_id}/analysis
 */
(function () {
  "use strict";

  var cfg = window.CONFIG || {};

  /* ---------- 小工具 ---------- */
  function fmtHours(sec) {
    return (sec / 3600).toFixed(1) + " 小时";
  }

  /* ---------- 取数据 ---------- */
  function fetchWithTimeout(url, ms) {
    var ctrl = new AbortController();
    var timer = setTimeout(function () { ctrl.abort(); }, ms);

    return fetch(url, { signal: ctrl.signal }).then(function (resp) {
      clearTimeout(timer);
      if (!resp.ok) {
        throw new Error("HTTP " + resp.status);
      }
      return resp.json();
    });
  }

  function getData() {
    if (cfg.USE_MOCK) {
      return Promise.resolve(window.MOCK_DATA);
    }
    var url = cfg.API_BASE_URL
            + "/devices/" + encodeURIComponent(cfg.DEVICE_ID)
            + "/analysis?days=" + cfg.DAYS;
    return fetchWithTimeout(url, cfg.TIMEOUT || 10000);
  }

  /* ---------- 使用建议（与 Python 版判断规则一致） ---------- */
  function buildTips(summary, appRanking) {
    var tips = [];

    var avgH = summary.avg_daily_seconds / 3600;
    if (avgH > 6) {
      tips.push("日均 " + avgH.toFixed(1) + " 小时，使用时间偏长，建议明显减少。");
    } else if (avgH > 4) {
      tips.push("日均 " + avgH.toFixed(1) + " 小时，略高于健康范围，注意控制。");
    }

    var entertainment = appRanking
      .filter(function (i) { return i.category === "娱乐"; })
      .reduce(function (s, i) { return s + i.duration_seconds; }, 0);
    var total = summary.total_duration_seconds;
    if (total > 0 && entertainment / total > 0.4) {
      tips.push("娱乐类应用占比超过 40%，建议调整使用结构。");
    }

    var study = appRanking
      .filter(function (i) { return i.category === "学习"; })
      .reduce(function (s, i) { return s + i.duration_seconds; }, 0);
    if (study < 0.5 * 3600) {
      tips.push("学习类应用使用时间偏少，可适当增加。");
    }

    if (tips.length === 0) {
      tips.push("使用情况良好 👍");
    }
    return tips;
  }

  /* ---------- 渲染 ---------- */
  var chartInstances = [];

  function renderChart(id, option) {
    var el = document.getElementById(id);
    if (!el) { return; }
    var inst = echarts.getInstanceByDom(el) || echarts.init(el);
    inst.setOption(option);
    if (chartInstances.indexOf(inst) === -1) { chartInstances.push(inst); }
  }

  function renderMetrics(summary) {
    var items = [
      ["总时长", fmtHours(summary.total_duration_seconds)],
      ["日均", fmtHours(summary.avg_daily_seconds)],
      ["中位数", fmtHours(summary.median_daily_seconds)],
      ["P90", fmtHours(summary.p90_daily_seconds)]
    ];
    document.getElementById("metrics").innerHTML = items.map(function (kv) {
      return '<div class="card"><div class="label">' + kv[0] +
             '</div><div class="value">' + kv[1] + "</div></div>";
    }).join("");
  }

  function renderTips(tips) {
    document.getElementById("tips").innerHTML = tips.map(function (t) {
      return "<li>" + t + "</li>";
    }).join("");
  }

  function renderMeta(data, isMock) {
    var p = data.period || {};
    document.getElementById("meta-line").textContent =
      "数据范围：" + (p.start || "-") + " ~ " + (p.end || "-") +
      "　设备：" + data.device_id;

    var badge = document.getElementById("source-badge");
    badge.textContent = isMock ? "演示数据（mock）" : "实时数据（API）";
    badge.className = "badge" + (isMock ? "" : " real");

    document.getElementById("footer").textContent =
      "数据来源：后端 /api/v1/devices/{device_id}/analysis" +
      (isMock ? "（当前为 mock）" : "");
  }

  function renderAll(data, isMock) {
    renderMeta(data, isMock);
    renderMetrics(data.summary);

    renderChart("chart-trend", window.Charts.lineTrend(data.trend));
    renderChart("chart-ranking", window.Charts.barRanking(data.app_ranking));
    renderChart("chart-category", window.Charts.pieCategory(data.app_ranking));
    renderChart("chart-group", window.Charts.barGroupCompare(data.summary, data.group_comparison));

    var g = data.group_comparison;
    document.getElementById("rank-note").textContent =
      "你在群体中排名：第 " + g.my_rank + " 名 / 共 " + g.group_size + " 人";

    renderTips(buildTips(data.summary, data.app_ranking));
  }

  function showError(msg) {
    var badge = document.getElementById("source-badge");
    badge.textContent = "加载失败";
    badge.className = "badge err";
    document.getElementById("meta-line").textContent = msg;
    document.getElementById("tips").innerHTML =
      "<li>数据加载失败：" + msg + "</li>";
  }

  /* 暴露给测试脚本使用 */
  window.buildTips = buildTips;

  /* ---------- 启动 ---------- */
  if (typeof document !== "undefined" && document.getElementById("tips")) {
    getData()
      .then(function (data) { renderAll(data, !!cfg.USE_MOCK); })
      .catch(function (e) { showError(e && e.message ? e.message : String(e)); });

    window.addEventListener("resize", function () {
      chartInstances.forEach(function (c) { c.resize(); });
    });
  }
})();
