"""
单容器方案做连续文档

========================================
一、整体架构
========================================

    顶栏
    └── splitter（左右分栏）
        ├── 左侧：目录树 + 搜索 + 状态筛选
        └── 右侧：scroll_area（连续文档）

========================================
二、右侧单容器方案
========================================

    scroll_area
    └── detail_panel（column，一个容器装全部内容）
          ├── card_1
          ├── card_2
          ├── ...
          └── card_8

    8 个卡片一次性全部渲染，用户自由滚动浏览。
    点击左侧节点时，不做清空/重建，直接滚动到对应位置。

    滚动方式：
    ├── 点击文档节点   → scroll_to(card) 滚动到该卡片
    ├── 点击文件夹节点 → scroll_to(第一个子项的卡片)
    ├── 搜索框输入     → set_visibility(True/False) 控制显隐
    └── 状态筛选下拉   → set_visibility(True/False) 控制显隐

    关键：组件只创建一次，后续只操作显隐和滚动，不销毁重建

========================================
三、数据流
========================================

    ITEMS_DATA（列表）
        ↓ build_items_dict()
    items_dict（{id: item} 字典，方便按 id 查找）

    FAKE_TREE（树形结构）→ 渲染到左侧 ui.tree
    ITEMS_DATA             → 渲染到右侧卡片

    sections（{id: card} 字典）
        作用：左侧节点 id → 右侧卡片组件 的映射
        用途：点击左侧时，通过 id 找到 card，然后滚动/显隐

========================================
四、组件关系
========================================

    body（overflow: hidden，禁止整页滚动）
    └── header（固定顶栏）
    └── splitter（左右分栏，高度 = 100vh - 52px）
        ├── before（左侧，overflow: hidden）
        │     ├── input（搜索框）
        │     ├── select（状态下拉）
        │     └── tree（目录树，overflow-auto 自己滚动）
        └── after（右侧）
              └── scroll_area（高度固定，自己滚动）
                    └── detail_panel（column，撑开内容高度）
                          └── card × 8

========================================
五、文件结构（后续拆分）
========================================

    app.py          → 页面构建 + 启动
    data.py         → 假数据（后续换成数据库）
    helpers.py      → 辅助函数（render, show_detail, on_tree_select）
"""


from nicegui import ui

# ==================== 假数据 ====================

FAKE_TREE = [
    {
        'id': 'category-1',
        'label': '📂 合同审批',
        'children': [
            {'id': 'item-1', 'label': '购销合同-华为技术有限公司'},
            {'id': 'item-2', 'label': '服务合同-阿里云计算有限公司'},
            {'id': 'item-3', 'label': '租赁合同-万科物业管理'},
        ],
    },
    {
        'id': 'category-2',
        'label': '📂 费用报销',
        'children': [
            {'id': 'item-4', 'label': '差旅费报销-张三'},
            {'id': 'item-5', 'label': '办公用品采购-李四'},
        ],
    },
    {
        'id': 'category-3',
        'label': '📂 人事审批',
        'children': [
            {'id': 'item-6', 'label': '入职申请-王五'},
            {'id': 'item-7', 'label': '请假申请-赵六'},
            {'id': 'item-8', 'label': '转正申请-孙七'},
        ],
    },
]

