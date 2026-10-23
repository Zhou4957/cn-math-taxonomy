/* 访问统计配置。两项都留空时，站点不加载任何统计脚本，也不发出任何统计请求。
 * 本 fork 为孩子自用版：endpoint 已清空，不向原作者的统计端上报。 */
window.CNM_STATS = {
  cloudflareToken: '',
  endpoint: '',
  onEvent: null
};
