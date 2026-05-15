import type {
  ProjectGeneratorModelProfile,
  ProjectGeneratorProjectType,
  ProjectGeneratorStrategy,
} from '@/types/generator';

export const PROJECT_TYPE_LABELS: Record<ProjectGeneratorProjectType, string> = {
  'business-dashboard': '经营看板',
  'admin-system': '管理后台',
  'marketing-site': '宣传官网',
  'mobile-h5': '手机页面',
  'data-report': '数据报告',
  custom: '其他类型',
};

export const GENERATION_STRATEGY_OPTIONS: Array<{
  id: ProjectGeneratorStrategy;
  label: string;
  hint: string;
}> = [
  { id: 'quality', label: '质量优先', hint: '更适合正式交给同事继续开发' },
  { id: 'quick', label: '先出样子', hint: '先把主要页面和内容跑通' },
  { id: 'budget', label: '节省成本', hint: '控制模型成本和生成范围' },
  { id: 'strict', label: '更稳妥', hint: '先把需求、风险和边界说清楚' },
];

export const MODEL_PROFILE_OPTIONS: Array<{
  id: ProjectGeneratorModelProfile;
  label: string;
  hint: string;
  cost: string;
}> = [
  { id: 'recommended', label: '推荐', hint: '按团队默认配置继续', cost: '均衡' },
  { id: 'faster', label: '更快', hint: '适合简单页面或原型', cost: '较低' },
  { id: 'stronger', label: '更强', hint: '适合复杂业务和多页面系统', cost: '较高' },
  { id: 'cheaper', label: '更省', hint: '适合预算敏感的任务', cost: '低' },
  { id: 'custom', label: '专家自定义', hint: '由技术同事在 Cursor / Codex 中接管', cost: '由同事确认' },
];

export const DEFAULT_PAGES = ['首页', '列表页', '详情页'];
