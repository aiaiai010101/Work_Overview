#!/usr/bin/env python3
"""
Work_Overview v0.1 — 骨架
目标：跑通界面框架，熟悉 NiceGUI 基本组件

运行方式：python app.py
然后浏览器打开 http://127.0.0.1:5000
"""

from nicegui import ui

DEBUG = True

if DEBUG:
    import inspect
    for name in ['label', 'button', 'card', 'column', 'row',
                 'input', 'header', 'tree', 'select', 'icon',
                 'separator', 'space']:
        orig = getattr(ui, name)
        def make_wrapper(fn):
            def wrapper(*a, **kw):
                el = fn(*a, **kw)
                el.props(f'data-src="L{inspect.stack()[1].lineno}"')
                return el
            return wrapper
        setattr(ui, name, make_wrapper(orig))

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 一、假数据
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# 后面会换成数据库，现在先用一个写死的列表来演示树形结构。
# 每个节点需要三个字段：
#   - id       : 唯一标识（给程序用的）
#   - label    : 显示文字（给用户看的）
#   - children : 子节点列表（可以为空列表，也可以没有这个字段）
#
# 注意：这就是 NiceGUI 的 ui.tree 所要求的数据格式。

FAKE_TREE = [
    {
        'id': 1,
        'label': '📁 日常工作',
        'children': [
            {'id': 4, 'label': '📄 文件审批 🔴'},
            {'id': 5, 'label': '📄 月度报表 🔴'},
        ],
    },
    {
        'id': 2,
        'label': '📁 专项任务',
        'children': [
            {
                'id': 6,
                'label': '📁 信息化建设',
                'children': [
                    {'id': 7, 'label': '📄 需求调研 🟡'},
                ],
            },
        ],
    },
    {
        'id': 3,
        'label': '📁 会议纪要',
        'children': [
            {'id': 8, 'label': '📄 2024年第一次处务会 🟢'},
        ],
    },
]

# 模拟一个简单的数据字典，后面会换成数据库查询
FAKE_ITEMS = {
    1: {'name': '日常工作',          'type': 'folder',   'status': ''},
    2: {'name': '专项任务',          'type': 'folder',   'status': ''},
    3: {'name': '会议纪要',          'type': 'folder',   'status': ''},
    4: {'name': '文件审批',          'type': 'document', 'status': '待办'},
    5: {'name': '月度报表',          'type': 'document', 'status': '待办'},
    6: {'name': '信息化建设',        'type': 'folder',   'status': ''},
    7: {'name': '需求调研',          'type': 'document', 'status': '在办'},
    8: {'name': '2024年第一次处务会', 'type': 'document', 'status': '已办'},
}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 二、页面构建
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# @ui.page('/') 是一个装饰器，表示当用户访问根路径时，执行这个函数。
# 每个用户（每个浏览器标签页）访问时，都会独立执行一次，
# 所以里面的变量是每个用户各自独立的，互不影响。
#
# 你可以把这个函数理解为：
# "有人打开了浏览器，我现在要给他画一个界面"

