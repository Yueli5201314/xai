import flet as ft
from openai import OpenAI
import os

def main(page: ft.Page):
    # --- 1. 全局页面配置 ---
    page.title = "Grok"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#000000" # 纯黑背景
    page.padding = 0         # 移除默认边距，实现全屏
    page.adaptive = True     # 适配移动端

    # 获取 Key
    api_key = os.environ.get("XAI_API_KEY")

    # --- 2. 定义组件 ---

    # 2.1 聊天列表区域
    # 初始状态显示一个大的 Grok Logo
    welcome_text = ft.Column(
        [
            ft.Text("Grok", size=40, weight="bold", color="white", opacity=0.8),
            ft.Text("annex to your brain", size=14, color="grey", italic=True),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )

    # 聊天记录容器
    chat_list = ft.ListView(
        expand=True,
        spacing=20,
        padding=20,
        auto_scroll=True,
    )
    
    # 将欢迎语放在中间容器里
    center_container = ft.Container(
        content=welcome_text,
        alignment=ft.alignment.center,
        expand=True
    )

    # 2.2 输入框区域 (仿官方悬浮样式)
    txt_input = ft.TextField(
        hint_text="Ask anything...",
        hint_style=ft.TextStyle(color="#666666"),
        text_style=ft.TextStyle(color="white", size=16),
        bgcolor="transparent",
        border=ft.InputBorder.NONE, # 无边框，靠容器画边框
        multiline=True,
        min_lines=1,
        max_lines=5,
        expand=True,
        shift_enter=True, # Shift+Enter换行，Enter提交
    )

    # 发送按钮
    send_btn = ft.IconButton(
        icon="arrow_upward", # 修复了之前的图标报错
        icon_color="black",
        bgcolor="white",     # 白色圆底黑箭头
        width=35,
        height=35,
        style=ft.ButtonStyle(shape=ft.CircleBorder()),
        tooltip="Send",
    )

    # --- 3. 核心逻辑 ---
    def send_message(e):
        user_text = txt_input.value
        if not user_text.strip(): return

        # 1. 隐藏欢迎语
        center_container.visible = False
        
        # 2. 立即清空输入框 (让用户感觉响应很快)
        current_text = user_text # 暂存
        txt_input.value = ""
        txt_input.disabled = True # 暂时禁用防止重复提交
        page.update()

        # 3. 添加用户气泡 (靠右)
        chat_list.controls.append(
            ft.Row([
                ft.Container(
                    content=ft.Text(current_text, color="white", size=16),
                    bgcolor="#1A1A1A", # 深灰背景
                    padding=ft.padding.symmetric(horizontal=20, vertical=12),
                    border_radius=20,
                    maw=320, # 最大宽度
                )
            ], alignment=ft.MainAxisAlignment.END)
        )
        page.update()

        # 4. 添加 AI 思考占位符 (靠左)
        ai_response_text = ft.Text("▌", color="white", size=16, font_family="monospace")
        chat_list.controls.append(
            ft.Row([
                ft.Container(
                    content=ai_response_text,
                    padding=ft.padding.only(left=10),
                    maw=350,
                )
            ], alignment=ft.MainAxisAlignment.START)
        )
        page.update()

        # 5. 发送请求
        try:
            if not api_key:
                raise Exception("API Key Missing")

            client = OpenAI(api_key=api_key, base_url="https://api.x.ai/v1")
            
            stream = client.chat.completions.create(
                model="grok-3",
                messages=[
                    {"role": "system", "content": "You are Grok, a rebellious AI."},
                    {"role": "user", "content": current_text}
                ],
                stream=True,
            )

            full_res = ""
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_res += content
                    ai_response_text.value = full_res + "▌"
                    page.update()
            
            # 完成
            ai_response_text.value = full_res

        except Exception as err:
            ai_response_text.value = f"⚠️ Error: {str(err)}"
            ai_response_text.color = "red"

        # 6. 恢复输入框
        txt_input.disabled = False
        txt_input.focus()
        page.update()

    # 绑定事件
    send_btn.on_click = send_message
    txt_input.on_submit = send_message # 绑定回车键

    # --- 4. 组装布局 (层叠式布局) ---
    
    # 底部输入栏容器
    input_bar = ft.Container(
        content=ft.Row(
            [txt_input, send_btn],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.END,
        ),
        bgcolor="#111111", # 底部栏背景色
        border_radius=25,
        padding=ft.padding.symmetric(horizontal=15, vertical=5),
        margin=ft.margin.symmetric(horizontal=15, vertical=10),
        border=ft.border.all(1, "#333333"), # 细边框
    )

    # 主布局
    page.add(
        ft.Column(
            [
                # 上半部分：聊天记录 + 欢迎语
                ft.Stack(
                    [
                        center_container, # 底层：欢迎语
                        chat_list,        # 上层：聊天记录
                    ],
                    expand=True,
                ),
                # 底部：输入栏
                input_bar,
            ],
            expand=True,
            spacing=0,
        )
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    ft.app(target=main, view=ft.WEB_BROWSER, port=port, host="0.0.0.0")