ITEMS_DATA = [
    {
        'id': 'item-1',
        'title': '购销合同-华为技术有限公司',
        'status': '在办',
        'applicant': '张经理',
        'date': '2025-03-15',
        'content': (
            '合同编号：HW-2025-001\n'
            '合同金额：500万元\n'
            '签订日期：2025年3月15日\n\n'
            '本合同由甲方与华为技术有限公司就服务器设备采购事宜签订。'
            '合同有效期为2025年3月15日至2026年3月14日。\n\n'
            '第一条 合同标的\n'
            '甲方向乙方采购华为FusionServer系列服务器共计50台，'
            '具体型号及配置详见附件一《设备清单》。\n\n'
            '第二条 价款及支付\n'
            '合同总价款为人民币伍佰万元整（¥5,000,000.00），'
            '甲方应在合同签订后30日内支付30%预付款，'
            '设备验收合格后15日内支付剩余70%尾款。\n\n'
            '第三条 交货与验收\n'
            '乙方应在合同签订后60日内完成全部设备的交付及安装调试。'
            '甲方应在设备交付后10个工作日内组织验收。'
        ),
    },
    {
        'id': 'item-2',
        'title': '服务合同-阿里云计算有限公司',
        'status': '待办',
        'applicant': '李主管',
        'date': '2025-04-01',
        'content': (
            '合同编号：ALI-2025-002\n'
            '合同金额：200万元\n'
            '签订日期：2025年4月1日\n\n'
            '本合同由甲方与阿里云计算有限公司就云计算服务租赁事宜签订。\n\n'
            '服务内容包括：\n'
            '1. ECS云服务器 × 20台（8核32G配置）\n'
            '2. OSS对象存储 10TB\n'
            '3. CDN全球加速服务\n'
            '4. 负载均衡SLB服务\n\n'
            '服务期限为2025年4月1日至2026年3月31日，'
            '乙方应保证服务可用性不低于99.95%。\n\n'
            '如因乙方原因导致服务中断，'
            '乙方应按照中断时长的10倍给予服务时长补偿。'
        ),
    },
    {
        'id': 'item-3',
        'title': '租赁合同-万科物业管理',
        'status': '已办',
        'applicant': '王总监',
        'date': '2025-02-20',
        'content': (
            '合同编号：WK-2025-003\n'
            '合同金额：180万元/年\n'
            '签订日期：2025年2月20日\n\n'
            '本合同由甲方与万科物业管理有限公司就办公场地租赁事宜签订。\n\n'
            '租赁标的：XX市XX区XX路XX号XX大厦15层整层\n'
            '建筑面积：2000平方米\n'
            '租赁期限：2025年3月1日至2028年2月28日\n\n'
            '月租金为人民币壹拾伍万元整，甲方应于每月5日前支付当月租金。'
            '租赁期间，乙方负责物业管理及公共设施维护。'
        ),
    },
    {
        'id': 'item-4',
        'title': '差旅费报销-张三',
        'status': '待办',
        'applicant': '张三',
        'date': '2025-04-10',
        'content': (
            '报销编号：BX-2025-0041\n'
            '报销金额：8,650元\n'
            '出差日期：2025年4月5日 - 4月8日\n\n'
            '出差事由：赴上海参加2025年度供应商大会\n\n'
            '费用明细：\n'
            '1. 往返机票：3,200元（经济舱）\n'
            '2. 酒店住宿：2,400元（3晚 × 800元/晚）\n'
            '3. 市内交通：450元\n'
            '4. 餐饮补贴：600元（4天 × 150元/天）\n'
            '5. 会议注册费：2,000元\n\n'
            '所有发票及行程单已附后，请审批。'
        ),
    },
    {
        'id': 'item-5',
        'title': '办公用品采购-李四',
        'status': '在办',
        'applicant': '李四',
        'date': '2025-04-12',
        'content': (
            '采购编号：CG-2025-0051\n'
            '采购金额：12,360元\n'
            '申请日期：2025年4月12日\n\n'
            '因部门扩编，现需采购以下办公用品：\n\n'
            '1. 办公桌椅套装 × 5套，单价1,500元\n'
            '2. 显示器支架 × 5个，单价280元\n'
            '3. 文件柜 × 3个，单价620元\n'
            '4. 碎纸机 × 1台，单价500元\n\n'
            '以上物品拟从京东企业采购平台下单，预计3-5个工作日到货。'
        ),
    },
    {
        'id': 'item-6',
        'title': '入职申请-王五',
        'status': '已办',
        'applicant': '王五',
        'date': '2025-03-25',
        'content': (
            '申请编号：RS-2025-0061\n'
            '申请人：王五\n'
            '拟入职日期：2025年4月15日\n\n'
            '拟聘岗位：高级Java开发工程师\n'
            '所属部门：技术研发部\n'
            '汇报对象：赵总监\n\n'
            '薪资待遇：月薪35,000元，年终奖2个月\n'
            '试用期：3个月（薪资80%）\n\n'
            '候选人背景：\n'
            '学历：硕士（XX大学计算机科学专业）\n'
            '工作年限：6年\n'
            '上家公司：XX科技有限公司\n\n'
            '已通过三轮技术面试及HR面试，综合评价优秀。'
        ),
    },
    {
        'id': 'item-7',
        'title': '请假申请-赵六',
        'status': '待办',
        'applicant': '赵六',
        'date': '2025-04-14',
        'content': (
            '申请编号：RS-2025-0071\n'
            '申请人：赵六\n'
            '所属部门：市场营销部\n\n'
            '请假类型：年假\n'
            '请假日期：2025年4月21日 - 4月25日（共5天）\n\n'
            '请假事由：家中有事需回老家处理，已与同事做好工作交接。\n\n'
            '工作交接安排：\n'
            '1. 日常客户对接由钱七同事代为处理\n'
            '2. 本周五前完成月度营销报告\n'
            '3. 紧急事务可通过手机联系\n\n'
            '剩余年假天数：8天\n'
            '本次使用：5天\n'
            '使用后剩余：3天'
        ),
    },
    {
        'id': 'item-8',
        'title': '转正申请-孙七',
        'status': '在办',
        'applicant': '孙七',
        'date': '2025-04-08',
        'content': (
            '申请编号：RS-2025-0081\n'
            '申请人：孙七\n'
            '所属部门：产品设计部\n'
            '入职日期：2025年1月8日\n'
            '试用期满日期：2025年4月7日\n\n'
            '试用期工作总结：\n\n'
            '1. 独立完成公文管理系统V2.0的UI设计，获得客户好评\n'
            '2. 参与移动端App改版项目，负责交互设计\n'
            '3. 建立了部门设计规范文档，提升团队协作效率\n'
            '4. 组织2次设计评审会，推动设计质量提升\n\n'
            '直属上级评价：孙七同学试用期间表现优秀，'
            '专业能力强，沟通协作好，建议按时转正。\n\n'
            '转正后薪资：维持原定薪资标准不变。'
        ),
    },
]

