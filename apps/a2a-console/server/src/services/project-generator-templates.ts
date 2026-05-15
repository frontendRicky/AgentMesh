import type { ProjectGeneratorTemplate } from '@a2a-console/contract';

export const PROJECT_GENERATOR_TEMPLATES: ProjectGeneratorTemplate[] = [
  {
    id: 'business-dashboard',
    name: '经营看板',
    description: '适合展示销售、订单、客户、库存、财务等关键指标。',
    examples: ['销售日报', '门店经营看板', '客户增长分析'],
    recommended_strategy: 'quality',
  },
  {
    id: 'admin-system',
    name: '管理后台',
    description: '适合需要列表、筛选、详情、编辑、权限说明的内部系统。',
    examples: ['订单管理', '客户资料库', '审批工作台'],
    recommended_strategy: 'strict',
  },
  {
    id: 'marketing-site',
    name: '宣传官网',
    description: '适合介绍产品、服务、案例、价格和联系方式。',
    examples: ['公司官网', '新品活动页', '服务介绍页'],
    recommended_strategy: 'quality',
  },
  {
    id: 'mobile-h5',
    name: '手机页面',
    description: '适合手机优先的报名、查询、展示或轻量业务流程。',
    examples: ['报名表单', '活动邀请', '移动端查询页'],
    recommended_strategy: 'quick',
  },
  {
    id: 'data-report',
    name: '数据报告',
    description: '适合把多组数据做成可阅读、可比较、可导出的页面。',
    examples: ['月度运营报告', '项目复盘', '数据洞察页'],
    recommended_strategy: 'quality',
  },
  {
    id: 'custom',
    name: '其他类型',
    description: '适合暂时说不清类别，但已经有明确业务说明的页面。',
    examples: ['自定义工具', '混合型页面', '内部演示'],
    recommended_strategy: 'strict',
  },
];
