/* charts.js — 图表配置
 *
 * 每个函数收数据、返回一份 ECharts 配置对象。
 * 渲染交给 app.js 统一处理。
 */
(function () {
  var PALETTE = ["#5b7cfa", "#67c23a", "#f5a623", "#f56c6c", "#9b59b6", "#14b8a6"];

  function toHours(sec) {
    return Math.round((sec / 3600) * 100) / 100;
  }

  var BASE = {
    color: PALETTE,
    textStyle: { fontFamily: '"Microsoft YaHei", system-ui, sans-serif' },
    grid: { left: 48, right: 24, top: 30, bottom: 40 },
    tooltip: { trigger: "item", confine: true }
  };

  window.Charts = {
    /* 每日使用时长折线图 */
    lineTrend: function (trend) {
      var dates = trend.map(function (d) { return d.date; });
      var hours = trend.map(function (d) { return toHours(d.total_duration_seconds); });

      return {
        color: PALETTE,
        textStyle: BASE.textStyle,
        grid: BASE.grid,
        tooltip: { trigger: "axis", valueFormatter: function (v) { return v + " 小时"; } },
        xAxis: {
          type: "category",
          data: dates,
          boundaryGap: false,
          axisLine: { lineStyle: { color: "#dfe4ee" } },
          axisLabel: { color: "#6b7280", fontSize: 11 }
        },
        yAxis: {
          type: "value",
          name: "小时",
          nameTextStyle: { color: "#9aa3b2", fontSize: 11 },
          splitLine: { lineStyle: { color: "#eef1f7" } },
          axisLabel: { color: "#6b7280", fontSize: 11 }
        },
        series: [{
          type: "line",
          data: hours,
          smooth: true,
          symbolSize: 7,
          lineStyle: { width: 3 },
          areaStyle: {
            color: {
              type: "linear", x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: "rgba(91,124,250,.28)" },
                { offset: 1, color: "rgba(91,124,250,.02)" }
              ]
            }
          }
        }]
      };
    },

    /* 应用使用排行（横向条形） */
    barRanking: function (appRanking) {
      var sorted = appRanking.slice().sort(function (a, b) {
        return a.duration_seconds - b.duration_seconds;
      });
      var names = sorted.map(function (d) { return d.app_name; });
      var hours = sorted.map(function (d) { return toHours(d.duration_seconds); });

      return {
        color: PALETTE,
        textStyle: BASE.textStyle,
        grid: { left: 78, right: 56, top: 16, bottom: 34 },
        tooltip: { trigger: "axis", axisPointer: { type: "shadow" },
                   valueFormatter: function (v) { return v + " 小时"; } },
        xAxis: {
          type: "value",
          splitLine: { lineStyle: { color: "#eef1f7" } },
          axisLabel: { color: "#6b7280", fontSize: 11 }
        },
        yAxis: {
          type: "category",
          data: names,
          axisLine: { lineStyle: { color: "#dfe4ee" } },
          axisLabel: { color: "#374151", fontSize: 12 }
        },
        series: [{
          type: "bar",
          data: hours,
          barWidth: 16,
          itemStyle: { borderRadius: [0, 6, 6, 0] },
          label: { show: true, position: "right", formatter: "{c} h",
                   color: "#6b7280", fontSize: 11 }
        }]
      };
    },

    /* 使用类别占比（环形） */
    pieCategory: function (appRanking) {
      var totals = {};
      appRanking.forEach(function (item) {
        totals[item.category] = (totals[item.category] || 0) + item.duration_seconds;
      });
      var data = Object.keys(totals).map(function (k) {
        return { name: k, value: toHours(totals[k]) };
      });

      return {
        color: PALETTE,
        textStyle: BASE.textStyle,
        tooltip: { trigger: "item", formatter: "{b}：{c} 小时（{d}%）", confine: true },
        legend: { bottom: 0, icon: "circle", textStyle: { color: "#6b7280", fontSize: 12 } },
        series: [{
          type: "pie",
          radius: ["45%", "70%"],
          center: ["50%", "45%"],
          avoidLabelOverlap: true,
          itemStyle: { borderColor: "#fff", borderWidth: 2 },
          label: { formatter: "{b}\n{d}%", color: "#374151", fontSize: 11 },
          data: data
        }]
      };
    },

    /* 个人 vs 群体 */
    barGroupCompare: function (summary, group) {
      var me = toHours(summary.avg_daily_seconds);
      var avg = toHours(group.group_avg_daily_seconds);

      return {
        color: ["#5b7cfa", "#c7d0e8"],
        textStyle: BASE.textStyle,
        grid: { left: 52, right: 24, top: 30, bottom: 34 },
        tooltip: { trigger: "axis", valueFormatter: function (v) { return v + " 小时"; } },
        xAxis: {
          type: "category",
          data: ["我", "群体均值"],
          axisLine: { lineStyle: { color: "#dfe4ee" } },
          axisLabel: { color: "#374151", fontSize: 13 }
        },
        yAxis: {
          type: "value",
          name: "日均小时",
          nameTextStyle: { color: "#9aa3b2", fontSize: 11 },
          splitLine: { lineStyle: { color: "#eef1f7" } },
          axisLabel: { color: "#6b7280", fontSize: 11 }
        },
        series: [{
          type: "bar",
          data: [me, avg],
          barWidth: 56,
          itemStyle: { borderRadius: [8, 8, 0, 0] },
          label: { show: true, position: "top", formatter: "{c} h",
                   color: "#6b7280", fontSize: 12 }
        }]
      };
    }
  };
})();