STATUS_COLORS = {
    '待办': 'orange',
    '在办': 'blue',
    '已办': 'green',
}


# ==================== 辅助函数 ====================

def build_items_dict(items_list):
    """把列表转成 {id: item} 的字典，方便按 id 查找"""
    return {item['id']: item for item in items_list}


def on_tree_select(ref, e):
    """树节点选中回调"""
    if not e.value:
        return

    target_id = None


    # 文件夹节点：找第一个子项
    if e.value.startswith('category'):
        for node in FAKE_TREE:
            if node['id'] == e.value and node.get('children'):
                target_id = node['children'][0]['id']
                break
    else:
        # 文档节点
        target_id = e.value

    # 用 JS 原生 scrollIntoView 滚动到目标卡片
    if target_id and target_id in ref['sections']:
        card = ref['sections'][target_id]
        ui.run_javascript(
            f'document.getElementById("c{card.id}")'
            f'.scrollIntoView({{behavior: "smooth", block: "start"}})'
        )


def on_search(ref, e):
    """搜索框输入回调：过滤左侧树 + 右侧内容块"""
    keyword = e.value.strip().lower() if e.value else ''

    for item_id, card in ref['sections'].items():
        item = ref['items_dict'].get(item_id)
        if not item:
            continue
        if keyword == '' or keyword in item['title'].lower():
            card.set_visibility(True)
        else:
            card.set_visibility(False)


def on_filter(ref, e):
    """状态下拉框回调：按状态过滤"""
    status = e.value

    for item_id, card in ref['sections'].items():
        item = ref['items_dict'].get(item_id)
        if not item:
            continue
        if status == '全部' or item['status'] == status:
            card.set_visibility(True)
        else:
            card.set_visibility(False)


def render_right_content(ref, items_list):
    """渲染右侧连续文档，返回 {item_id: card引用} 的字典"""
    sections = {}

    for item in items_list:
        with  ui.card().classes('w-full') as card:
            # 标题行：标题 + 状态徽章
            with ui.row().classes('w-full items-center gap-3'):
                ui.label(item['title']).classes('text-xl font-bold')
                ui.badge(
                    item['status'],
                    color=STATUS_COLORS.get(item['status'], 'grey'),
                )

            # 元信息行：日期 + 申请人
            with ui.row().classes('gap-4 text-sm text-gray-500'):
                ui.label(f"📅 {item['date']}")
                ui.label(f"👤 {item['applicant']}")

            ui.separator()

            # 正文内容
            ui.label(item['content']).style(
                'white-space: pre-wrap; line-height: 1.8;'
            )

        sections[item['id']] = card

    return sections


# ==================== 页面 ====================

@ui.page('/')
def index():
    ui.query('body').style('overflow: hidden')

    # ref 存放所有跨函数共享的引用
    ref = {}
    ref['items_dict'] = build_items_dict(ITEMS_DATA)

    # ---------- 顶栏 ----------
    with ui.header().classes('bg-blue-800 text-white items-center gap-2 px-4 py-2'):
        ui.icon('description').classes('text-2xl')
        ui.label('公文管理系统').classes('text-xl font-bold')
        ui.space()
        ui.button('新建文档', on_click=lambda: ui.notify('功能待实现')).props(
            'flat dense text-color=white'
        )

    # ---------- 主体 ----------
    with ui.splitter(value=25).classes('w-full').style(
        'height: calc(100vh - 52px)'
    ) as splitter:

        # ---- 左侧目录 ----
        with splitter.before:
            with ui.column().classes('w-full h-full p-2 gap-2').style(
                'overflow: hidden'
            ):
                search_input = ui.input(
                    placeholder='🔍 搜索事项...'
                ).classes('w-full').props('dense clearable outlined')
                search_input.on('update:model-value', lambda e: on_search(ref, e))

                status_filter = ui.select(
                    options=['全部', '待办', '在办', '已办'],
                    value='全部',
                ).classes('w-full').props('dense outlined label="状态筛选"')
                status_filter.on('update:model-value', lambda e: on_filter(ref, e))

                ref['tree'] = ui.tree(
                    FAKE_TREE,
                    label_key='label',
                    children_key='children',
                    node_key='id',
                    on_select=lambda e: on_tree_select(ref, e),
                ).classes('w-full flex-grow overflow-auto').props('dense')

        # ---- 右侧连续文档 ----
        with splitter.after:
            ref['scroll_area'] = ui.scroll_area().classes('w-full').style(
                'height: calc(100vh - 52px);'
            )
            with ref['scroll_area']:
                with ui.column().classes('w-full gap-6 p-6'):
                    ref['sections'] = render_right_content(ref, ITEMS_DATA)


# ==================== 启动 ====================

if __name__ in {'__main__', '__mp_main__'}:
    print()
    print('=' * 50)
    print('    公文管理系统')
    print('=' * 50)
    print('  访问地址: http://127.0.0.1:5000')
    print('  按 Ctrl+C 停止')
    print('=' * 50)
    print()

    ui.run(
        host='0.0.0.0',
        port=5000,
        title='公文管理系统',
        reload=False,
        show=True,
    )

