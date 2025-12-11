import flet as ft
from openai import AsyncOpenAI # 使用异步客户端
import os
import asyncio

# 将主函数改为 async 模式
async def main(page: ft.Page):
    # --- 1. 全局页面配置 ---
    page.title = "Grok"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#000000"
    page.padding = 0
    page.adaptive = True

    # 获取 Key
    api_key = os.environ.get("XAI_API_KEY")

    # --- 2. 定义组件 ---
    
    # 欢迎语
    welcome_text = ft.Column(
        [
            ft.Text("Grok", size=40, weight="bold", color="white", opacity=0.8),
            ft.Text("annex to your brain", size=14, color="grey", italic=True),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )

    chat_list = ft.ListView(
        expand=True,
        spacing=20,
        padding=20,
        auto_scroll=True,
    )
    
    center_container = ft.Container(
        content=welcome_text,
        alignment=ft.alignment.center,
        expand=True
    )

    txt_input = ft.TextField(
        hint_text="Ask anything...",
        hint_style=ft.TextStyle(color="#666666"),
        text_style=ft.TextStyle(color="white", size=16),
        bgcolor="transparent",
        border=ft.InputBorder.NONE,
        multiline=True,
        min_lines=1,
        max_lines=5,
        expand=True,
        shift_enter=True,
    )

    send_btn = ft.IconButton(
        icon="arrow_upward",
        icon_color="black",
        bgcolor="white",
        width=35,
        height=35,
        style=ft.ButtonStyle(shape=ft.CircleBorder()),
        tooltip="Send",
    )

    # --- 3. 核心逻辑 (Async 异步版) ---
    async def send_message(e):
        user_text = txt_input.value
        if not user_text: return
        if not user_text.strip(): return

        print(f"User sent: {user_text}") # 打印日志，方便在后台看

        # 1. 界面立刻响应！
        center_container.visible = False
        txt_input.value = ""
        txt_input.disabled = True
        
        # 显示用户消息
        chat_list.controls.append(
            ft.Row([
                ft.Container(
                    content=ft.Text(user_text, color="white", size=16),
                    bgcolor="#1A1A1A",
                    padding=ft.padding.symmetric(horizontal=20, vertical=12),
                    border_radius=20,
                    maw=320,
                )
            ], alignment=ft.MainAxisAlignment.END)
        )
        
        # 显示思考中占位符
        loading_text = "Grok is thinking..."
        ai_response_text = ft.Text(loading_text, color="yellow", size=16, font_family="monospace")
        chat_list.controls.append(
            ft.Row([
                ft.Container(content=ai_response_text, padding=ft.padding.only(left=10), maw=350)
            ], alignment=ft.MainAxisAlignment.START)
        )
        
        # ⚡️ 关键：异步刷新界面 (让上面的改动立刻生效，不再卡死)
        await page.update_async()

        try:
            if not api_key:
                raise Exception("API Key 未配置")

            # 初始化异步客户端
            client = AsyncOpenAI(api_key=api_key, base_url="https://api.x.ai/v1")
            
            # 发起异步请求
            stream = await client.chat.completions.create(
                model="grok-3",
                messages=[
                    {"role": "system", "content": "You are Grok."},
                    {"role": "user", "content": user_text}
                ],
                stream=True,
            )

            full_res = ""
            ai_response_text.color = "white" # 开始生成时变白
            
            # 异步读取流
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_res += content
                    ai_response_text.value = full_res + "▌"
                    # 每收到一个字就刷新一次界面
                    await page.update_async()
            
            ai_response_text.value = full_res

        except Exception as err:
            print(f"Error: {err}")
            ai_response_text.value = f"⚠️ Error: {str(err)}"
            ai_response_text.color = "red"

        # 恢复输入框
        txt_input.disabled = False
        txt_input.focus()
        await page.update_async()

    # 绑定事件
    send_btn.on_click = send_message
    txt_input.on_submit = send_message

    # --- 4. 布局 ---
    input_bar = ft.Container(
        content=ft.Row(
            [txt_input, send_btn],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.END,
        ),
        bgcolor="#111111",
        border_radius=25,
        padding=ft.padding.symmetric(horizontal=15, vertical=5),
        margin=ft.margin.symmetric(horizontal=15, vertical=10),
        border=ft.border.all(1, "#333333"),
    )

    await page.add_async(
        ft.Column(
            [
                ft.Stack([center_container, chat_list], expand=True),
                input_bar,
            ],
            expand=True,
            spacing=0,
        )
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    # 注意：这里要用 ft.app_async
    ft.app(target=main, view=ft.WEB_BROWSER, port=port, host="0.0.0.0")