@ui.page('/')
def index():

    # ── 2.1 用一个字典来存放需要跨函数访问的 UI 组件 ──
    #
    # 为什么需要这个？因为 Python 闭包的特性：
    # 内层函数可以"读"外层变量，但不能直接"改"它。
    # 把组件存到字典里，就可以在任何内层函数中通过 ref['xxx'] 来访问。
    # 这是 NiceGUI 开发中非常常用的模式。

    ref = {}

    # ── 2.2 定义"展示详情"的函数 ──
    #
    # 当用户在左侧树上点击某个节点时，我们要：
    #   1. 清空右侧面板
    #   2. 根据点击的节点 ID，查出数据
    #   3. 在右侧面板中填入内容
    #
    # 这里用 panel.clear() 清空，然后用 with panel: 往里面添加新内容。
    # 这个"清空再填充"的模式，是 NiceGUI 动态更新界面的核心手法。

    def show_detail(item_id):
        """在右侧面板中展示某个事项的详情"""

        # 从假数据中查找
        item = FAKE_ITEMS.get(item_id)
        if not item:
            return

        # 拿到右侧面板的引用
        panel = ref['detail_panel']

        # 清空面板里的所有旧内容
        panel.clear()

        # with panel: 表示"接下来创建的组件，都放进 panel 里"
        with panel:
            # 事项名称，用大号加粗文字
            ui.label(item['name']).classes('text-2xl font-bold')

            # 类型和状态，用小号灰色文字
            type_text = '文件夹' if item['type'] == 'folder' else '文档'
            status_text = item['status'] or '无'
            ui.label(f'类型: {type_text}　|　状态: {status_text}').classes(
                'text-sm text-gray-500'
            )

            # 分隔线
            ui.separator()

            # 占位提示（后续会替换成富文本编辑器）
            ui.label('📝 正文内容区域（下一步实现）').classes(
                'text-gray-400 mt-4'
            )

            # 占位提示（后续会替换成附件管理）
            ui.label('📎 附件管理区域（下一步实现）').classes(
                'text-gray-400 mt-2'
            )

    def show_welcome():
        """右侧面板的初始欢迎状态"""
        panel = ref['detail_panel']
        panel.clear()
        with panel:
            # 用一个纵向居中的容器来放欢迎信息
            # classes() 里写的是 Tailwind CSS 的工具类：
            #   w-full     = 宽度撑满
            #   items-center = 子元素水平居中
            #   py-24      = 上下留大片空白
            with ui.column().classes('w-full items-center py-24'):
                ui.icon('assignment', size='5rem').classes('text-gray-300')
                ui.label('选择左侧事项查看详情').classes(
                    'text-gray-400 text-lg mt-4'
                )

    # ── 2.3 树节点选中事件的回调函数 ──
    #
    # 当用户点击树上的某个节点时，NiceGUI 会调用这个函数，
    # 并传入一个事件对象 e，其中 e.value 就是被选中节点的 id。
    # 如果用户取消选中（再点一下同一个节点），e.value 会是 None。

    def on_tree_select(e):
        if e.value is None:
            # 取消选中了，回到欢迎页
            show_welcome()
            return
        # e.value 就是我们在 FAKE_TREE 中定义的那个 id
        show_detail(e.value)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 三、开始画界面
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #
    # NiceGUI 的界面是自上而下"声明式"构建的。
    # 你写 ui.xxx()，浏览器里就立刻出现对应的元素。
    # 用 with 语句可以表示"嵌套关系"——
    #   with A:
    #       B
    # 表示 B 是 A 的子元素。

    # ── 3.1 顶部工具栏 ──
    #
    # ui.header() 会创建一个固定在顶部的横条。
    # .classes() 用来添加 Tailwind CSS 样式类：
    #   items-center = 垂直居中对齐
    #   gap-2        = 子元素之间留间距
    #   px-4 py-2    = 内边距
    #   bg-blue-700  = 深蓝背景

    with ui.header().classes('items-center gap-2 px-4 py-2 bg-blue-700'):


        # 图标 + 标题
        ui.icon('work', size='sm').classes('text-white')
        ui.label('Work_Overview').classes('text-white text-lg font-bold')

        # ui.space() 是一个弹性空白，会把左右两边的元素"撑开"
        # 类似于 CSS 的 flex-grow，让后面的按钮靠右排列
        ui.space()


        # 工具栏按钮（目前只是摆在这里，点击功能后续实现）
        # .props() 用来设置底层 Quasar 组件的属性：
        #   flat        = 扁平样式，没有背景色和阴影
        #   dense       = 紧凑，减少内边距
        #   text-color  = 文字颜色
        ui.button(
            '📁 新建文件夹',
            on_click=lambda: ui.notify('功能待实现', type='info'),
        ).props('flat dense text-color=white')

        ui.button(
            '📄 新建文档',
            on_click=lambda: ui.notify('功能待实现', type='info'),
        ).props('flat dense text-color=white')

        # 竖线分隔符，视觉上把不同功能组隔开
        ui.separator().props('vertical dark inset').classes('mx-1')

        ui.button(
            '✏️ 重命名',
            on_click=lambda: ui.notify('功能待实现', type='info'),
        ).props('flat dense text-color=white')

        ui.button(
            '🗑️ 删除',
            on_click=lambda: ui.notify('功能待实现', type='info'),
        ).props('flat dense text-color=red-3')

    # ── 3.2 主体区域：左右分栏 ──
    #
    # ui.splitter 会创建一个可拖拽的分栏容器。
    #   value=25 表示左侧默认占 25% 宽度
    #
    # splitter.before = 左侧区域
    # splitter.after  = 右侧区域
    #
    # .style() 用来写内联 CSS（当 Tailwind 的预设类不够用时）
    # 这里用 calc(100vh - 52px) 让主体区域填满整个屏幕高度减去顶栏高度。

    with ui.splitter(value=25).classes('w-full').style(
        'height: calc(100vh - 52px);'
    ) as splitter:

        # ── 左侧面板 ──
        with splitter.before:
            with ui.column().classes('w-full h-full p-2 gap-2'):

                # 搜索框（目前仅占位，搜索功能后续实现）
                # props 说明：
                #   dense     = 紧凑高度
                #   clearable = 右侧显示清除按钮
                #   outlined  = 带边框样式
                ui.input(placeholder='🔍 搜索事项...').classes('w-full').props(
                    'dense clearable outlined'
                )

                # 状态筛选下拉框（目前仅占位）
                ui.select(
                    options=['全部', '待办', '在办', '已办'],
                    value='全部',
                ).classes('w-full').props('dense outlined label="状态筛选"')

                # ── 树形控件 ──
                #
                # 这是左侧最核心的组件。参数说明：
                #   第1个参数  = 树的数据（嵌套字典列表）
                #   label_key  = 字典中哪个字段作为显示文字
                #   children_key = 字典中哪个字段作为子节点列表
                #   node_key   = 字典中哪个字段作为唯一标识
                #   on_select  = 用户选中节点时的回调函数
                #
                # .classes() 说明：
                #   flex-grow = 占满剩余纵向空间
                #   overflow-auto = 内容过多时出现滚动条
                #
                # .props('dense') = 紧凑模式，行高更小

                ref['tree'] = ui.tree(
                    FAKE_TREE,
                    label_key='label',
                    children_key='children',
                    node_key='id',
                    on_select=on_tree_select,
                ).classes('w-full flex-grow overflow-auto').props('dense')

        # ── 右侧面板 ──
        with splitter.after:
            # ui.scroll_area 提供一个可滚动的区域
            # 当内容（正文+附件）很长时，右侧会独立滚动，不影响左侧
            with ui.scroll_area().classes('w-full h-full'):
                # 这个 column 就是我们后续动态填充内容的容器
                # 在 show_detail() 中通过 ref['detail_panel'] 来访问它
                ref['detail_panel'] = ui.column().classes('w-full p-4')

                # 初始显示欢迎信息
                show_welcome()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 四、启动应用
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# ui.run() 会启动一个内置的 Web 服务器。参数说明：
#   host='0.0.0.0'  = 监听所有网卡，局域网内其他电脑也能访问
#   port=5000       = 端口号，访问地址就是 http://xxx:5000
#   title=...       = 浏览器标签页的标题
#   reload=False    = 关闭热重载（正式使用时关闭，开发时可设为 True）
#   show=False      = 不自动打开浏览器（服务器可能没有桌面环境）
#
# __mp_main__ 的判断是 NiceGUI 多进程模式需要的，加上即可。

if __name__ in {'__main__', '__mp_main__'}:
    print()
    print('=' * 50)
    print('    Work_Overview v0.1 — 骨架')
    print('=' * 50)
    print('  访问地址: http://127.0.0.1:5000')
    print('  按 Ctrl+C 停止')
    print('=' * 50)
    print()

    ui.run(
        host='0.0.0.0',
        port=5000,
        title='Work_Overview',
        reload=False,
        show=True,
    )