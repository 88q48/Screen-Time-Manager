/* config.js — 网页配置
 *
 * 联调时改这里，不用动其他文件：
 *   USE_MOCK = false，并把 API_BASE_URL 改成后端的真实地址。
 */
window.CONFIG = {
  // true = 用 mock-data.js 里的数据；false = 请求后端
  USE_MOCK: true,

  // 后端接口前缀（与 /api/v1 协议一致）
  API_BASE_URL: "http://localhost:8000/api/v1",

  // 当前设备标识
  DEVICE_ID: "win_device_01",

  // 统计天数
  DAYS: 7,

  // 请求超时（毫秒）
  TIMEOUT: 10000
};
